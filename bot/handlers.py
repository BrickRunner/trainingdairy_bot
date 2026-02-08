"""
Обработчики команд и сообщений бота
"""

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from datetime import datetime
from typing import Union
import re
import logging

from bot.fsm import AddTrainingStates, ExportPDFStates
from bot.keyboards import (
    get_main_menu_keyboard,
    get_training_types_keyboard,
    get_cancel_keyboard,
    get_skip_keyboard,
    get_fatigue_keyboard,
    get_period_keyboard,
    get_date_keyboard,
    get_trainings_list_keyboard,
    get_training_detail_keyboard,
    get_export_type_keyboard,
    get_export_period_keyboard
)
from bot.calendar_keyboard import CalendarKeyboard
from database.queries import (
    add_user, add_training, get_user,
    get_trainings_by_period, get_training_statistics, get_training_by_id,
    get_trainings_by_custom_period, get_statistics_by_custom_period,
    delete_training,  
    get_user_settings,  
    get_main_training_types,  
    get_pulse_zone_for_value  
)
from bot.graphs import generate_graphs
from bot.pdf_export import create_training_pdf
from utils.unit_converter import format_distance, format_pace, format_swimming_distance
from utils.date_formatter import DateFormatter, get_user_date_format
from utils.goals_checker import check_weekly_goals
from ratings.rating_updater import update_single_user_rating
from database.level_queries import calculate_and_update_user_level
from coach.coach_queries import is_user_coach
from ai.ai_analyzer import analyze_training_statistics, is_ai_available

router = Router()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    from coach.coach_queries import is_user_coach, find_coach_by_code, add_student_to_coach

    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    await add_user(user_id, username)

    args = message.text.split()
    if len(args) > 1 and args[1].startswith("coach_"):
        coach_code = args[1].replace("coach_", "").upper()

        coach_id = await find_coach_by_code(coach_code)

        if coach_id:
            if coach_id == user_id:
                await message.answer(
                    "❌ Вы не можете добавить себя в качестве своего ученика.",
                    parse_mode="HTML"
                )
                is_coach_status = await is_user_coach(user_id)
                settings = await get_user_settings(user_id)
                name = settings.get('name', username) if settings else username
                await message.answer(
                    f"👋 Привет, {name}!\n\nВыбери действие из меню ниже 👇",
                    reply_markup=get_main_menu_keyboard(is_coach_status),
                    parse_mode="HTML"
                )
                return

            settings = await get_user_settings(user_id)

            if not settings or not settings.get('name') or not settings.get('birth_date'):
                await state.update_data(pending_coach_code=coach_code)
                from registration.registration_handlers import start_registration
                await start_registration(message, state)
                return

            success = await add_student_to_coach(coach_id, user_id)

            if success:
                coach_user = await get_user(coach_id)
                coach_name = coach_user.get('username', 'Тренер') if coach_user else 'Тренер'

                await message.answer(
                    f"✅ <b>Вы успешно подключились к тренеру!</b>\n\n"
                    f"Ваш тренер: @{coach_name}\n\n"
                    f"Теперь тренер может просматривать ваши тренировки и статистику.",
                    reply_markup=ReplyKeyboardRemove(),
                    parse_mode="HTML"
                )

                try:
                    student_name = message.from_user.full_name
                    await message.bot.send_message(
                        coach_id,
                        f"🎉 <b>Новый ученик!</b>\n\n"
                        f"К вам подключился: {student_name}",
                        parse_mode="HTML"
                    )

                    coach_settings = await get_user_settings(coach_id)
                    coach_is_coach = await is_user_coach(coach_id)

                    await message.bot.send_message(
                        coach_id,
                        "Вы в главном меню",
                        reply_markup=get_main_menu_keyboard(coach_is_coach),
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify coach: {e}")

                settings = await get_user_settings(user_id)
                is_coach_status = await is_user_coach(user_id)

                await message.answer(
                    "Вы в главном меню",
                    reply_markup=get_main_menu_keyboard(is_coach_status),
                    parse_mode="HTML"
                )
                return
            else:
                await message.answer(
                    "⚠️ Вы уже подключены к этому тренеру.",
                    reply_markup=ReplyKeyboardRemove()
                )

                settings = await get_user_settings(user_id)
                is_coach_status = await is_user_coach(user_id)

                await message.answer(
                    "Вы в главном меню",
                    reply_markup=get_main_menu_keyboard(is_coach_status),
                    parse_mode="HTML"
                )
                return
        else:
            await message.answer(
                "❌ Код тренера не найден.\n\n"
                "Проверьте правильность ссылки и попробуйте снова."
            )

    settings = await get_user_settings(user_id)

    if not settings or not settings.get('name') or not settings.get('birth_date'):
        from registration.registration_handlers import start_registration
        await start_registration(message, state)
        return

    is_coach_status = await is_user_coach(user_id)

    name = settings.get('name', username)
    welcome_text = (
        f"👋 Привет, {name}!\n\n"
        "Добро пожаловать в <b>Trainingdiary_bot</b> — твой личный дневник тренировок! 🏃‍♂️\n\n"
        "Что я умею:\n"
        "➕ Добавлять тренировки\n"
        "📊 Показывать статистику\n"
        "📈 Строить графики прогресса\n"
        "🏆 Отслеживать достижения\n\n"
        "Выбери действие из меню ниже 👇"
    )

    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard(is_coach_status),
        parse_mode="HTML"
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = (
        "📖 **Справка по боту**\n\n"
        "**Команды:**\n"
        "/start - Начать работу с ботом\n"
        "/add_training - Добавить тренировку\n"
        "/stats - Посмотреть статистику\n"
        "/help - Показать эту справку\n\n"
        "**Кнопки меню:**\n"
        "➕ Добавить тренировку - Записать новую тренировку\n"
        "📊 Мои тренировки - Посмотреть список тренировок\n"
        "📈 Графики - Визуализация прогресса\n"
        "🏆 Достижения - Ваши достижения и награды\n"
        "📥 Экспорт в PDF - Сохранить тренировки в PDF\n\n"
        "Для добавления тренировки следуйте инструкциям бота. "
        "Для удаления тренировки откройте её детали в '📊 Мои тренировки' и нажмите '🗑 Удалить тренировку'.\n"
        "Вы всегда можете отменить действие, нажав кнопку ❌ Отменить"
    )
    
    await message.answer(help_text, parse_mode="Markdown")

@router.message(F.text == "➕ Добавить тренировку")
@router.message(Command("add_training"))
async def start_add_training(message: Message, state: FSMContext):
    """Начало процесса добавления тренировки"""
    user_id = message.from_user.id

    main_types = await get_main_training_types(user_id)

    if not main_types:
        await message.answer(
            "⚠️ **Настройка основных типов тренировок**\n\n"
            "Вы еще не выбрали основные типы тренировок.\n"
            "Пожалуйста, перейдите в меню ⚙️ Настройки → 👤 Профиль → "
            "Установить основные типы тренировок",
            parse_mode="Markdown"
        )
        return

    from datetime import datetime
    today = datetime.now().date().isoformat()

    import aiosqlite
    import os
    DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT id, type, date, distance, avg_pace, pace_unit, exercises, intervals, comment
            FROM trainings
            WHERE user_id = ? AND date <= ? AND is_planned = 1 AND duration IS NULL
            ORDER BY date ASC, id ASC
            """,
            (user_id, today)
        ) as cursor:
            planned_trainings = await cursor.fetchall()

    if planned_trainings:
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        from aiogram.types import InlineKeyboardButton
        from utils.date_formatter import get_user_date_format, DateFormatter

        user_date_format = await get_user_date_format(user_id)

        text = "📋 <b>Запланированные тренировки</b>\n\n"
        text += "Выберите тренировку для выполнения или добавьте новую:\n\n"

        builder = InlineKeyboardBuilder()

        for i, training in enumerate(planned_trainings, 1):
            training_dict = dict(training)

            training_date_str = DateFormatter.format_date(training_dict['date'], user_date_format)

            desc = f"📅 {training_date_str} • 📝 {training_dict['type'].capitalize()}"

            if training_dict.get('distance'):
                desc += f" • {training_dict['distance']} км"
            if training_dict.get('avg_pace'):
                desc += f" • темп {training_dict['avg_pace']}"
            if training_dict.get('exercises'):
                desc += f" • {training_dict['exercises'][:30]}..."
            if training_dict.get('intervals'):
                desc += f" • {training_dict['intervals'][:30]}..."

            text += f"{i}. {desc}\n"

            builder.row(
                InlineKeyboardButton(
                    text=f"✅ Выполнить: {training_dict['type'].capitalize()} ({training_date_str})",
                    callback_data=f"complete_planned:{training_dict['id']}"
                )
            )

        text += "\n💡 Или добавьте новую тренировку:"

        builder.row(
            InlineKeyboardButton(
                text="➕ Добавить новую тренировку",
                callback_data="add_new_training"
            )
        )

        await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
        return

    await message.answer(
        "🏋️ **Добавление тренировки**\n\n"
        "Выберите тип тренировки:",
        reply_markup=get_training_types_keyboard(main_types),
        parse_mode="Markdown"
    )
    await state.set_state(AddTrainingStates.waiting_for_type)


@router.callback_query(F.data == "add_new_training")
async def add_new_training_callback(callback: CallbackQuery, state: FSMContext):
    """Добавить новую тренировку (минуя запланированные)"""
    user_id = callback.from_user.id

    main_types = await get_main_training_types(user_id)

    await callback.message.edit_text(
        "🏋️ **Добавление тренировки**\n\n"
        "Выберите тип тренировки:",
        reply_markup=get_training_types_keyboard(main_types),
        parse_mode="Markdown"
    )
    await state.set_state(AddTrainingStates.waiting_for_type)
    await callback.answer()


@router.callback_query(F.data.startswith("complete_planned:"))
async def complete_planned_training(callback: CallbackQuery, state: FSMContext):
    """Начать выполнение запланированной тренировки"""
    training_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    import aiosqlite
    import os
    DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT * FROM trainings
            WHERE id = ? AND user_id = ? AND is_planned = 1 AND duration IS NULL
            """,
            (training_id, user_id)
        ) as cursor:
            planned = await cursor.fetchone()

    if not planned:
        await callback.answer("❌ Тренировка не найдена", show_alert=True)
        return

    planned_dict = dict(planned)

    user_settings = await get_user_settings(user_id)
    distance_unit = user_settings.get('distance_unit', 'км') if user_settings else 'км'
    user_date_format = await get_user_date_format(user_id)

    date_str = DateFormatter.format_date(planned_dict['date'], user_date_format)

    await state.update_data(
        planned_training_id=training_id,
        training_type=planned_dict['type'],  
        date=planned_dict['date'],
        planned_distance=planned_dict.get('distance'),
        planned_pace=planned_dict.get('avg_pace'),
        planned_exercises=planned_dict.get('exercises'),
        planned_intervals=planned_dict.get('intervals'),
        coach_comment=planned_dict.get('comment'),
        user_id=user_id  
    )

    text = f"✅ <b>Выполнение тренировки</b>\n\n"
    text += f"📝 <b>Тип:</b> {planned_dict['type'].capitalize()}\n"
    text += f"📅 <b>Дата:</b> {date_str}\n\n"

    if planned_dict.get('distance'):
        text += f"📏 <b>Плановая дистанция:</b> {format_distance(planned_dict['distance'], distance_unit)}\n"
    if planned_dict.get('avg_pace'):
        pace_unit = planned_dict.get('pace_unit', 'мин/км')
        if distance_unit == 'миль':
            pace_unit = 'мин/миля'
        text += f"⏱ <b>Желаемый темп:</b> {planned_dict['avg_pace']} {pace_unit}\n"
    if planned_dict.get('exercises'):
        text += f"💪 <b>Плановые упражнения:</b> {planned_dict['exercises']}\n"
    if planned_dict.get('intervals'):
        text += f"🔄 <b>Плановые интервалы:</b> {planned_dict['intervals']}\n"
    if planned_dict.get('comment'):
        text += f"💬 <b>Комментарий тренера:</b> {planned_dict['comment']}\n"

    text += "\n⏱ <b>Введите продолжительность тренировки</b> (в формате ЧЧ:ММ:СС или ММ:СС):\n\n"
    text += "Примеры:\n"
    text += "• <code>45:30</code> (45 минут 30 секунд)\n"
    text += "• <code>01:25:30</code> или <code>1:25:30</code> (1 час 25 минут)"

    await callback.message.edit_text(text, parse_mode="HTML")
    await state.set_state(AddTrainingStates.waiting_for_time)
    await callback.answer()


@router.callback_query(F.data == "quick_add_training")
async def quick_add_training_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик быстрого добавления тренировки из напоминания"""
    user_id = callback.from_user.id

    main_types = await get_main_training_types(user_id)

    if not main_types:
        await callback.message.answer(
            "⚠️ **Настройка основных типов тренировок**\n\n"
            "Вы еще не выбрали основные типы тренировок.\n"
            "Пожалуйста, перейдите в меню ⚙️ Настройки → 👤 Профиль → "
            "Установить основные типы тренировок",
            parse_mode="Markdown"
        )
        await callback.answer()
        return

    await callback.message.answer(
        "🏋️ **Добавление тренировки**\n\n"
        "Выберите тип тренировки:",
        reply_markup=get_training_types_keyboard(main_types),
        parse_mode="Markdown"
    )
    await state.set_state(AddTrainingStates.waiting_for_type)
    await callback.answer()


@router.callback_query(F.data.startswith("training_type:"))
async def process_training_type(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора типа тренировки"""
    training_type = callback.data.split(":")[1]
    user_id = callback.from_user.id

    main_types = await get_main_training_types(user_id)

    if training_type not in main_types:
        await callback.answer(
            "❌ Этот тип тренировки недоступен!\n"
            "Настройте основные типы в разделе Настройки → Профиль",
            show_alert=True
        )
        return

    await state.update_data(training_type=training_type)

    await callback.message.edit_text(
        f"✅ Выбран тип: **{training_type.capitalize()}**",
        parse_mode="Markdown"
    )

    calendar = CalendarKeyboard.create_calendar(1, datetime.now(), "cal", max_date=datetime.now())
    await callback.message.answer(
        "📅 Когда была тренировка?\n\n"
        "Выберите дату из календаря или используйте кнопки ниже:",
        reply_markup=calendar
    )

    await callback.message.answer(
        "Или выберите быстрый вариант:",
        reply_markup=get_date_keyboard()
    )

    await state.set_state(AddTrainingStates.waiting_for_date)
    await callback.answer()

@router.message(AddTrainingStates.waiting_for_date)
async def process_date(message: Message, state: FSMContext):
    """Обработка даты тренировки"""
    if message.text == "❌ Отменить":
        await cancel_handler(message, state)
        return
    
    user_id = message.from_user.id
    date_format = await get_user_date_format(user_id)
    
    from datetime import timedelta
    utc_now = datetime.utcnow()
    moscow_now = utc_now + timedelta(hours=3)
    today = moscow_now.date()
    yesterday = today - timedelta(days=1)
    
    if message.text in ["сегодня", "📅 Сегодня"]:
        date = today
    elif message.text in ["вчера", "📅 Вчера"]:
        date = yesterday
    elif message.text == "📝 Ввести дату":
        format_desc = DateFormatter.get_format_description(date_format)
        await message.answer(
            f"📅 Введите дату тренировки\n\n"
            f"Формат: {format_desc}",
            reply_markup=get_cancel_keyboard()
        )
        return
    else:
        date_pattern = DateFormatter.get_validation_pattern(date_format)
        if not re.match(date_pattern, message.text):
            format_desc = DateFormatter.get_format_description(date_format)
            await message.answer(
                f"❌ Неверный формат даты!\n\n"
                f"Используйте формат: {format_desc}\n"
                "Или выберите кнопку на клавиатуре"
            )
            return
        
        date = DateFormatter.parse_date(message.text, date_format)
        if date is None:
            await message.answer(
                "❌ Некорректная дата!\n\n"
                "Проверьте правильность введенной даты"
            )
            return
    
    if date > today:
        today_str = DateFormatter.format_date(today, date_format)
        date_str = DateFormatter.format_date(date, date_format)
        await message.answer(
            f"❌ Нельзя добавить тренировку в будущем!\n\n"
            f"Сегодня: {today_str}\n"
            f"Вы ввели: {date_str}\n\n"
            "Введите дату не позже сегодняшней."
        )
        return
    
    await state.update_data(date=date)
    
    date_str = DateFormatter.format_date(date, date_format)
    await message.answer(
        f"✅ Дата: {date_str}\n\n"
        "⏰ Введите время тренировки\n\n"
        "Формат: ЧЧ:ММ:СС или ММ:СС (если меньше часа)\n"
        "Примеры:\n"
        "• 45:30 (45 минут 30 секунд)\n"
        "• 01:25:30 или 1:25:30 (1 час 25 минут)\n"
        "• 25:15:45 (для ультрамарафонов)",
        reply_markup=get_cancel_keyboard()
    )
    
    await state.set_state(AddTrainingStates.waiting_for_time)

@router.message(AddTrainingStates.waiting_for_time)
async def process_time(message: Message, state: FSMContext):
    """Обработка времени тренировки"""
    if message.text == "❌ Отменить":
        await cancel_handler(message, state)
        return

    time_pattern = r'^\d{1,3}:\d{1,2}(:\d{1,2})?$'
    if not re.match(time_pattern, message.text):
        await message.answer(
            "❌ Неверный формат времени!\n\n"
            "Используйте формат: ЧЧ:ММ:СС или ММ:СС\n"
            "Примеры:\n"
            "• 45:30 (45 минут 30 секунд)\n"
            "• 01:25:30 или 1:25:30 (1 час 25 минут)"
        )
        return

    try:
        parts = message.text.split(':')

        if len(parts) == 2:
            minutes, seconds = map(int, parts)
            hours = 0
        elif len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
        else:
            raise ValueError("Неверный формат")

        if minutes > 59 or seconds > 59:
            await message.answer(
                "❌ Некорректное время!\n\n"
                "Убедитесь, что минуты ≤ 59, секунды ≤ 59"
            )
            return

        if hours == 0 and minutes == 0 and seconds == 0:
            await message.answer(
                "❌ Время тренировки не может быть 00:00:00!\n\n"
                "Минимальное время: 00:00:01\n"
                "Введите корректное время тренировки."
            )
            return

        formatted_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        total_minutes = hours * 60 + minutes + (1 if seconds > 0 else 0)

    except ValueError:
        await message.answer(
            "❌ Некорректное время!\n\n"
            "Проверьте правильность введенного времени"
        )
        return
    
    await state.update_data(time=formatted_time, duration=total_minutes)
    
    data = await state.get_data()
    training_type = data.get('training_type', 'кросс')
    
    if training_type == 'силовая':
        await message.answer(
            f"✅ Время: {formatted_time}\n\n"
            "💪 Опишите выполненные упражнения\n\n"
            "Например:\n"
            "Жим лёжа 3х10 (70кг)\n"
            "Приседания 4х12 (80кг)\n"
            "Подтягивания 3х8\n\n"
            "Или нажмите ⏭️ Пропустить",
            reply_markup=get_skip_keyboard()
        )
        await state.set_state(AddTrainingStates.waiting_for_exercises)
    elif training_type == 'интервальная':
        await message.answer(
            f"✅ Время: {formatted_time}\n\n"
            "⚡ Опишите тренировку\n\n"
            "Например:\n"
            "1. Разминка - 3000м\n"
            "2. ОРУ + СБУ + 2 ускорения по ~80м\n"
            "    Работа:\n"
            "3. 10 х 200м / 200м - (33,6; 33,0; 33,5; 34,0; 33,7; 33,3; 33,4; 33,5; 33,0; 29,0)\n"
            "4. Трусца - 600м\n"
            "   7 х 60м - многоскоки \n"
            "5. Заминка - 1000м"
        )
        await state.set_state(AddTrainingStates.waiting_for_intervals)
    else:
        user_id = message.from_user.id
        user_settings = await get_user_settings(user_id)
        distance_unit = user_settings.get('distance_unit', 'км') if user_settings else 'км'

        unit_prepositional = 'километрах' if distance_unit == 'км' else 'милях'

        await message.answer(
            f"✅ Время: {formatted_time}\n\n"
            f"🏃 Введите дистанцию в {unit_prepositional}\n\n"
            "Например: 10 или 10.5"
        )
        await state.set_state(AddTrainingStates.waiting_for_distance)

@router.message(AddTrainingStates.waiting_for_distance)
async def process_distance(message: Message, state: FSMContext):
    """Обработка дистанции"""
    if message.text == "❌ Отменить":
        await cancel_handler(message, state)
        return

    user_id = message.from_user.id
    user_settings = await get_user_settings(user_id)
    distance_unit = user_settings.get('distance_unit', 'км') if user_settings else 'км'

    try:
        distance_input = float(message.text.replace(',', '.'))
        if distance_input <= 0:
            raise ValueError
    except ValueError:
        await message.answer(
            "❌ Неверный формат!\n\n"
            f"Введите положительное число ({distance_unit})\n"
            "Например: 10 или 10.5"
        )
        return

    if distance_unit == 'мили':
        from utils.unit_converter import miles_to_km
        distance_km = miles_to_km(distance_input)
    else:
        distance_km = distance_input

    await state.update_data(distance=distance_km)

    data = await state.get_data()
    training_type = data.get('training_type', 'кросс')

    if training_type == 'плавание':
        distance_text = f"✅ Дистанция: {format_swimming_distance(distance_km, distance_unit)}"

        from bot.keyboards import get_swimming_location_keyboard
        await message.answer(
            f"{distance_text}\n\n"
            "🏊 Где проходила тренировка?",
            reply_markup=get_swimming_location_keyboard()
        )
        await state.set_state(AddTrainingStates.waiting_for_swimming_location)
    else:
        distance_text = f"✅ Дистанция: {format_distance(distance_km, distance_unit)}"

        await message.answer(
            f"{distance_text}\n\n"
            "❤️ Введите средний пульс (уд/мин)\n\n"
            "Например: 145",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(AddTrainingStates.waiting_for_avg_pulse)

@router.message(AddTrainingStates.waiting_for_avg_pulse)
async def process_avg_pulse(message: Message, state: FSMContext):
    """Обработка среднего пульса"""
    if message.text == "❌ Отменить":
        await cancel_handler(message, state)
        return

    try:
        avg_pulse = int(message.text)
        if avg_pulse < 40 or avg_pulse > 250:
            raise ValueError
    except ValueError:
        await message.answer(
            "❌ Неверный формат!\n\n"
            "Введите корректное значение пульса (40-250 уд/мин)\n"
            "Например: 145"
        )
        return

    await state.update_data(avg_pulse=avg_pulse)

    user_id = message.from_user.id
    pulse_zone = await get_pulse_zone_for_value(user_id, avg_pulse)

    zone_names = {
        'zone1': '🟢 Зона 1 (Восстановление)',
        'zone2': '🔵 Зона 2 (Аэробная)',
        'zone3': '🟡 Зона 3 (Темповая)',
        'zone4': '🟠 Зона 4 (Анаэробная)',
        'zone5': '🔴 Зона 5 (Максимальная)'
    }

    zone_info = ""
    if pulse_zone:
        zone_info = f"\n{zone_names[pulse_zone]}"

    await message.answer(
        f"✅ Средний пульс: {avg_pulse} уд/мин{zone_info}\n\n"
        "💓 Введите максимальный пульс (уд/мин)\n\n"
        "Например: 175"
    )

    await state.set_state(AddTrainingStates.waiting_for_max_pulse)

@router.message(AddTrainingStates.waiting_for_exercises)
async def process_exercises(message: Message, state: FSMContext):
    """Обработка описания упражнений для силовой тренировки"""
    if message.text == "❌ Отменить":
        await cancel_handler(message, state)
        return
    
    exercises = None if message.text == "⏭️ Пропустить" else message.text
    await state.update_data(exercises=exercises)

    await message.answer(
        "❤️ Введите средний пульс (уд/мин)\n\n"
        "Например: 130",
        reply_markup=get_cancel_keyboard()
    )
    
    await state.set_state(AddTrainingStates.waiting_for_avg_pulse)

@router.message(AddTrainingStates.waiting_for_intervals)
async def process_intervals(message: Message, state: FSMContext):
    """Обработка описания интервалов для интервальной тренировки"""
    if message.text == "❌ Отменить":
        await cancel_handler(message, state)
        return
    
    intervals = message.text
    
    from utils.interval_calculator import calculate_interval_volume, format_volume_message
    volume = calculate_interval_volume(intervals)
    
    await state.update_data(intervals=intervals, calculated_volume=volume)
    
    if volume:
        volume_msg = f"\n\n{format_volume_message(volume)}"
        await message.answer(
            f"✅ Описание сохранено{volume_msg}\n\n"
            "❤️ Введите средний пульс (уд/мин)\n\n"
            "Например: 165",
            reply_markup=get_cancel_keyboard()
        )
    else:
        await message.answer(
            "✅ Описание сохранено\n\n"
            "⚠️ Не удалось рассчитать объём автоматически\n"
            "(Возможно, не все пункты пронумерованы)\n\n"
            "❤️ Введите средний пульс (уд/мин)\n\n"
            "Например: 165",
            reply_markup=get_cancel_keyboard()
        )
    
    await state.set_state(AddTrainingStates.waiting_for_avg_pulse)



@router.callback_query(AddTrainingStates.waiting_for_swimming_location, F.data.startswith("swimming_location:"))
async def process_swimming_location(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора места для плавания"""
    location = callback.data.split(":")[1]
    await state.update_data(swimming_location=location)

    location_text = "🏊 Бассейн" if location == "pool" else "🌊 Открытая вода"

    if location == "pool":
        from bot.keyboards import get_pool_length_keyboard
        await callback.message.edit_text(
            f"✅ Место: {location_text}\n\n"
            "📏 Выберите длину бассейна:",
            reply_markup=get_pool_length_keyboard()
        )
        await state.set_state(AddTrainingStates.waiting_for_pool_length)
    else:
        from bot.keyboards import get_swimming_styles_keyboard
        await callback.message.edit_text(
            f"✅ Место: {location_text}\n\n"
            "🏊 Выберите стили плавания:",
            reply_markup=get_swimming_styles_keyboard()
        )
        await state.update_data(selected_swimming_styles=[])
        await state.set_state(AddTrainingStates.waiting_for_swimming_styles)

    await callback.answer()


@router.callback_query(AddTrainingStates.waiting_for_pool_length, F.data.startswith("pool_length:"))
async def process_pool_length(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора длины бассейна"""
    pool_length = int(callback.data.split(":")[1])
    await state.update_data(pool_length=pool_length)

    from bot.keyboards import get_swimming_styles_keyboard
    await callback.message.edit_text(
        f"✅ Бассейн {pool_length}м\n\n"
        "🏊 Выберите стили плавания:",
        reply_markup=get_swimming_styles_keyboard()
    )

    await state.update_data(selected_swimming_styles=[])
    await state.set_state(AddTrainingStates.waiting_for_swimming_styles)
    await callback.answer()


@router.callback_query(AddTrainingStates.waiting_for_swimming_styles, F.data.startswith("swimming_style:"))
async def process_swimming_style_toggle(callback: CallbackQuery, state: FSMContext):
    """Обработка переключения стилей плавания (множественный выбор)"""
    style = callback.data.split(":")[1]

    data = await state.get_data()
    selected_styles = data.get('selected_swimming_styles', [])

    if style in selected_styles:
        selected_styles.remove(style)
    else:
        selected_styles.append(style)

    await state.update_data(selected_swimming_styles=selected_styles)

    from bot.keyboards import update_swimming_styles_keyboard
    await callback.message.edit_reply_markup(
        reply_markup=update_swimming_styles_keyboard(selected_styles)
    )

    await callback.answer()


@router.callback_query(AddTrainingStates.waiting_for_swimming_styles, F.data == "swimming_styles:done")
async def process_swimming_styles_done(callback: CallbackQuery, state: FSMContext):
    """Завершение выбора стилей плавания"""
    data = await state.get_data()
    selected_styles = data.get('selected_swimming_styles', [])

    if not selected_styles:
        await callback.answer("⚠️ Выберите хотя бы один стиль!", show_alert=True)
        return

    from utils.swimming_pace import format_swimming_styles
    styles_text = format_swimming_styles(selected_styles)

    await callback.message.edit_text(
        f"✅ Стили: {styles_text}\n\n"
        "📝 Опишите отрезки тренировки\n\n"
        "Например:\n"
        "1. Разминка - 400м вольный стиль\n"
        "2. Основная часть:\n"
        "   - 8x100м вольный (1:30 на 100м)\n"
        "   - 4x200м брасс (3:20 на 200м)\n"
        "3. Заминка - 200м вольный\n\n"
        "Или нажмите ⏭️ Пропустить"
    )

    await callback.message.answer(
        "Введите описание или пропустите:",
        reply_markup=get_skip_keyboard()
    )

    await state.set_state(AddTrainingStates.waiting_for_swimming_sets)
    await callback.answer()


@router.message(AddTrainingStates.waiting_for_swimming_sets)
async def process_swimming_sets(message: Message, state: FSMContext):
    """Обработка описания отрезков для плавания"""
    if message.text == "❌ Отменить":
        await cancel_handler(message, state)
        return

    swimming_sets = None if message.text == "⏭️ Пропустить" else message.text
    await state.update_data(swimming_sets=swimming_sets)

    if swimming_sets:
        await message.answer("✅ Описание отрезков сохранено")

    await message.answer(
        "❤️ Введите средний пульс (уд/мин)\n\n"
        "Например: 130",
        reply_markup=get_cancel_keyboard()
    )

    await state.set_state(AddTrainingStates.waiting_for_avg_pulse)


@router.message(AddTrainingStates.waiting_for_max_pulse)
async def process_max_pulse(message: Message, state: FSMContext):
    """Обработка максимального пульса"""
    if message.text == "❌ Отменить":
        await cancel_handler(message, state)
        return

    try:
        max_pulse = int(message.text)
        if max_pulse < 40 or max_pulse > 250:
            raise ValueError
    except ValueError:
        await message.answer(
            "❌ Неверный формат!\n\n"
            "Введите корректное значение пульса (40-250 уд/мин)\n"
            "Например: 175"
        )
        return

    data = await state.get_data()
    avg_pulse = data.get('avg_pulse', 0)

    if max_pulse < avg_pulse:
        await message.answer(
            f"❌ Ошибка!\n\n"
            f"Максимальный пульс ({max_pulse}) не может быть меньше среднего ({avg_pulse})!\n\n"
            f"Введите корректное значение максимального пульса:"
        )
        return

    await state.update_data(max_pulse=max_pulse)

    user_id = message.from_user.id
    pulse_zone = await get_pulse_zone_for_value(user_id, max_pulse)

    zone_names = {
        'zone1': '🟢 Зона 1 (Восстановление)',
        'zone2': '🔵 Зона 2 (Аэробная)',
        'zone3': '🟡 Зона 3 (Темповая)',
        'zone4': '🟠 Зона 4 (Анаэробная)',
        'zone5': '🔴 Зона 5 (Максимальная)'
    }

    zone_info = ""
    if pulse_zone:
        zone_info = f"\n{zone_names[pulse_zone]}"

    await message.answer(
        f"✅ Максимальный пульс: {max_pulse} уд/мин{zone_info}\n\n"
        "💬 Добавьте комментарий к тренировке\n\n"
        "Например: Хорошая форма, легко пробежал\n\n"
        "Или нажмите ⏭️ Пропустить",
        reply_markup=get_skip_keyboard()
    )

    await state.set_state(AddTrainingStates.waiting_for_comment)

@router.message(AddTrainingStates.waiting_for_comment)
async def process_comment(message: Message, state: FSMContext):
    """Обработка комментария"""
    if message.text == "❌ Отменить":
        await cancel_handler(message, state)
        return
    
    comment = None if message.text == "⏭️ Пропустить" else message.text
    await state.update_data(comment=comment)
    
    await message.answer(
        "💪 Оцените уровень усилий на тренировке\n\n"
        "Выберите от 1 (очень легко) до 10 (максимальные усилия):",
        reply_markup=ReplyKeyboardRemove()
    )

    await message.answer(
        "Выберите уровень усилий:",
        reply_markup=get_fatigue_keyboard()
    )
    
    await state.set_state(AddTrainingStates.waiting_for_fatigue)

@router.callback_query(F.data.startswith("fatigue:"))
async def process_fatigue(callback: CallbackQuery, state: FSMContext):
    """Обработка уровня усилий и сохранение тренировки"""
    fatigue_level = int(callback.data.split(":")[1])
    
    data = await state.get_data()
    data['fatigue_level'] = fatigue_level
    data['user_id'] = callback.from_user.id
    
    user_settings = await get_user_settings(callback.from_user.id)
    distance_unit = user_settings.get('distance_unit', 'км') if user_settings else 'км'
    date_format = user_settings.get('date_format', 'DD.MM.YYYY') if user_settings else 'DD.MM.YYYY'

    if 'training_type' not in data:
        await callback.message.edit_text("❌ Ошибка: не удалось определить тип тренировки. Попробуйте добавить тренировку заново.")
        await state.clear()
        await callback.answer()
        return

    training_type = data['training_type']

    if 'time' in data and data['time']:
        time_str = data['time']
        hours, minutes, seconds = map(int, time_str.split(':'))
        total_seconds = hours * 3600 + minutes * 60 + seconds
        total_minutes = total_seconds / 60

        if training_type not in ['силовая', 'интервальная'] and 'distance' in data:
            distance = data['distance']

            avg_pace, pace_unit = format_pace(
                distance,
                total_seconds,
                distance_unit,
                training_type
            )

            data['avg_pace'] = avg_pace
            data['pace_unit'] = pace_unit
    

    if 'planned_training_id' in data and data['planned_training_id']:
        import aiosqlite
        import os
        DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

        coach_id = None
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT added_by_coach_id FROM trainings WHERE id = ?",
                (data['planned_training_id'],)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    coach_id = row[0]

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """
                UPDATE trainings
                SET time = ?, duration = ?, distance = ?, avg_pace = ?, pace_unit = ?,
                    avg_pulse = ?, max_pulse = ?, exercises = ?, intervals = ?,
                    calculated_volume = ?, description = ?, results = ?, comment = ?,
                    fatigue_level = ?, is_planned = 0
                WHERE id = ? AND user_id = ?
                """,
                (
                    data.get('time'),
                    data.get('duration'),
                    data.get('distance'),
                    data.get('avg_pace'),
                    data.get('pace_unit'),
                    data.get('avg_pulse'),
                    data.get('max_pulse'),
                    data.get('exercises'),
                    data.get('intervals'),
                    data.get('calculated_volume'),
                    data.get('description'),
                    data.get('results'),
                    data.get('comment'),
                    data.get('fatigue_level'),
                    data['planned_training_id'],
                    data['user_id']
                )
            )
            await db.commit()

        if coach_id:
            try:
                from coach.coach_training_queries import get_student_display_name

                student_name = await get_student_display_name(coach_id, data['user_id'])

                coach_date_format = await get_user_date_format(coach_id)
                coach_settings = await get_user_settings(coach_id)
                distance_unit = coach_settings.get('distance_unit', 'км') if coach_settings else 'км'

                date_str = DateFormatter.format_date(data.get('date'), coach_date_format)

                type_emoji = {
                    'кросс': '🏃',
                    'плавание': '🏊',
                    'велотренировка': '🚴',
                    'силовая': '💪',
                    'интервальная': '⚡'
                }
                emoji = type_emoji.get(data['training_type'], '📝')

                report = f"✅ <b>Тренировка выполнена!</b>\n\n"
                report += f"Ученик: <b>{student_name}</b>\n\n"
                report += f"{emoji} <b>Тип:</b> {data['training_type'].capitalize()}\n"
                report += f"📅 <b>Дата:</b> {date_str}\n"

                if data.get('time'):
                    report += f"⏱ <b>Время:</b> {data['time']}\n"

                if data.get('distance'):
                    report += f"📏 <b>Дистанция:</b> {format_distance(data['distance'], distance_unit)}\n"

                if data.get('avg_pace'):
                    report += f"⚡ <b>Средний темп:</b> {data['avg_pace']} {data.get('pace_unit', '')}\n"

                if data.get('avg_pulse'):
                    report += f"❤️ <b>Средний пульс:</b> {data['avg_pulse']} уд/мин\n"

                if data.get('fatigue_level'):
                    report += f"💪 <b>Уровень усилий:</b> {data['fatigue_level']}/10\n"

                if data.get('comment'):
                    report += f"\n💬 <b>Комментарий ученика:</b>\n<i>{data['comment']}</i>\n"

                from aiogram.utils.keyboard import InlineKeyboardBuilder
                from aiogram.types import InlineKeyboardButton

                builder = InlineKeyboardBuilder()
                builder.row(
                    InlineKeyboardButton(
                        text="📊 Подробная информация",
                        callback_data=f"coach:training_detail:{data['planned_training_id']}:{data['user_id']}"
                    )
                )

                await callback.bot.send_message(
                    coach_id,
                    report,
                    reply_markup=builder.as_markup(),
                    parse_mode="HTML"
                )

                coach_is_coach = await is_user_coach(coach_id)
                await callback.bot.send_message(
                    coach_id,
                    "Главное меню:",
                    reply_markup=get_main_menu_keyboard(coach_is_coach)
                )

                logger.info(f"Training report sent to coach {coach_id} for student {data['user_id']}")
            except Exception as e:
                logger.error(f"Failed to send training report to coach: {e}")
    else:
        await add_training(data)

    try:
        await update_single_user_rating(callback.from_user.id)
    except Exception as e:
        logger.error(f"Ошибка при обновлении рейтинга: {str(e)}")

    try:
        level_update = await calculate_and_update_user_level(callback.from_user.id)
        if level_update['level_changed']:
            logger.info(f"Уровень пользователя {callback.from_user.id} изменен: "
                       f"{level_update['old_level']} -> {level_update['new_level']}")
            from ratings.user_levels import get_level_emoji
            new_emoji = get_level_emoji(level_update['new_level'])
            levels_order = ['новичок', 'любитель', 'профи', 'элитный']
            old_idx = levels_order.index(level_update['old_level']) if level_update['old_level'] in levels_order else 0
            new_idx = levels_order.index(level_update['new_level']) if level_update['new_level'] in levels_order else 0
            if new_idx > old_idx:
                await callback.bot.send_message(
                    callback.from_user.id,
                    f"🎉 <b>Уровень повышен!</b>\n\n"
                    f"Вы поднялись до уровня {new_emoji} <b>{level_update['new_level'].capitalize()}</b>!\n\n"
                    f"Продолжайте тренироваться для повышения уровня!",
                    parse_mode="HTML"
                )
            elif new_idx < old_idx:
                await callback.bot.send_message(
                    callback.from_user.id,
                    f"📉 <b>Уровень изменён</b>\n\n"
                    f"Ваш уровень теперь {new_emoji} <b>{level_update['new_level'].capitalize()}</b>.\n\n"
                    f"Добавляйте тренировки, чтобы вернуться к прежнему уровню!",
                    parse_mode="HTML"
                )
    except Exception as e:
        logger.error(f"Ошибка при обновлении уровня: {str(e)}")

    try:
        await check_weekly_goals(callback.from_user.id, callback.bot, training_type)
    except Exception as e:
        logger.error(f"Ошибка при проверке целей: {str(e)}")

    try:
        from ratings.achievements_checker import check_and_award_achievements
        new_achievements = await check_and_award_achievements(callback.from_user.id, callback.bot)
        if new_achievements:
            logger.info(f"Пользователь {callback.from_user.id} получил {len(new_achievements)} новых достижений")
    except Exception as e:
        logger.error(f"Ошибка при проверке достижений: {str(e)}")

    training_type = data['training_type']
    
    if training_type == 'плавание':
        training_emoji = "🏊"
    elif training_type == 'велотренировка':
        training_emoji = "🚴"
    elif training_type == 'силовая':
        training_emoji = "💪"
    elif training_type == 'интервальная':
        training_emoji = "⚡"
    else:  
        training_emoji = "🏃"
    
    date_str = DateFormatter.format_date(data['date'], date_format)
    
    summary = (
        "✅ **Тренировка успешно добавлена!**\n\n"
        f"📅 Дата: {date_str}\n"
        f"{training_emoji} Тип: {training_type.capitalize()}\n"
        f"⏰ Время: {data['time']}\n"
    )
    
    if training_type == 'силовая':
        if data.get('exercises'):
            summary += f"💪 Упражнения:\n{data['exercises']}\n"
    elif training_type == 'интервальная':
        if data.get('intervals'):
            summary += f"⚡ Описание:\n{data['intervals']}\n"
            
            if data.get('calculated_volume'):
                from utils.interval_calculator import format_volume_message
                volume_text = format_volume_message(data['calculated_volume'])
                if volume_text:
                    summary += f"{volume_text}\n"
            
            from utils.interval_calculator import calculate_average_interval_pace
            avg_pace_intervals = calculate_average_interval_pace(data['intervals'])
            if avg_pace_intervals:
                summary += f"⚡ Средний темп отрезков: {avg_pace_intervals}\n"
    else:
        distance_km = data['distance']
        
        if training_type == 'плавание':
            distance_text = f"📏 Дистанция: {format_swimming_distance(distance_km, distance_unit)}"
        else:
            distance_text = f"📏 Дистанция: {format_distance(distance_km, distance_unit)}"
        
        pace_emoji = "⚡"
        if training_type == 'велотренировка':
            pace_label = "Средняя скорость"
        else:
            pace_label = "Средний темп"
        
        summary += (
            f"{distance_text}\n"
            f"{pace_emoji} {pace_label}: {avg_pace} {pace_unit}\n"
        )

        if training_type == 'плавание':
            if data.get('swimming_location'):
                from utils.swimming_pace import format_swimming_location
                location_text = format_swimming_location(data['swimming_location'], data.get('pool_length'))
                summary += f"📍 Место: {location_text}\n"

            if data.get('selected_swimming_styles'):
                from utils.swimming_pace import format_swimming_styles
                styles_text = format_swimming_styles(data['selected_swimming_styles'])
                summary += f"🏊 Стили: {styles_text}\n"

            if data.get('swimming_sets'):
                summary += f"📝 Отрезки:\n{data['swimming_sets']}\n"

    if data.get('avg_pulse') and data.get('max_pulse'):
        summary += f"❤️ Средний пульс: {data['avg_pulse']} уд/мин\n"
        summary += f"💓 Максимальный пульс: {data['max_pulse']} уд/мин\n"
    
    if data.get('comment'):
        summary += f"💬 Комментарий: {data['comment']}\n"
    
    summary += f"💪 Усилия: {fatigue_level}/10"

    await callback.message.edit_text(summary, parse_mode="Markdown")

    is_coach_status = await is_user_coach(callback.from_user.id)
    await callback.message.answer(
        "Что делаем дальше?",
        reply_markup=get_main_menu_keyboard(is_coach_status)
    )

    await state.clear()
    await callback.answer("Тренировка сохранена! ✅")

@router.message(F.text == "❌ Отменить")
@router.callback_query(F.data == "cancel")
async def cancel_handler(message: Union[Message, CallbackQuery], state: FSMContext):
    """Отмена текущей операции с контекстно-зависимой навигацией"""
    logger.warning(f"🔴 GLOBAL cancel_handler called!")
    current_state = await state.get_state()
    logger.warning(f"🔴 GLOBAL cancel_handler - current_state: {current_state}")

    if current_state is None:
        if isinstance(message, Message):
            is_coach_status = await is_user_coach(message.from_user.id)
            await message.answer(
                "Нечего отменять 🤷‍♂️",
                reply_markup=get_main_menu_keyboard(is_coach_status)
            )
        return

    user_id = message.from_user.id if isinstance(message, Message) else message.from_user.id

    await state.clear()

    if 'AddTrainingStates' in current_state:
        cancel_text = "❌ Добавление тренировки отменено"
    elif 'ExportPDFStates' in current_state:
        cancel_text = "❌ Экспорт отменён"
    elif 'SettingsStates' in current_state:
        cancel_text = "❌ Изменение настроек отменено"
    elif 'CompetitionStates' in current_state:
        cancel_text = "❌ Операция с соревнованием отменена"
    elif 'CoachStates' in current_state:
        cancel_text = "❌ Операция отменена"
    elif 'RegistrationStates' in current_state:
        cancel_text = "❌ Регистрация отменена"
    elif 'HealthMetricsStates' in current_state or 'HealthExportStates' in current_state:
        cancel_text = "❌ Действие отменено"
    else:
        cancel_text = "❌ Действие отменено"

    is_coach = await is_user_coach(user_id)

    menu_text = "Вы в главном меню"
    keyboard = get_main_menu_keyboard(is_coach=is_coach)

    if isinstance(message, CallbackQuery):
        try:
            await message.message.edit_text(
                f"{cancel_text}\n\n{menu_text}",
                reply_markup=None
            )
        except Exception:
            await message.message.answer(
                f"{cancel_text}\n\n{menu_text}"
            )

        await message.message.answer(
            "Главное меню:",
            reply_markup=keyboard
        )
        await message.answer()
    else:
        await message.answer(
            f"{cancel_text}\n\n{menu_text}",
            reply_markup=keyboard
        )

@router.message(F.text == "📊 Мои тренировки")
async def show_my_trainings(message: Message):
    """Показать меню выбора периода для просмотра тренировок"""
    await message.answer(
        "📊 *Мои тренировки*\n\n"
        "Выберите период для просмотра:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    await message.answer(
        "Выберите период:",
        reply_markup=get_period_keyboard()
    )

@router.callback_query(F.data.startswith("period:"))
async def show_trainings_period(callback: CallbackQuery, state: FSMContext):
    """Показать тренировки за выбранный период с детальной статистикой"""
    period = callback.data.split(":")[1]

    data = await state.get_data()
    old_message_ids = data.get('trainings_message_ids', [])
    for msg_id in old_message_ids:
        try:
            await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=msg_id)
        except Exception:
            pass
    await state.update_data(trainings_message_ids=[])

    user_settings = await get_user_settings(callback.from_user.id)
    distance_unit = user_settings.get('distance_unit', 'км') if user_settings else 'км'
    date_format = user_settings.get('date_format', 'DD.MM.YYYY') if user_settings else 'DD.MM.YYYY'
    
    period_days = {
        "week": 7,
        "2weeks": 14,
        "month": 30
    }
    
    period_names = {
        "week": "неделю",
        "2weeks": "2 недели",
        "month": "месяц"
    }
    
    days = period_days.get(period, 7)
    period_name = period_names.get(period, "период")
    
    stats = await get_training_statistics(callback.from_user.id, period)
    trainings = await get_trainings_by_period(callback.from_user.id, period)
    
    if not trainings:
        await callback.message.edit_text(
            f"📊 *Тренировки за {period_name}*\n\n"
            f"У вас пока нет тренировок за этот период.\n\n"
            f"_Обновлено: {datetime.now().strftime('%H:%M:%S')}_",
            parse_mode="Markdown",
            reply_markup=get_period_keyboard()
        )
        await callback.answer()
        return
    
    from datetime import timedelta
    today = datetime.now().date()
    
    if period == 'week':
        start_date = today - timedelta(days=today.weekday())
        start_date_str = DateFormatter.format_date(start_date, date_format).split('.')[-1] if date_format == 'DD.MM.YYYY' else DateFormatter.format_date(start_date, date_format).rsplit('.', 1)[0] if '.' in DateFormatter.format_date(start_date, date_format) else DateFormatter.format_date(start_date, date_format).rsplit('/', 1)[0] if '/' in DateFormatter.format_date(start_date, date_format) else DateFormatter.format_date(start_date, date_format).rsplit('-', 1)[0]
        if date_format == 'DD.MM.YYYY':
            period_display = f"неделю (с {start_date.strftime('%d.%m')} по сегодня)"
        elif date_format == 'MM/DD/YYYY':
            period_display = f"неделю (с {start_date.strftime('%m/%d')} по сегодня)"
        else:
            period_display = f"неделю (с {start_date.strftime('%m-%d')} по сегодня)"
    elif period == '2weeks':
        start_date = today - timedelta(days=today.weekday() + 7)
        if date_format == 'DD.MM.YYYY':
            period_display = f"2 недели (с {start_date.strftime('%d.%m')} по сегодня)"
        elif date_format == 'MM/DD/YYYY':
            period_display = f"2 недели (с {start_date.strftime('%m/%d')} по сегодня)"
        else:
            period_display = f"2 недели (с {start_date.strftime('%m-%d')} по сегодня)"
    elif period == 'month':
        start_date = today.replace(day=1)
        if date_format == 'DD.MM.YYYY':
            period_display = f"месяц (с {start_date.strftime('%d.%m')} по сегодня)"
        elif date_format == 'MM/DD/YYYY':
            period_display = f"месяц (с {start_date.strftime('%m/%d')} по сегодня)"
        else:
            period_display = f"месяц (с {start_date.strftime('%m-%d')} по сегодня)"
    else:
        period_display = period_name
    
    message_text = f"📊 *Тренировки за {period_display}*\n\n"
    message_text += "━━━━━━━━━━━━━━━━━━\n"
    message_text += "📈 *ОБЩАЯ СТАТИСТИКА*\n"
    message_text += "━━━━━━━━━━━━━━━━━━\n\n"
    
    message_text += f"🏃 Всего тренировок: *{stats['total_count']}*\n"
    
    if stats['total_distance'] > 0:
        message_text += f"📏 Общий километраж: *{format_distance(stats['total_distance'], distance_unit)}*\n"
        
        if period in ['2weeks', 'month']:
            days_in_period = (today - start_date).days + 1  
            weeks_count = days_in_period / 7
            
            if weeks_count > 0:
                avg_per_week = stats['total_distance'] / weeks_count
                message_text += f"   _(Средний за неделю: {format_distance(avg_per_week, distance_unit)})_\n"
    
    if stats['types_count']:
        message_text += f"\n📋 *Типы тренировок:*\n"
        
        type_emoji = {
            'кросс': '🏃',
            'плавание': '🏊',
            'велотренировка': '🚴',
            'силовая': '💪',
            'интервальная': '⚡'
        }
        
        sorted_types = sorted(stats['types_count'].items(), key=lambda x: x[1], reverse=True)
        
        for t_type, count in sorted_types:
            emoji = type_emoji.get(t_type, '📝')
            percentage = (count / stats['total_count']) * 100
            message_text += f"  {emoji} {t_type.capitalize()}: {count} ({percentage:.1f}%)\n"
    
    if stats['avg_fatigue'] > 0:
        message_text += f"\n💪 Средний уровень усилий: *{stats['avg_fatigue']}/10*\n"
    
    message_text += "\n━━━━━━━━━━━━━━━━━━\n"
    message_text += "📝 *СПИСОК ТРЕНИРОВОК*\n"
    message_text += "━━━━━━━━━━━━━━━━━━\n\n"
    
    type_emoji = {
        'кросс': '🏃',
        'плавание': '🏊',
        'велотренировка': '🚴',
        'силовая': '💪',
        'интервальная': '⚡'
    }

    for idx, training in enumerate(trainings[:15], 1):  
        date = DateFormatter.format_date(training['date'], date_format)
        t_type = training['type']
        emoji = type_emoji.get(t_type, '📝')
        
        message_text += f"*{idx}.* {emoji} *{t_type.capitalize()}* • {date}\n"
        
        if training.get('time'):
            message_text += f"   ⏰ Время: {training['time']}\n"
        
        if t_type == 'интервальная':
            if training.get('calculated_volume'):
                message_text += f"   📏 Дистанция: {format_distance(training['calculated_volume'], distance_unit)}\n"
        else:
            if training.get('distance'):
                if t_type == 'плавание':
                    message_text += f"   📏 Дистанция: {format_swimming_distance(training['distance'], distance_unit)}\n"
                else:
                    message_text += f"   📏 Дистанция: {format_distance(training['distance'], distance_unit)}\n"
        
        if t_type == 'интервальная':
            if training.get('intervals'):
                from utils.interval_calculator import calculate_average_interval_pace
                avg_pace_intervals = calculate_average_interval_pace(training['intervals'])
                if avg_pace_intervals:
                    message_text += f"   ⚡ Средний темп отрезков: {avg_pace_intervals}\n"
        elif t_type == 'велотренировка':
            if training.get('avg_pace'):
                message_text += f"   🚴 Средняя скорость: {training['avg_pace']} {training.get('pace_unit', '')}\n"
        elif t_type != 'силовая':
            if training.get('avg_pace'):
                message_text += f"   ⚡ Средний темп: {training['avg_pace']} {training.get('pace_unit', '')}\n"
        
        if training.get('avg_pulse'):
            message_text += f"   ❤️ Пульс: {training['avg_pulse']} уд/мин\n"

        if training.get('fatigue_level'):
            message_text += f"   💪 Усилия: {training['fatigue_level']}/10\n"
        
        message_text += "\n"
    
    if len(trainings) > 15:
        message_text += f"_... и ещё {len(trainings) - 15} тренировок_\n"

    try:
        await callback.message.edit_text(
            message_text,
            parse_mode="Markdown",
            reply_markup=get_period_keyboard(period)
        )
    except Exception as e:
        if "message is not modified" in str(e):
            await callback.answer("Данные актуальны", show_alert=False)
        else:
            logger.error(f"Ошибка при редактировании сообщения: {str(e)}")
            raise
    
    new_message_ids = []
    if len(trainings) >= 2:
        try:
            period_captions = {
                'week': 'за неделю',
                '2weeks': 'за 2 недели',
                'month': 'за месяц'
            }
            caption_suffix = period_captions.get(period, '')

            combined_graph = generate_graphs(trainings, period, days, distance_unit)
            logger.info(f"Отправка объединённого графика для периода {period}...")

            if combined_graph:
                graph_msg = await callback.message.answer_photo(
                    photo=BufferedInputFile(combined_graph.read(), filename="statistics.png"),
                    caption=f"📊 Статистика тренировок {caption_suffix}"
                )
                new_message_ids.append(graph_msg.message_id)
                logger.info("Объединённый график отправлен")
            else:
                logger.warning("Не удалось создать графики")
                warning_msg = await callback.message.answer("⚠️ Недостаточно данных для создания графиков")
                new_message_ids.append(warning_msg.message_id)

        except Exception as e:
            logger.error(f"Ошибка при отправке графика: {str(e)}", exc_info=True)
            error_msg = await callback.message.answer(f"❌ Ошибка при создания графиков: {str(e)}")
            new_message_ids.append(error_msg.message_id)
    else:
        logger.info(f"Недостаточно тренировок для графиков: {len(trainings)} (минимум 2)")

    menu_msg = await callback.message.answer(
        "📋 *Выберите тренировку для просмотра деталей:*\n\n"
        "Нажмите на номер тренировки или выберите другой период",
        parse_mode="Markdown",
        reply_markup=get_trainings_list_keyboard(trainings, period, date_format)
    )
    new_message_ids.append(menu_msg.message_id)

    await state.update_data(trainings_message_ids=new_message_ids)

    await callback.answer()


@router.callback_query(F.data.startswith("ai_analyze_trainings:"))
async def ai_analyze_trainings(callback: CallbackQuery):
    """AI-анализ статистики тренировок за период"""
    period = callback.data.split(":")[1]
    user_id = callback.from_user.id

    if not is_ai_available():
        await callback.answer(
            "❌ AI-анализ недоступен. Добавьте OPENROUTER_API_KEY в .env файл",
            show_alert=True
        )
        return

    await callback.answer("🤖 Анализирую данные...", show_alert=False)

    processing_msg = await callback.message.answer("🤖 AI анализирует ваши тренировки...")

    try:
        user_settings = await get_user_settings(user_id)
        distance_unit = user_settings.get('distance_unit', 'км') if user_settings else 'км'

        trainings = await get_trainings_by_period(user_id, period)
        statistics = await get_training_statistics(user_id, period)

        if not trainings:
            await processing_msg.edit_text(
                "❌ Нет тренировок за выбранный период для анализа"
            )
            return

        analysis = await analyze_training_statistics(
            statistics=statistics,
            trainings=trainings,
            period=period,
            distance_unit=distance_unit
        )

        if analysis:
            import html
            period_names = {
                "week": "неделю",
                "2weeks": "2 недели",
                "month": "месяц"
            }
            period_name = period_names.get(period, period)

            safe_analysis = html.escape(analysis)

            msg_text = (
                f"🤖 <b>AI-анализ тренировок за {period_name}</b>\n\n"
                f"{safe_analysis}\n\n"
                f"<i>Анализ создан с помощью Google Gemini</i>"
            )

            await processing_msg.edit_text(msg_text, parse_mode="HTML")

            from coach.coach_queries import is_user_coach
            is_coach_status = await is_user_coach(user_id)
            await processing_msg.answer(
                "Выбери действие из меню 👇",
                reply_markup=get_main_menu_keyboard(is_coach_status)
            )
        else:
            await processing_msg.edit_text(
                "❌ Не удалось создать AI-анализ. Попробуйте позже."
            )

    except Exception as e:
        logger.error(f"Ошибка при AI-анализе тренировок: {e}")
        await processing_msg.edit_text(
            "❌ Произошла ошибка при анализе. Попробуйте позже."
        )


@router.callback_query(F.data.startswith("delete_training:"))
async def request_delete_confirmation(callback: CallbackQuery):
    """Запрос подтверждения удаления тренировки"""
    parts = callback.data.split(":")
    training_id = int(parts[1])
    period = parts[2]
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete:{training_id}:{period}"),
        InlineKeyboardButton(text="❌ Нет", callback_data="cancel_delete")
    )
    
    await callback.message.answer(
        f"🗑 Вы уверены, что хотите удалить эту тренировку?",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("confirm_delete:"))
async def confirm_delete(callback: CallbackQuery):
    """Подтверждение и выполнение удаления тренировки"""
    parts = callback.data.split(":")
    training_id = int(parts[1])
    period = parts[2]
    user_id = callback.from_user.id
    
    user_settings = await get_user_settings(user_id)
    date_format = user_settings.get('date_format', 'DD.MM.YYYY') if user_settings else 'DD.MM.YYYY'
    
    deleted = await delete_training(training_id, user_id)
    
    if deleted:
        await callback.message.answer(f"✅ Тренировка удалена!")
        
        stats = await get_training_statistics(user_id, period)
        trainings = await get_trainings_by_period(user_id, period)
        
        if not trainings:
            period_names = {"week": "неделю", "2weeks": "2 недели", "month": "месяц"}
            period_name = period_names.get(period, "период")
            await callback.message.answer(
                f"📊 *Тренировки за {period_name}*\n\n"
                f"У вас больше нет тренировок за этот период.",
                parse_mode="Markdown",
                reply_markup=get_period_keyboard()
            )
            await callback.message.delete()  
            await callback.answer()
            return
        
        period_days = {"week": 7, "2weeks": 14, "month": 30}
        period_names = {"week": "неделю", "2weeks": "2 недели", "month": "месяц"}
        days = period_days.get(period, 7)
        period_name = period_names.get(period, "период")
        
        from datetime import timedelta
        today = datetime.now().date()
        if period == 'week':
            start_date = today - timedelta(days=today.weekday())
            period_display = f"неделю (с {start_date.strftime('%d.%m')} по сегодня)"
        elif period == '2weeks':
            start_date = today - timedelta(days=today.weekday() + 7)
            period_display = f"2 недели (с {start_date.strftime('%d.%m')} по сегодня)"
        elif period == 'month':
            start_date = today.replace(day=1)
            period_display = f"месяц (с {start_date.strftime('%d.%m')} по сегодня)"
        else:
            period_display = period_name
        
        message_text = f"📊 *Тренировки за {period_display}*\n\n"
        message_text += "━━━━━━━━━━━━━━━━━━\n"
        message_text += "📈 *ОБЩАЯ СТАТИСТИКА*\n"
        message_text += "━━━━━━━━━━━━━━━━━━\n\n"
        message_text += f"🏃 Всего тренировок: *{stats['total_count']}*\n"
        if stats['total_distance'] > 0:
            distance_unit = user_settings.get('distance_unit', 'км') if user_settings else 'км'
            message_text += f"📏 Общий километраж: *{format_distance(stats['total_distance'], distance_unit)}*\n"
            if period in ['2weeks', 'month']:
                days_in_period = (today - start_date).days + 1
                weeks_count = days_in_period / 7
                if weeks_count > 0:
                    avg_per_week = stats['total_distance'] / weeks_count
                    message_text += f"   _(Средний за неделю: {format_distance(avg_per_week, distance_unit)})_\n"
        if stats['types_count']:
            message_text += f"\n📋 *Типы тренировок:*\n"
            type_emoji = {
                'кросс': '🏃', 'плавание': '🏊', 'велотренировка': '🚴', 'силовая': '💪', 'интервальная': '⚡'
            }
            sorted_types = sorted(stats['types_count'].items(), key=lambda x: x[1], reverse=True)
            for t_type, count in sorted_types:
                emoji = type_emoji.get(t_type, '📝')
                percentage = (count / stats['total_count']) * 100
                message_text += f"  {emoji} {t_type.capitalize()}: {count} ({percentage:.1f}%)\n"
        if stats['avg_fatigue'] > 0:
            message_text += f"\n💪 Средний уровень усилий: *{stats['avg_fatigue']}/10*\n"
        message_text += "\n━━━━━━━━━━━━━━━━━━\n"
        message_text += "📝 *СПИСОК ТРЕНИРОВОК*\n"
        message_text += "━━━━━━━━━━━━━━━━━━\n\n"

        for idx, training in enumerate(trainings[:15], 1):
            date = DateFormatter.format_date(training['date'], date_format)
            t_type = training['type']
            emoji = type_emoji.get(t_type, '📝')
            message_text += f"*{idx}.* {emoji} *{t_type.capitalize()}* • {date}\n"
            if training.get('time'):
                message_text += f"   ⏰ Время: {training['time']}\n"
            if t_type == 'интервальная':
                if training.get('calculated_volume'):
                    message_text += f"   📏 Дистанция: {format_distance(training['calculated_volume'], distance_unit)}\n"
            else:
                if training.get('distance'):
                    if t_type == 'плавание':
                        message_text += f"   📏 Дистанция: {format_swimming_distance(training['distance'], distance_unit)}\n"
                    else:
                        message_text += f"   📏 Дистанция: {format_distance(training['distance'], distance_unit)}\n"
            if t_type == 'интервальная' and training.get('intervals'):
                from utils.interval_calculator import calculate_average_interval_pace
                avg_pace_intervals = calculate_average_interval_pace(training['intervals'])
                if avg_pace_intervals:
                    message_text += f"   ⚡ Средний темп отрезков: {avg_pace_intervals}\n"
            elif t_type == 'велотренировка' and training.get('avg_pace'):
                message_text += f"   🚴 Средняя скорость: {training['avg_pace']} {training.get('pace_unit', '')}\n"
            elif t_type != 'силовая' and training.get('avg_pace'):
                message_text += f"   ⚡ Средний темп: {training['avg_pace']} {training.get('pace_unit', '')}\n"
            if training.get('avg_pulse'):
                message_text += f"   ❤️ Пульс: {training['avg_pulse']} уд/мин\n"
            if training.get('fatigue_level'):
                message_text += f"   💪 Усилия: {training['fatigue_level']}/10\n"
            message_text += "\n"
        if len(trainings) > 15:
            message_text += f"_... и ещё {len(trainings) - 15} тренировок_\n"

        try:
            await callback.message.edit_text(
                message_text,
                parse_mode="Markdown",
                reply_markup=get_period_keyboard(period)
            )
        except Exception as e:
            if "message is not modified" in str(e):
                await callback.answer("Данные актуальны", show_alert=False)
            else:
                logger.error(f"Ошибка при редактировании сообщения: {str(e)}")
                raise
        
        if len(trainings) >= 2:
            try:
                period_captions = {'week': 'за неделю', '2weeks': 'за 2 недели', 'month': 'за месяц'}
                caption_suffix = period_captions.get(period, '')
                combined_graph = generate_graphs(trainings, period, days, distance_unit)
                if combined_graph:
                    await callback.message.answer_photo(
                        photo=BufferedInputFile(combined_graph.read(), filename="statistics.png"),
                        caption=f"📊 Статистика тренировок {caption_suffix}"
                    )
                    logger.info("Объединённый график отправлен")
                else:
                    logger.warning("Не удалось создать графики")
                    await callback.message.answer("⚠️ Недостаточно данных для создания графиков")
            except Exception as e:
                logger.error(f"Ошибка при отправке графика: {str(e)}", exc_info=True)
                await callback.message.answer(f"❌ Ошибка при создании графиков: {str(e)}")
        
        await callback.message.answer(
            "📋 *Выберите тренировку для просмотра деталей:*\n\n"
            "Нажмите на номер тренировки или выберите другой период",
            parse_mode="Markdown",
            reply_markup=get_trainings_list_keyboard(trainings, period, date_format)
        )
    else:
        await callback.message.answer(f"❌ Тренировка не найдена или не ваша.")
    await callback.message.delete()  
    await callback.answer()

@router.callback_query(F.data == "cancel_delete")
async def cancel_delete(callback: CallbackQuery):
    """Отмена удаления тренировки"""
    await callback.message.answer("❌ Удаление отменено.")
    await callback.message.delete()
    await callback.answer()

@router.callback_query(F.data.startswith("training_detail:"))
async def show_training_detail(callback: CallbackQuery):
    """Показать детальную информацию о конкретной тренировке"""
    parts = callback.data.split(":")
    training_id = int(parts[1])
    period = parts[2]

    from coach.coach_training_queries import get_training_with_comments
    training = await get_training_with_comments(training_id)

    if not training or training['user_id'] != callback.from_user.id:
        await callback.answer("❌ Тренировка не найдена", show_alert=True)
        return
    
    user_settings = await get_user_settings(callback.from_user.id)
    distance_unit = user_settings.get('distance_unit', 'км') if user_settings else 'км'
    date_format = user_settings.get('date_format', 'DD.MM.YYYY') if user_settings else 'DD.MM.YYYY'
    
    from datetime import datetime
    
    type_emoji = {
        'кросс': '🏃',
        'плавание': '🏊',
        'велотренировка': '🚴',
        'силовая': '💪',
        'интервальная': '⚡'
    }
    
    t_type = training['type']
    emoji = type_emoji.get(t_type, '📝')
    date = DateFormatter.format_date(training['date'], date_format)
    
    detail_text = (
        f"{emoji} *Детальная информация о тренировке*\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"📅 *Дата:* {date}\n"
        f"🏋️ *Тип:* {t_type.capitalize()}\n"
    )
    
    if training.get('time'):
        detail_text += f"⏱ *Время:* {training['time']}\n"
    
    if t_type == 'интервальная':
        if training.get('calculated_volume'):
            detail_text += f"📏 *Объем:* {format_distance(training['calculated_volume'], distance_unit)}\n"
        
        if training.get('intervals'):
            from utils.interval_calculator import calculate_average_interval_pace
            avg_pace_intervals = calculate_average_interval_pace(training['intervals'])
            if avg_pace_intervals:
                detail_text += f"⚡ *Средний темп отрезков:* {avg_pace_intervals}\n"
            
            detail_text += f"\n📋 *Описание тренировки:*\n```\n{training['intervals']}\n```\n"
    
    elif t_type == 'силовая':
        if training.get('exercises'):
            detail_text += f"\n💪 *Упражнения:*\n```\n{training['exercises']}\n```\n"
    
    else:
        if training.get('distance'):
            if t_type == 'плавание':
                detail_text += f"📏 *Дистанция:* {format_swimming_distance(training['distance'], distance_unit)}\n"
            else:
                detail_text += f"📏 *Дистанция:* {format_distance(training['distance'], distance_unit)}\n"

        if t_type == 'плавание':
            if training.get('swimming_location'):
                from utils.swimming_pace import format_swimming_location
                location_text = format_swimming_location(
                    training['swimming_location'],
                    training.get('pool_length')
                )
                detail_text += f"📍 *Место:* {location_text}\n"

            if training.get('swimming_styles'):
                import json
                try:
                    styles = json.loads(training['swimming_styles'])
                    from utils.swimming_pace import format_swimming_styles
                    styles_text = format_swimming_styles(styles)
                    detail_text += f"🏊 *Стили:* {styles_text}\n"
                except:
                    pass

            if training.get('swimming_sets'):
                detail_text += f"\n📝 *Отрезки:*\n```\n{training['swimming_sets']}\n```\n"

        if training.get('avg_pace'):
            pace_unit = training.get('pace_unit', '')
            if t_type == 'велотренировка':
                detail_text += f"🚴 *Средняя скорость:* {training['avg_pace']} {pace_unit}\n"
            else:
                detail_text += f"⚡ *Средний темп:* {training['avg_pace']} {pace_unit}\n"
    
    if training.get('avg_pulse'):
        detail_text += f"❤️ *Средний пульс:* {training['avg_pulse']} уд/мин\n"
    
    if training.get('max_pulse'):
        detail_text += f"💗 *Максимальный пульс:* {training['max_pulse']} уд/мин\n"
    
    if training.get('comment'):
        detail_text += f"\n💬 *Мой комментарий:*\n_{training['comment']}_\n"

    comments = training.get('comments', [])
    if comments:
        detail_text += f"\n💬 *Комментарий тренера:*\n"
        for comment in comments:
            author_name = comment.get('author_name') or comment.get('author_username')
            detail_text += f"_{author_name}:_ {comment['comment']}\n"

    if training.get('fatigue_level'):
        detail_text += f"\n💪 *Уровень усилий:* {training['fatigue_level']}/10\n"
    
    detail_text += "\n━━━━━━━━━━━━━━━━━"
    
    try:
        await callback.message.edit_text(
            detail_text,
            parse_mode="Markdown",
            reply_markup=get_training_detail_keyboard(period, training_id=training_id)  
        )
    except Exception as e:
        await callback.message.answer(
            detail_text,
            parse_mode="Markdown",
            reply_markup=get_training_detail_keyboard(period, training_id=training_id)  
        )
    
    await callback.answer()

@router.callback_query(F.data == "back_to_periods")
async def back_to_periods(callback: CallbackQuery):
    """Вернуться к выбору периодов"""
    await callback.message.edit_text(
        "📊 *Мои тренировки*\n\n"
        "Выберите период для просмотра:",
        parse_mode="Markdown",
        reply_markup=get_period_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("back_to_list:"))
async def back_to_list(callback: CallbackQuery):
    """Вернуться к списку тренировок"""
    period = callback.data.split(":")[1]

    user_settings = await get_user_settings(callback.from_user.id)
    date_format = user_settings.get('date_format', 'DD.MM.YYYY') if user_settings else 'DD.MM.YYYY'

    trainings = await get_trainings_by_period(callback.from_user.id, period)

    if not trainings:
        await callback.answer("❌ Тренировки не найдены", show_alert=True)
        return

    try:
        await callback.message.edit_text(
            "📋 *Выберите тренировку для просмотра деталей:*\n\n"
            "Нажмите на номер тренировки или выберите другой период",
            parse_mode="Markdown",
            reply_markup=get_trainings_list_keyboard(trainings, period, date_format)
        )
    except Exception as e:
        logger.error(f"Ошибка при возврате к списку: {str(e)}")
        await callback.answer("❌ Ошибка при возврате к списку", show_alert=True)
        return
    
    await callback.answer()

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """Вернуться в главное меню"""
    from coach.coach_queries import is_user_coach

    user_id = callback.from_user.id
    is_coach_status = await is_user_coach(user_id)

    await callback.message.delete()
    await callback.message.answer(
        "Вы в главном меню",
        reply_markup=get_main_menu_keyboard(is_coach_status)
    )
    await callback.answer()

@router.message(F.text == "📊 Статистика")
async def show_stats(message: Message):
    """Показать статистику (заглушка)"""
    await message.answer(
        "📊 Статистика будет доступна позже!\n\n"
        "Здесь вы сможете увидеть:\n"
        "• Общее количество тренировок\n"
        "• Суммарную дистанцию\n"
        "• Среднюю продолжительность\n"
        "• И многое другое!"
    )

@router.message(F.text == "📈 Графики")
async def show_graphs(message: Message):
    """Показать графики (заглушка)"""
    await message.answer("📈 Графики будут доступна позже!")


@router.message(F.text == "ℹ️ Помощь")
async def show_help(message: Message):
    """Показать помощь"""
    from help.help_keyboards import get_help_main_menu
    from help.help_texts import HELP_MAIN

    await message.answer(
        HELP_MAIN,
        reply_markup=get_help_main_menu(),
        parse_mode="HTML"
    )

@router.message(F.text == "🤖 Training Assistant")
async def show_training_assistant(message: Message):
    """Показать меню Training Assistant"""
    from training_assistant.ta_keyboards import get_main_menu_keyboard as get_ta_menu

    await message.answer(
        "🤖 <b>Training Assistant - Ваш AI тренер</b>\n\n"
        "Выберите, чем я могу помочь:",
        reply_markup=get_ta_menu(),
        parse_mode="HTML"
    )

@router.message(F.text == "🏃 Соревнования")
async def show_competitions(message: Message):
    """Показать меню соревнований"""
    text = (
        "🏆 <b>СОРЕВНОВАНИЯ</b>\n\n"
        "Здесь вы можете:\n"
        "• Найти предстоящие марафоны и забеги\n"
        "• Зарегистрироваться на соревнование\n"
        "• Отслеживать свою подготовку\n"
        "• Добавлять результаты\n"
        "• Вести историю участия\n\n"
        "Выберите раздел:"
    )

    from competitions.competitions_keyboards import get_competitions_main_menu

    await message.answer(
        text,
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )
    await message.answer(
        "Выберите действие:",
        reply_markup=get_competitions_main_menu(),
        parse_mode="HTML"
    )


@router.message(F.text == "📥 Экспорт в PDF")
async def export_pdf_menu(message: Message):
    """Показать меню выбора типа экспорта в PDF"""
    await message.answer(
        "📥 <b>Экспорт в PDF</b>\n\n"
        "Выберите, что вы хотите экспортировать:",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )
    await message.answer(
        "Выберите тип экспорта:",
        reply_markup=get_export_type_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("export_type:"))
async def process_export_type(callback: CallbackQuery):
    """Обработка выбора типа экспорта"""
    export_type = callback.data.split(":")[1]

    if export_type == "trainings":
        await callback.message.edit_text(
            "📊 <b>Экспорт тренировок в PDF</b>\n\n"
            "Выберите период для экспорта:",
            parse_mode="HTML",
            reply_markup=get_export_period_keyboard()
        )
    elif export_type == "health":
        from health.health_keyboards import get_export_period_keyboard as get_health_export_period_keyboard
        await callback.message.edit_text(
            "❤️ <b>Экспорт данных здоровья в PDF</b>\n\n"
            "Выберите период для экспорта:",
            parse_mode="HTML",
            reply_markup=get_health_export_period_keyboard()
        )
    elif export_type == "competitions":
        from competitions.competitions_keyboards import get_export_period_menu
        await callback.message.edit_text(
            "🏃 <b>Экспорт соревнований в PDF</b>\n\n"
            "Выберите период для экспорта:",
            parse_mode="HTML",
            reply_markup=get_export_period_menu()
        )

    await callback.answer()


@router.callback_query(F.data == "back_to_export_menu")
async def back_to_export_menu(callback: CallbackQuery):
    """Возврат в меню выбора типа экспорта"""
    await callback.message.edit_text(
        "📥 <b>Экспорт в PDF</b>\n\n"
        "Выберите, что вы хотите экспортировать:",
        parse_mode="HTML",
        reply_markup=get_export_type_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("export_period:"))
async def process_export_period(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора периода экспорта"""
    period = callback.data.split(":")[1]
    
    from datetime import datetime, timedelta
    
    user_settings = await get_user_settings(callback.from_user.id)
    date_format = user_settings.get('date_format', 'DD.MM.YYYY') if user_settings else 'DD.MM.YYYY'
    
    today = datetime.now().date()
    
    if period == "6months":
        start_date = today - timedelta(days=180)
        end_date = today
        period_text = DateFormatter.format_date_range(start_date, end_date, date_format)

        await callback.answer("⏳ Генерирую PDF...", show_alert=True)

        await generate_and_send_pdf(
            callback.message,
            callback.from_user.id,
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d'),
            period_text
        )
        
    elif period == "year":
        start_date = today - timedelta(days=365)
        end_date = today
        period_text = DateFormatter.format_date_range(start_date, end_date, date_format)

        await callback.answer("⏳ Генерирую PDF...", show_alert=True)

        await generate_and_send_pdf(
            callback.message,
            callback.from_user.id,
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d'),
            period_text
        )
        
    elif period == "custom":
        user_settings = await get_user_settings(callback.from_user.id)
        date_format = user_settings.get('date_format', 'DD.MM.YYYY') if user_settings else 'DD.MM.YYYY'
        format_desc = DateFormatter.get_format_description(date_format)

        calendar = CalendarKeyboard.create_calendar(
            calendar_format=1,
            current_date=datetime.now(),
            callback_prefix="cal",
            max_date=datetime.now(),
            show_cancel=True,
            cancel_callback="trainings:export:cancel"
        )
        await callback.message.edit_text(
            f"📅 <b>Произвольный период</b>\n\n"
            f"Выберите начальную дату из календаря или введите вручную в формате {format_desc}",
            reply_markup=calendar,
            parse_mode="HTML"
        )

        await state.set_state(ExportPDFStates.waiting_for_start_date)
    
    await callback.answer()

@router.message(ExportPDFStates.waiting_for_start_date)
async def process_export_start_date(message: Message, state: FSMContext):
    """Обработка начальной даты для произвольного периода"""
    if not message.text:
        await message.answer(
            "❌ Пожалуйста, отправьте текстовое сообщение с датой",
            reply_markup=get_cancel_keyboard()
        )
        return

    user_settings = await get_user_settings(message.from_user.id)
    date_format = user_settings.get('date_format', 'DD.MM.YYYY') if user_settings else 'DD.MM.YYYY'

    date_pattern = DateFormatter.get_validation_pattern(date_format)
    match = re.match(date_pattern, message.text.strip())
    
    if not match:
        format_desc = DateFormatter.get_format_description(date_format)
        await message.answer(
            f"❌ Неверный формат даты!\n\n"
            f"Пожалуйста, введите дату в формате {format_desc}"
        )
        return
    
    start_date = DateFormatter.parse_date(message.text.strip(), date_format)
    
    if start_date is None:
        await message.answer(
            "❌ Некорректная дата!\n\n"
            f"Пожалуйста, введите существующую дату"
        )
        return
    
    if start_date > datetime.now().date():
        await message.answer(
            "❌ Дата не может быть из будущего!\n\n"
            "Пожалуйста, введите корректную дату:"
        )
        return
    
    await state.update_data(start_date=start_date.strftime('%Y-%m-%d'))

    format_desc = DateFormatter.get_format_description(date_format)
    start_date_str = DateFormatter.format_date(start_date, date_format)

    calendar = CalendarKeyboard.create_calendar(
        calendar_format=1,
        current_date=datetime.now(),
        callback_prefix="cal_end",
        max_date=datetime.now(),
        show_cancel=True,
        cancel_callback="trainings:export:cancel"
    )

    await message.answer(
        f"✅ Начальная дата: {start_date_str}\n\n"
        f"📅 Теперь выберите конечную дату из календаря или введите вручную в формате {format_desc}",
        reply_markup=calendar,
        parse_mode="HTML"
    )
    await state.set_state(ExportPDFStates.waiting_for_end_date)

@router.message(ExportPDFStates.waiting_for_end_date)
async def process_export_end_date(message: Message, state: FSMContext):
    """Обработка конечной даты для произвольного периода"""
    if not message.text:
        await message.answer(
            "❌ Пожалуйста, отправьте текстовое сообщение с датой",
            reply_markup=get_cancel_keyboard()
        )
        return

    user_settings = await get_user_settings(message.from_user.id)
    date_format = user_settings.get('date_format', 'DD.MM.YYYY') if user_settings else 'DD.MM.YYYY'

    date_pattern = DateFormatter.get_validation_pattern(date_format)
    match = re.match(date_pattern, message.text.strip())
    
    if not match:
        format_desc = DateFormatter.get_format_description(date_format)
        await message.answer(
            f"❌ Неверный формат даты!\n\n"
            f"Пожалуйста, введите дату в формате {format_desc}"
        )
        return
    
    end_date = DateFormatter.parse_date(message.text.strip(), date_format)
    
    if end_date is None:
        await message.answer(
            "❌ Некорректная дата!\n\n"
            "Пожалуйста, введите существующую дату"
        )
        return
    
    if end_date > datetime.now().date():
        await message.answer(
            "❌ Дата не может быть из будущего!\n\n"
            "Пожалуйста, введите корректную дату:"
        )
        return
    
    data = await state.get_data()
    start_date_str = data['start_date']
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    
    if end_date < start_date:
        start_date_formatted = DateFormatter.format_date(start_date, date_format)
        await message.answer(
            f"❌ Конечная дата не может быть раньше начальной!\n\n"
            f"Начальная дата: {start_date_formatted}\n"
            f"Пожалуйста, введите конечную дату не раньше этой:"
        )
        return
    
    period_text = DateFormatter.format_date_range(start_date, end_date, date_format)

    await generate_and_send_pdf(
        message,
        message.from_user.id,
        start_date_str,
        end_date.strftime('%Y-%m-%d'),
        period_text
    )
        
    await state.clear()
        
    

async def generate_and_send_pdf(message: Message, user_id: int, start_date: str, end_date: str, period_text: str):
    """
    Генерирует и отправляет PDF с тренировками
    
    Args:
        message: Сообщение для ответа
        user_id: ID пользователя
        start_date: Начальная дата в формате 'YYYY-MM-DD'
        end_date: Конечная дата в формате 'YYYY-MM-DD'
        period_text: Текстовое описание периода для отображения
    """
    try:
        trainings = await get_trainings_by_custom_period(user_id, start_date, end_date)
        
        if not trainings:
            await message.answer(
                f"📭 За период {period_text} нет тренировок.\n\n"
                "Выберите другой период.",
                reply_markup=get_export_period_keyboard()
            )
            return
        
        stats = await get_statistics_by_custom_period(user_id, start_date, end_date)
        
        logger.info(f"Генерация PDF для пользователя {user_id}: {len(trainings)} тренировок")
        pdf_buffer = await create_training_pdf(trainings, period_text, stats, user_id)
        
        user_settings = await get_user_settings(user_id)
        distance_unit = user_settings.get('distance_unit', 'км') if user_settings else 'км'
        
        filename = f"trainings_{start_date}_{end_date}.pdf"
        
        total_distance = stats.get('total_distance', 0)
        distance_text = format_distance(total_distance, distance_unit) if total_distance else f"0 {distance_unit}"

        await message.answer_document(
            BufferedInputFile(pdf_buffer.read(), filename=filename),
            caption=f"📥 *Экспорт тренировок*\n\n"
                    f"Период: {period_text}\n"
                    f"Тренировок: {len(trainings)}\n"
                    f"Километраж: {distance_text}",
            parse_mode="Markdown"
        )
        
        logger.info(f"PDF успешно отправлен пользователю {user_id}")

        from coach.coach_queries import is_user_coach
        is_coach_status = await is_user_coach(user_id)

        await message.answer(
            "✅ PDF успешно создан!",
            reply_markup=get_main_menu_keyboard(is_coach_status)
        )

    except Exception as e:
        logger.error(f"Ошибка при генерации PDF: {str(e)}", exc_info=True)

        from coach.coach_queries import is_user_coach
        is_coach_status = await is_user_coach(user_id)

        await message.answer(
            f"❌ Ошибка при создании PDF:\n{str(e)}\n\n"
            "Попробуйте позже или выберите другой период.",
            reply_markup=get_main_menu_keyboard(is_coach_status)
        )



@router.callback_query(F.data.startswith("cal_end_1_select_"))
async def handle_calendar_end_date_selection(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора конечной даты из календаря"""
    logger.info(f"Обработчик cal_end_1_select_: {callback.data}")

    parsed = CalendarKeyboard.parse_callback_data(callback.data.replace("cal_end_", "cal_"))
    selected_date = parsed.get("date")

    if not selected_date:
        await callback.answer("❌ Ошибка при выборе даты", show_alert=True)
        return

    from datetime import timedelta
    utc_now = datetime.utcnow()
    moscow_now = utc_now + timedelta(hours=3)
    today = moscow_now.date()

    if selected_date.date() > today:
        await callback.answer("❌ Нельзя выбрать дату из будущего!", show_alert=True)
        return

    data = await state.get_data()
    start_date_str = data.get('start_date')

    if not start_date_str:
        await callback.answer("❌ Ошибка: начальная дата не найдена", show_alert=True)
        return

    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = selected_date.date()

    user_id = callback.from_user.id
    date_format = await get_user_date_format(user_id)

    if end_date < start_date:
        start_date_formatted = DateFormatter.format_date(start_date, date_format)
        await callback.answer(
            f"❌ Конечная дата не может быть раньше начальной ({start_date_formatted})!",
            show_alert=True
        )
        return

    period_text = DateFormatter.format_date_range(start_date, end_date, date_format)
    date_str = DateFormatter.format_date(end_date, date_format)

    await callback.answer("⏳ Генерирую PDF...", show_alert=True)

    await generate_and_send_pdf(
        callback.message,
        callback.from_user.id,
        start_date_str,
        end_date.strftime('%Y-%m-%d'),
        period_text
    )

    await state.clear()
    await callback.answer()


@router.callback_query(F.data.startswith("cal_end_"))
async def handle_calendar_end_date_navigation(callback: CallbackQuery, state: FSMContext):
    """Обработчик навигации по календарю для конечной даты"""
    logger.info(f"Обработчик cal_end_ навигация: {callback.data}")

    if callback.data.startswith("cal_end_1_select_"):
        return

    if callback.data == "cal_end_empty":
        await callback.answer()
        return

    callback_data_normalized = callback.data.replace("cal_end_", "cal_")
    new_keyboard = CalendarKeyboard.handle_navigation(callback_data_normalized, prefix="cal", max_date=datetime.now(), show_cancel=True, cancel_callback="trainings:export:cancel")

    if new_keyboard:
        final_keyboard = CalendarKeyboard.replace_prefix_in_keyboard(new_keyboard, "cal", "cal_end")

        try:
            await callback.message.edit_reply_markup(reply_markup=final_keyboard)
        except Exception as e:
            if "message is not modified" not in str(e).lower():
                logger.error(f"Ошибка при обновлении календаря: {str(e)}")

    await callback.answer()


@router.callback_query(F.data.startswith("cal_1_select_"))
async def handle_calendar_date_selection(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора даты из календаря"""
    parsed = CalendarKeyboard.parse_callback_data(callback.data)
    selected_date = parsed.get("date")

    if not selected_date:
        await callback.answer("❌ Ошибка при выборе даты", show_alert=True)
        return

    current_state = await state.get_state()

    from datetime import timedelta
    utc_now = datetime.utcnow()
    moscow_now = utc_now + timedelta(hours=3)
    today = moscow_now.date()

    if selected_date.date() > today:
        await callback.answer("❌ Нельзя выбрать дату из будущего!", show_alert=True)
        return

    user_id = callback.from_user.id
    date_format = await get_user_date_format(user_id)
    date_str = DateFormatter.format_date(selected_date.date(), date_format)

    if current_state == AddTrainingStates.waiting_for_date:
        await state.update_data(date=selected_date.date())

        try:
            await callback.message.delete()
        except Exception:
            pass  

        await callback.message.answer(
            f"✅ Дата: {date_str}\n\n"
            "⏰ Введите время тренировки\n\n"
            "Формат: ЧЧ:ММ:СС или ММ:СС (если меньше часа)\n"
            "Примеры:\n"
            "• 45:30 (45 минут 30 секунд)\n"
            "• 01:25:30 или 1:25:30 (1 час 25 минут)\n"
            "• 25:15:45 (для ультрамарафонов)",
            reply_markup=get_cancel_keyboard()
        )

        await state.set_state(AddTrainingStates.waiting_for_time)

    elif current_state == ExportPDFStates.waiting_for_start_date:
        await state.update_data(start_date=selected_date.date().strftime('%Y-%m-%d'))

        format_desc = DateFormatter.get_format_description(date_format)

        await callback.message.edit_text(
            f"✅ Начальная дата: {date_str}\n\n"
            f"Теперь выберите конечную дату"
        )

        calendar = CalendarKeyboard.create_calendar(
            calendar_format=1,
            current_date=selected_date,
            callback_prefix="cal_end",
            max_date=datetime.now(),
            show_cancel=True,
            cancel_callback="trainings:export:cancel"
        )
        await callback.message.answer(
            "📅 Выберите конечную дату или введите вручную в формате " + format_desc,
            reply_markup=calendar
        )

        await state.set_state(ExportPDFStates.waiting_for_end_date)

    elif current_state == ExportPDFStates.waiting_for_end_date:
        data = await state.get_data()
        start_date_str = data.get('start_date')

        if not start_date_str:
            await callback.answer("❌ Ошибка: начальная дата не найдена", show_alert=True)
            return

        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = selected_date.date()

        if end_date < start_date:
            start_date_formatted = DateFormatter.format_date(start_date, date_format)
            await callback.answer(
                f"❌ Конечная дата не может быть раньше начальной ({start_date_formatted})!",
                show_alert=True
            )
            return

        period_text = DateFormatter.format_date_range(start_date, end_date, date_format)

        await callback.answer("⏳ Генерирую PDF...", show_alert=True)

        await generate_and_send_pdf(
            callback.message,
            callback.from_user.id,
            start_date_str,
            end_date.strftime('%Y-%m-%d'),
            period_text
        )

        await state.clear()

    await callback.answer()


@router.callback_query(F.data.startswith("cal_"))
async def handle_calendar_navigation(callback: CallbackQuery, state: FSMContext):
    """Обработчик навигации по календарю"""
    if callback.data.startswith("cal_end_") or callback.data.startswith("cal_birth_"):
        return

    if callback.data.startswith("cal_1_select_"):
        return

    if callback.data == "cal_empty":
        await callback.answer()
        return

    new_keyboard = CalendarKeyboard.handle_navigation(callback.data, prefix="cal", max_date=datetime.now(), show_cancel=True, cancel_callback="trainings:export:cancel")

    if new_keyboard:
        try:
            await callback.message.edit_reply_markup(reply_markup=new_keyboard)
        except Exception as e:
            if "message is not modified" not in str(e).lower():
                logger.error(f"Ошибка при обновлении календаря: {str(e)}")
    else:
        logger.warning(f"Навигация календаря не сработала для callback: {callback.data}")

    await callback.answer()


@router.callback_query(F.data == "trainings:export:cancel")
async def cancel_trainings_export_inline(callback: CallbackQuery, state: FSMContext):
    """Отмена процесса экспорта тренировок (inline кнопка)"""
    await state.clear()
    from bot.keyboards import get_export_type_keyboard

    await callback.message.edit_text(
        "📥 <b>Экспорт в PDF</b>\n\n"
        "Выберите, что вы хотите экспортировать:",
        parse_mode="HTML",
        reply_markup=get_export_type_keyboard()
    )
    await callback.answer("Экспорт отменен")



@router.message(F.text == "👨‍🏫 Кабинет тренера")
async def show_coach_section(message: Message):
    """Показать кабинет тренера"""
    from coach.coach_queries import is_user_coach
    from coach.coach_keyboards import get_coach_main_menu

    user_id = message.from_user.id

    if not await is_user_coach(user_id):
        await message.answer(
            "У вас нет доступа к этому разделу.\n\n"
            "Чтобы стать тренером, включите режим тренера в ⚙️ Настройки"
        )
        return

    await message.answer(
        "👨‍🏫 <b>Кабинет тренера</b>\n\n"
        "Здесь вы можете управлять своими учениками, "
        "просматривать их тренировки и прогресс.",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )
    await message.answer(
        "Выберите действие:",
        reply_markup=get_coach_main_menu(),
        parse_mode="HTML"
    )