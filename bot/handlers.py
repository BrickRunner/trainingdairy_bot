"""
Обработчики команд и сообщений бота
"""

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from datetime import datetime
import re

from bot.fsm import AddTrainingStates
from bot.keyboards import (
    get_main_menu_keyboard,
    get_training_types_keyboard,
    get_cancel_keyboard,
    get_skip_keyboard,
    get_fatigue_keyboard,
    get_period_keyboard,
    get_date_keyboard
)
from database.queries import add_user, add_training, get_user

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    # Добавляем пользователя в БД, если его нет
    await add_user(user_id, username)
    
    welcome_text = (
        f"👋 Привет, {username}!\n\n"
        "Добро пожаловать в **Trainingdiary_bot** — твой личный дневник тренировок! 🏃‍♂️\n\n"
        "Что я умею:\n"
        "➕ Добавлять тренировки\n"
        "📊 Показывать статистику\n"
        "📈 Строить графики прогресса\n"
        "🏆 Отслеживать достижения\n\n"
        "Выбери действие из меню ниже 👇"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
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
        "📊 Статистика - Посмотреть свою статистику\n"
        "📈 Графики - Визуализация прогресса\n"
        "🏆 Достижения - Ваши достижения и награды\n\n"
        "Для добавления тренировки следуйте инструкциям бота. "
        "Вы всегда можете отменить действие, нажав кнопку ❌ Отменить"
    )
    
    await message.answer(help_text, parse_mode="Markdown")


@router.message(F.text == "➕ Добавить тренировку")
@router.message(Command("add_training"))
async def start_add_training(message: Message, state: FSMContext):
    """Начало процесса добавления тренировки"""
    await message.answer(
        "🏋️ **Добавление тренировки**\n\n"
        "Выберите тип тренировки:",
        reply_markup=get_training_types_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(AddTrainingStates.waiting_for_type)


@router.callback_query(F.data.startswith("training_type:"))
async def process_training_type(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора типа тренировки"""
    training_type = callback.data.split(":")[1]
    
    await state.update_data(training_type=training_type)
    
    await callback.message.edit_text(
        f"✅ Выбран тип: **{training_type.capitalize()}**",
        parse_mode="Markdown"
    )
    
    await callback.message.answer(
        "📅 Когда была тренировка?\n\n"
        "Выберите или введите дату:",
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
    
    # Текущая дата в UTC+3 (Москва)
    from datetime import timedelta
    utc_now = datetime.utcnow()
    moscow_now = utc_now + timedelta(hours=3)
    today = moscow_now.date()
    yesterday = today - timedelta(days=1)
    
    # Парсинг даты
    if message.text in ["сегодня", "📅 Сегодня"]:
        date = today
    elif message.text in ["вчера", "📅 Вчера"]:
        date = yesterday
    elif message.text == "📝 Ввести дату":
        # Запрашиваем ввод даты вручную
        await message.answer(
            "📅 Введите дату тренировки\n\n"
            "Формат: ДД.ММ.ГГГГ\n"
            "Например: 15.01.2024",
            reply_markup=get_cancel_keyboard()
        )
        return
    else:
        # Проверка формата ДД.ММ.ГГГГ
        date_pattern = r'^\d{2}\.\d{2}\.\d{4}$'
        if not re.match(date_pattern, message.text):
            await message.answer(
                "❌ Неверный формат даты!\n\n"
                "Используйте формат: ДД.ММ.ГГГГ (например, 15.01.2024)\n"
                "Или выберите кнопку на клавиатуре"
            )
            return
        
        try:
            date = datetime.strptime(message.text, "%d.%m.%Y").date()
        except ValueError:
            await message.answer(
                "❌ Некорректная дата!\n\n"
                "Проверьте правильность введенной даты"
            )
            return
    
    # Проверка, что дата не в будущем
    if date > today:
        await message.answer(
            f"❌ Нельзя добавить тренировку в будущем!\n\n"
            f"Сегодня: {today.strftime('%d.%m.%Y')}\n"
            f"Вы ввели: {date.strftime('%d.%m.%Y')}\n\n"
            "Введите дату не позже сегодняшней."
        )
        return
    
    await state.update_data(date=date)
    
    await message.answer(
        f"✅ Дата: {date.strftime('%d.%m.%Y')}\n\n"
        "⏰ Введите время тренировки\n\n"
        "Формат: ЧЧ:ММ:СС\n"
        "Примеры: 01:25:30 или 25:15:45 (для ультрамарафонов)",
        reply_markup=get_cancel_keyboard()
    )
    
    await state.set_state(AddTrainingStates.waiting_for_time)


@router.message(AddTrainingStates.waiting_for_time)
async def process_time(message: Message, state: FSMContext):
    """Обработка времени тренировки"""
    if message.text == "❌ Отменить":
        await cancel_handler(message, state)
        return
    
    # Гибкая проверка формата Ч:ММ:СС или ЧЧ:ММ:СС или ЧЧЧ:ММ:СС (для ультрамарафонов)
    time_pattern = r'^\d{1,3}:\d{1,2}:\d{1,2}$'
    if not re.match(time_pattern, message.text):
        await message.answer(
            "❌ Неверный формат времени!\n\n"
            "Используйте формат: ЧЧ:ММ:СС\n"
            "Примеры: 01:25:30 или 1:25:30 или 25:15:45"
        )
        return
    
    try:
        # Парсим время
        hours, minutes, seconds = map(int, message.text.split(':'))
        
        # Проверяем корректность минут и секунд
        if minutes > 59 or seconds > 59:
            await message.answer(
                "❌ Некорректное время!\n\n"
                "Убедитесь, что минуты ≤ 59, секунды ≤ 59"
            )
            return
        
        # Проверка на нулевое время
        if hours == 0 and minutes == 0 and seconds == 0:
            await message.answer(
                "❌ Время тренировки не может быть 00:00:00!\n\n"
                "Минимальное время: 00:00:01\n"
                "Введите корректное время тренировки."
            )
            return
        
        # Форматируем в красивый вид с ведущими нулями
        formatted_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        # Переводим в минуты для совместимости с БД
        total_minutes = hours * 60 + minutes + (1 if seconds > 0 else 0)
        
    except ValueError:
        await message.answer(
            "❌ Некорректное время!\n\n"
            "Проверьте правильность введенного времени"
        )
        return
    
    await state.update_data(time=formatted_time, duration=total_minutes)
    
    # Получаем тип тренировки для выбора следующего шага
    data = await state.get_data()
    training_type = data.get('training_type', 'кросс')
    
    if training_type == 'силовая':
        # Для силовой тренировки переходим к описанию упражнений
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
        # Для интервальной тренировки переходим к описанию
        await message.answer(
            f"✅ Время: {formatted_time}\n\n"
            "⚡ Опишите тренировку\n\n"
            "Например:\n"
            "1. Разминка - 3000м\n"
            "2. ОРУ + СБУ + 2 ускорения по ~80м\n"
            "    Работа:\n"
            "3. 6 х 1000м / 200м - ()\n"
            "4. Трусца - 600м\n"
            "5. 3 х 60м / 60м - ()\n"
            "6. Трусца - 600м\n"
            "7. СБУ по 40м:\n"
            "Высокие подскоки\n"
            "Буратино\n"
            "2 х Буратино + высокое бедро\n"
            "Прыжки\n"
            "Прыжки + прыжки вбок\n"
            "2 х прыжки + кандибобер\n"
            "Кандибобер\n"
            "2 х многоскоки на одну ногу\n"
            "Многоскоки\n"
            "8. Заминка - 1000м"
        )
        await state.set_state(AddTrainingStates.waiting_for_intervals)
    else:
        # Для остальных типов переходим к дистанции
        await message.answer(
            f"✅ Время: {formatted_time}\n\n"
            "🏃 Введите дистанцию в километрах\n\n"
            "Например: 10 или 10.5"
        )
        await state.set_state(AddTrainingStates.waiting_for_distance)


@router.message(AddTrainingStates.waiting_for_distance)
async def process_distance(message: Message, state: FSMContext):
    """Обработка дистанции"""
    if message.text == "❌ Отменить":
        await cancel_handler(message, state)
        return
    
    try:
        distance = float(message.text.replace(',', '.'))
        if distance <= 0:
            raise ValueError
    except ValueError:
        await message.answer(
            "❌ Неверный формат!\n\n"
            "Введите положительное число (километры)\n"
            "Например: 10 или 10.5"
        )
        return
    
    await state.update_data(distance=distance)
    
    # Получаем тип тренировки для адаптивного сообщения
    data = await state.get_data()
    training_type = data.get('training_type', 'кросс')
    
    # Адаптивное сообщение в зависимости от типа
    if training_type == 'плавание':
        distance_text = f"✅ Дистанция: {distance} км ({distance * 1000} м)"
    else:
        distance_text = f"✅ Дистанция: {distance} км"
    
    await message.answer(
        f"{distance_text}\n\n"
        "❤️ Введите средний пульс (уд/мин)\n\n"
        "Например: 145"
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
        if avg_pulse <= 0 or avg_pulse > 250:
            raise ValueError
    except ValueError:
        await message.answer(
            "❌ Неверный формат!\n\n"
            "Введите корректное значение пульса (30-250 уд/мин)\n"
            "Например: 145"
        )
        return
    
    await state.update_data(avg_pulse=avg_pulse)
    
    await message.answer(
        f"✅ Средний пульс: {avg_pulse} уд/мин\n\n"
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
        "Например: 130"
    )
    
    await state.set_state(AddTrainingStates.waiting_for_avg_pulse)


@router.message(AddTrainingStates.waiting_for_intervals)
async def process_intervals(message: Message, state: FSMContext):
    """Обработка описания интервалов для интервальной тренировки"""
    if message.text == "❌ Отменить":
        await cancel_handler(message, state)
        return
    
    # Описание обязательно - не разрешаем пропустить
    intervals = message.text
    
    # Рассчитываем объём тренировки
    from utils.interval_calculator import calculate_interval_volume, format_volume_message
    volume = calculate_interval_volume(intervals)
    
    # Сохраняем описание и объём
    await state.update_data(intervals=intervals, calculated_volume=volume)
    
    # Показываем рассчитанный объём
    if volume:
        volume_msg = f"\n\n{format_volume_message(volume)}"
        await message.answer(
            f"✅ Описание сохранено{volume_msg}\n\n"
            "❤️ Введите средний пульс (уд/мин)\n\n"
            "Например: 165"
        )
    else:
        await message.answer(
            "✅ Описание сохранено\n\n"
            "⚠️ Не удалось рассчитать объём автоматически\n"
            "(Возможно, не все пункты пронумерованы)\n\n"
            "❤️ Введите средний пульс (уд/мин)\n\n"
            "Например: 165"
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
        if max_pulse <= 0 or max_pulse > 250:
            raise ValueError
    except ValueError:
        await message.answer(
            "❌ Неверный формат!\n\n"
            "Введите корректное значение пульса (30-250 уд/мин)\n"
            "Например: 175"
        )
        return
    
    # Проверяем, что максимальный пульс не меньше среднего
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
    
    await message.answer(
        f"✅ Максимальный пульс: {max_pulse} уд/мин\n\n"
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
        "😴 Оцените уровень усталости после тренировки\n\n"
        "Выберите от 1 (совсем не устал) до 10 (очень устал):",
        reply_markup=ReplyKeyboardRemove()
    )
    
    # Отправляем inline-клавиатуру отдельным сообщением
    await message.answer(
        "Выберите уровень усталости:",
        reply_markup=get_fatigue_keyboard()
    )
    
    await state.set_state(AddTrainingStates.waiting_for_fatigue)


@router.callback_query(F.data.startswith("fatigue:"))
async def process_fatigue(callback: CallbackQuery, state: FSMContext):
    """Обработка уровня усталости и сохранение тренировки"""
    fatigue_level = int(callback.data.split(":")[1])
    
    # Получаем все данные из состояния
    data = await state.get_data()
    data['fatigue_level'] = fatigue_level
    data['user_id'] = callback.from_user.id
    
    # Рассчитываем средний темп
    time_str = data['time']
    hours, minutes, seconds = map(int, time_str.split(':'))
    total_seconds = hours * 3600 + minutes * 60 + seconds
    total_minutes = total_seconds / 60
    training_type = data['training_type']
    
    # Расчет темпа только для тренировок с дистанцией
    if training_type not in ['силовая', 'интервальная']:
        distance = data['distance']
        
        # Расчет темпа в зависимости от типа тренировки
        if training_type == 'плавание':
            # Для плавания: мин:сек на 100 метров
            distance_in_meters = distance * 1000
            seconds_per_100m = (total_seconds / distance_in_meters) * 100
            pace_minutes = int(seconds_per_100m // 60)
            pace_seconds = int(seconds_per_100m % 60)
            avg_pace = f"{pace_minutes}:{pace_seconds:02d}"
            pace_unit = "мин/100м"
        elif training_type == 'велотренировка':
            # Для велотренировки: средняя скорость в км/ч
            hours_total = total_seconds / 3600
            avg_speed = distance / hours_total
            avg_pace = f"{avg_speed:.1f}"
            pace_unit = "км/ч"
        else:
            # Для кросса: мин:сек на километр
            avg_pace_minutes = total_minutes / distance
            pace_minutes = int(avg_pace_minutes)
            pace_seconds = int((avg_pace_minutes - pace_minutes) * 60)
            avg_pace = f"{pace_minutes}:{pace_seconds:02d}"
            pace_unit = "мин/км"
        
        # Сохраняем темп в данные
        data['avg_pace'] = avg_pace
        data['pace_unit'] = pace_unit
    
    # Для интервальной тренировки - calculated_volume уже должен быть в data
    # (добавляется при обработке описания интервалов)
    
    # Сохраняем тренировку в БД
    await add_training(data)
    
    # Формируем итоговое сообщение
    training_type = data['training_type']
    
    # Определяем эмодзи в зависимости от типа
    if training_type == 'плавание':
        training_emoji = "🏊"
    elif training_type == 'велотренировка':
        training_emoji = "🚴"
    elif training_type == 'силовая':
        training_emoji = "💪"
    elif training_type == 'интервальная':
        training_emoji = "⚡"
    else:  # кросс
        training_emoji = "🏃"
    
    # Базовая информация для всех типов
    summary = (
        "✅ **Тренировка успешно добавлена!**\n\n"
        f"📅 Дата: {data['date'].strftime('%d.%m.%Y')}\n"
        f"{training_emoji} Тип: {training_type.capitalize()}\n"
        f"⏰ Время: {data['time']}\n"
    )
    
    # Специфичная информация в зависимости от типа
    if training_type == 'силовая':
        # Для силовой - упражнения вместо дистанции и темпа
        if data.get('exercises'):
            summary += f"💪 Упражнения:\n{data['exercises']}\n"
    elif training_type == 'интервальная':
        # Для интервальной - описание тренировки
        if data.get('intervals'):
            summary += f"⚡ Описание:\n{data['intervals']}\n"
            
            # Показываем рассчитанный объём если есть
            if data.get('calculated_volume'):
                from utils.interval_calculator import format_volume_message
                volume_text = format_volume_message(data['calculated_volume'])
                if volume_text:
                    summary += f"{volume_text}\n"
            
            # Показываем средний темп отрезков если есть результаты
            from utils.interval_calculator import calculate_average_interval_pace
            avg_pace_intervals = calculate_average_interval_pace(data['intervals'])
            if avg_pace_intervals:
                summary += f"⚡ Средний темп отрезков: {avg_pace_intervals}\n"
    else:
        # Для остальных типов - дистанция и темп
        distance_km = data['distance']
        
        if training_type == 'плавание':
            distance_text = f"📏 Дистанция: {distance_km} км ({int(distance_km * 1000)} м)"
        else:
            distance_text = f"📏 Дистанция: {distance_km} км"
        
        pace_emoji = "⚡"
        if training_type == 'велотренировка':
            pace_label = "Средняя скорость"
        else:
            pace_label = "Средний темп"
        
        summary += (
            f"{distance_text}\n"
            f"{pace_emoji} {pace_label}: {avg_pace} {pace_unit}\n"
        )
    
    # Пульс для всех типов тренировок
    if data.get('avg_pulse') and data.get('max_pulse'):
        summary += f"❤️ Средний пульс: {data['avg_pulse']} уд/мин\n"
        summary += f"💓 Максимальный пульс: {data['max_pulse']} уд/мин\n"
    
    # Комментарий если есть
    if data.get('comment'):
        summary += f"💬 Комментарий: {data['comment']}\n"
    
    summary += f"😴 Усталость: {fatigue_level}/10"
    
    await callback.message.edit_text(summary, parse_mode="Markdown")
    await callback.message.answer(
        "Что делаем дальше?",
        reply_markup=get_main_menu_keyboard()
    )
    
    # Очищаем состояние
    await state.clear()
    await callback.answer("Тренировка сохранена! ✅")


@router.message(F.text == "❌ Отменить")
@router.callback_query(F.data == "cancel")
async def cancel_handler(message: Message | CallbackQuery, state: FSMContext):
    """Отмена текущей операции"""
    current_state = await state.get_state()
    
    if current_state is None:
        if isinstance(message, Message):
            await message.answer(
                "Нечего отменять 🤷‍♂️",
                reply_markup=get_main_menu_keyboard()
            )
        return
    
    await state.clear()
    
    if isinstance(message, CallbackQuery):
        await message.message.edit_text("❌ Действие отменено")
        await message.message.answer(
            "Вы в главном меню",
            reply_markup=get_main_menu_keyboard()
        )
        await message.answer()
    else:
        await message.answer(
            "❌ Действие отменено\n\nВы в главном меню",
            reply_markup=get_main_menu_keyboard()
        )


@router.message(F.text == "📊 Мои тренировки")
async def show_my_trainings(message: Message):
    """Показать меню выбора периода для просмотра тренировок"""
    await message.answer(
        "📊 *Мои тренировки*\n\n"
        "Выберите период для просмотра:",
        parse_mode="Markdown",
        reply_markup=get_period_keyboard()
    )


@router.callback_query(F.data.startswith("period:"))
async def show_trainings_period(callback: CallbackQuery):
    """Показать тренировки за выбранный период с детальной статистикой"""
    period = callback.data.split(":")[1]
    
    # Определяем количество дней
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
    period_name = period_names.get(period, "неделю")
    
    # Получаем статистику и тренировки
    from database.queries import get_trainings_by_period, get_training_statistics
    
    stats = await get_training_statistics(callback.from_user.id, days)
    trainings = await get_trainings_by_period(callback.from_user.id, days)
    
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
    
    # Формируем заголовок с общей статистикой
    message_text = f"📊 *Тренировки за {period_name}*\n\n"
    message_text += "━━━━━━━━━━━━━━━━━━\n"
    message_text += "📈 *ОБЩАЯ СТАТИСТИКА*\n"
    message_text += "━━━━━━━━━━━━━━━━━━\n\n"
    
    # 1. Общее количество тренировок
    message_text += f"🏃 Всего тренировок: *{stats['total_count']}*\n"
    
    # 2. Общий километраж
    if stats['total_distance'] > 0:
        message_text += f"📏 Общий километраж: *{stats['total_distance']:.2f} км*\n"
    
    # 3. Типы тренировок с процентами
    if stats['types_count']:
        message_text += f"\n📋 *Типы тренировок:*\n"
        
        type_emoji = {
            'кросс': '🏃',
            'плавание': '🏊',
            'велотренировка': '🚴',
            'силовая': '💪',
            'интервальная': '⚡'
        }
        
        # Сортируем по количеству (от большего к меньшему)
        sorted_types = sorted(stats['types_count'].items(), key=lambda x: x[1], reverse=True)
        
        for t_type, count in sorted_types:
            emoji = type_emoji.get(t_type, '📝')
            percentage = (count / stats['total_count']) * 100
            message_text += f"  {emoji} {t_type.capitalize()}: {count} ({percentage:.1f}%)\n"
    
    # 4. Средний уровень усталости
    if stats['avg_fatigue'] > 0:
        message_text += f"\n😴 Средняя усталость: *{stats['avg_fatigue']}/10*\n"
    
    message_text += "\n━━━━━━━━━━━━━━━━━━\n"
    message_text += "📝 *СПИСОК ТРЕНИРОВОК*\n"
    message_text += "━━━━━━━━━━━━━━━━━━\n\n"
    
    # Эмодзи для типов
    type_emoji = {
        'кросс': '🏃',
        'плавание': '🏊',
        'велотренировка': '🚴',
        'силовая': '💪',
        'интервальная': '⚡'
    }
    
    # Добавляем детали каждой тренировки
    for idx, training in enumerate(trainings[:15], 1):  # Показываем максимум 15
        # Парсим дату
        date = datetime.strptime(training['date'], '%Y-%m-%d').strftime('%d.%m.%Y')
        t_type = training['type']
        emoji = type_emoji.get(t_type, '📝')
        
        # 1. Дата и тип
        message_text += f"*{idx}.* {emoji} *{t_type.capitalize()}* • {date}\n"
        
        # 2. Продолжительность в формате ЧЧ:ММ:СС
        if training.get('time'):
            message_text += f"   ⏰ Время: {training['time']}\n"
        
        # 3. Общий километраж
        if t_type == 'интервальная':
            if training.get('calculated_volume'):
                message_text += f"   📏 Дистанция: {training['calculated_volume']} км\n"
        else:
            if training.get('distance'):
                if t_type == 'плавание':
                    meters = int(training['distance'] * 1000)
                    message_text += f"   📏 Дистанция: {training['distance']} км ({meters} м)\n"
                else:
                    message_text += f"   📏 Дистанция: {training['distance']} км\n"
        
        # 4. Средний темп/скорость/интервалов
        if t_type == 'интервальная':
            # Показываем средний темп отрезков
            if training.get('intervals'):
                from utils.interval_calculator import calculate_average_interval_pace
                avg_pace_intervals = calculate_average_interval_pace(training['intervals'])
                if avg_pace_intervals:
                    message_text += f"   ⚡ Средний темп отрезков: {avg_pace_intervals}\n"
        elif t_type == 'велотренировка':
            # Для велосипеда - скорость
            if training.get('avg_pace'):
                message_text += f"   🚴 Средняя скорость: {training['avg_pace']} {training.get('pace_unit', '')}\n"
        elif t_type != 'силовая':
            # Для остальных (кросс, плавание) - темп
            if training.get('avg_pace'):
                message_text += f"   ⚡ Средний темп: {training['avg_pace']} {training.get('pace_unit', '')}\n"
        
        # Дополнительно: пульс
        if training.get('avg_pulse'):
            message_text += f"   ❤️ Пульс: {training['avg_pulse']} уд/мин\n"
        
        # Усталость
        if training.get('fatigue_level'):
            message_text += f"   😴 Усталость: {training['fatigue_level']}/10\n"
        
        message_text += "\n"
    
    if len(trainings) > 15:
        message_text += f"_... и ещё {len(trainings) - 15} тренировок_\n"
    
    try:
        await callback.message.edit_text(
            message_text,
            parse_mode="Markdown",
            reply_markup=get_period_keyboard()
        )
    except Exception as e:
        # Если сообщение не изменилось - просто отвечаем на callback
        if "message is not modified" in str(e):
            await callback.answer("Данные актуальны", show_alert=False)
        else:
            raise
    
    await callback.answer()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """Вернуться в главное меню"""
    await callback.message.delete()
    await callback.message.answer(
        "Вы в главном меню",
        reply_markup=get_main_menu_keyboard()
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
    await message.answer("📈 Графики будут доступны позже!")


@router.message(F.text == "🏆 Достижения")
async def show_achievements(message: Message):
    """Показать достижения (заглушка)"""
    await message.answer("🏆 Достижения будут доступны позже!")


@router.message(F.text == "⚙️ Настройки")
async def show_settings(message: Message):
    """Показать настройки (заглушка)"""
    await message.answer("⚙️ Настройки будут доступны позже!")


@router.message(F.text == "ℹ️ Помощь")
async def show_help(message: Message):
    """Показать помощь"""
    await cmd_help(message)
