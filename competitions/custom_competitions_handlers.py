"""
Обработчики для пользовательских соревнований
Функции:
- Создание своего соревнования
- Напоминания о соревнованиях
- Ввод результатов
- Предложения от тренера
"""

import logging
import json
from datetime import datetime, timedelta, date
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.fsm import CompetitionStates
from bot.calendar_keyboard import CalendarKeyboard
from competitions.competitions_queries import (
    add_competition,
    register_for_competition,
    get_competition,
    add_competition_result
)
from competitions.competitions_utils import (
    format_competition_distance,
    parse_user_distance_input,
    format_competition_date,
    parse_user_date_input,
    get_date_format_description,
    get_distance_unit_name,
    determine_competition_type
)
from utils.time_formatter import normalize_time, validate_time_format

logger = logging.getLogger(__name__)
router = Router()


# ========== ДОБАВЛЕНИЕ СОРЕВНОВАНИЯ ВРУЧНУЮ ==========

@router.callback_query(F.data == "comp:create_custom")
async def start_create_custom_competition(callback: CallbackQuery, state: FSMContext):
    """Начать добавление соревнования вручную"""

    text = (
        "🔍 <b>ДОБАВЛЕНИЕ СОРЕВНОВАНИЯ ВРУЧНУЮ</b>\n\n"
        "Вы можете добавить соревнование, в котором планируете участвовать.\n\n"
        "📝 <b>Шаг 1 из 6</b>\n\n"
        "Введите <b>название</b> соревнования:\n"
        "<i>Например: Московский марафон 2026</i>"
    )

    await callback.message.edit_text(text, parse_mode="HTML")
    await state.set_state(CompetitionStates.waiting_for_comp_name)
    await callback.answer()


@router.message(CompetitionStates.waiting_for_comp_name)
async def process_comp_name(message: Message, state: FSMContext):
    """Обработать название соревнования"""

    comp_name = message.text.strip()

    if not comp_name or len(comp_name) < 3:
        await message.answer(
            "❌ Название слишком короткое. Введите название минимум из 3 символов."
        )
        return

    # Сохраняем название
    await state.update_data(comp_name=comp_name)

    text = (
        f"✅ Название: <b>{comp_name}</b>\n\n"
        f"📝 <b>Шаг 2 из 6</b>\n\n"
        f"Введите <b>город</b>, где будет проходить соревнование:\n"
        f"<i>Например: Москва, Санкт-Петербург, Казань</i>"
    )

    await message.answer(text, parse_mode="HTML")
    await state.set_state(CompetitionStates.waiting_for_comp_city)


@router.message(CompetitionStates.waiting_for_comp_city)
async def process_comp_city(message: Message, state: FSMContext):
    """Обработать город соревнования"""

    comp_city = message.text.strip()

    if not comp_city or len(comp_city) < 2:
        await message.answer(
            "❌ Название города слишком короткое. Введите корректное название города."
        )
        return

    # Сохраняем город
    await state.update_data(comp_city=comp_city)

    # Показываем календарь для выбора даты
    calendar = CalendarKeyboard.create_calendar(
        calendar_format=1,
        current_date=datetime.now(),
        callback_prefix="cal_comp"
    )

    text = (
        f"✅ Город: <b>{comp_city}</b>\n\n"
        f"📝 <b>Шаг 3 из 6</b>\n\n"
        f"Выберите <b>дату</b> соревнования из календаря:"
    )

    await message.answer(text, parse_mode="HTML", reply_markup=calendar)
    await state.set_state(CompetitionStates.waiting_for_comp_date)


# Обработчики календаря для выбора даты соревнования
@router.callback_query(F.data.startswith("cal_comp_1_select_"), CompetitionStates.waiting_for_comp_date)
async def handle_comp_calendar_day_select(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора дня в календаре"""

    parsed = CalendarKeyboard.parse_callback_data(callback.data.replace("cal_comp_", "cal_"))
    selected_date = parsed.get("date")

    if not selected_date:
        await callback.answer("❌ Ошибка выбора даты", show_alert=True)
        return

    comp_date = selected_date.date()

    # Проверяем что дата в будущем
    if comp_date < date.today():
        await callback.answer("❌ Дата соревнования должна быть в будущем!", show_alert=True)
        return

    # Сохраняем дату
    await state.update_data(comp_date=comp_date.strftime('%Y-%m-%d'))

    user_id = callback.from_user.id
    formatted_date = await format_competition_date(comp_date.strftime('%Y-%m-%d'), user_id)

    # Создаём клавиатуру с типами
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏃 Бег", callback_data="comptype:running"))
    builder.row(InlineKeyboardButton(text="🏊 Плавание", callback_data="comptype:swimming"))
    builder.row(InlineKeyboardButton(text="🚴 Велоспорт", callback_data="comptype:cycling"))
    builder.row(InlineKeyboardButton(text="🏊‍♂️🚴‍♂️🏃 Триатлон", callback_data="comptype:triathlon"))
    builder.row(InlineKeyboardButton(text="⛰️ Трейл", callback_data="comptype:trail"))

    text = (
        f"✅ Дата: <b>{formatted_date}</b>\n\n"
        f"📝 <b>Шаг 4 из 6</b>\n\n"
        f"Выберите <b>вид спорта</b>:"
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await state.set_state(CompetitionStates.waiting_for_comp_type)
    await callback.answer()


@router.callback_query(F.data.startswith("cal_comp_"), CompetitionStates.waiting_for_comp_date)
async def handle_comp_calendar_navigation(callback: CallbackQuery, state: FSMContext):
    """Обработка навигации по календарю (переключение месяцев/годов)"""

    parsed = CalendarKeyboard.parse_callback_data(callback.data.replace("cal_comp_", "cal_"))

    # Получаем текущую дату из callback или используем текущую
    current_date = parsed.get("date")
    if not current_date:
        current_date = datetime.now()

    action = parsed.get("action", "")
    cal_format = parsed.get("format", 1)

    # Обрабатываем навигацию
    if action == "less":
        # Предыдущий период
        if cal_format == 1:  # Дни - переключаем месяц назад
            current_date = current_date.replace(day=1)
            if current_date.month == 1:
                current_date = current_date.replace(year=current_date.year - 1, month=12)
            else:
                current_date = current_date.replace(month=current_date.month - 1)
        elif cal_format == 2:  # Месяцы - переключаем год назад
            current_date = current_date.replace(year=current_date.year - 1)
    elif action == "more":
        # Следующий период
        if cal_format == 1:  # Дни - переключаем месяц вперед
            current_date = current_date.replace(day=1)
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        elif cal_format == 2:  # Месяцы - переключаем год вперед
            current_date = current_date.replace(year=current_date.year + 1)
    elif action == "change":
        # Переключаем формат календаря
        if cal_format == 1:
            cal_format = 2  # С дней на месяцы
        elif cal_format == 2:
            cal_format = 3  # С месяцев на годы

    # Создаем обновленный календарь
    calendar = CalendarKeyboard.create_calendar(
        calendar_format=cal_format,
        current_date=current_date,
        callback_prefix="cal_comp"
    )

    try:
        await callback.message.edit_reply_markup(reply_markup=calendar)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error updating calendar: {e}")
        await callback.answer()


@router.message(CompetitionStates.waiting_for_comp_date)
async def process_comp_date(message: Message, state: FSMContext):
    """Обработать дату соревнования (текстовый ввод как альтернатива календарю)"""

    date_text = message.text.strip()
    user_id = message.from_user.id

    # Парсим дату с учетом формата пользователя
    comp_date = await parse_user_date_input(date_text, user_id)

    if comp_date is None:
        date_format_desc = await get_date_format_description(user_id)
        await message.answer(
            f"❌ Неверный формат даты.\n"
            f"Используйте формат: {date_format_desc}\n"
            f"Или выберите дату из календаря выше."
        )
        return

    # Проверяем что дата в будущем
    if comp_date < date.today():
        await message.answer(
            "❌ Дата соревнования должна быть в будущем.\n"
            "Введите корректную дату или выберите из календаря:"
        )
        return

    # Сохраняем дату
    await state.update_data(comp_date=comp_date.strftime('%Y-%m-%d'))

    formatted_date = await format_competition_date(comp_date.strftime('%Y-%m-%d'), user_id)

    # Создаём клавиатуру с типами
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏃 Бег", callback_data="comptype:running"))
    builder.row(InlineKeyboardButton(text="🏊 Плавание", callback_data="comptype:swimming"))
    builder.row(InlineKeyboardButton(text="🚴 Велоспорт", callback_data="comptype:cycling"))
    builder.row(InlineKeyboardButton(text="🏊‍♂️🚴‍♂️🏃 Триатлон", callback_data="comptype:triathlon"))
    builder.row(InlineKeyboardButton(text="⛰️ Трейл", callback_data="comptype:trail"))

    text = (
        f"✅ Дата: <b>{formatted_date}</b>\n\n"
        f"📝 <b>Шаг 4 из 6</b>\n\n"
        f"Выберите <b>вид спорта</b>:"
    )

    await message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await state.set_state(CompetitionStates.waiting_for_comp_type)


@router.callback_query(F.data.startswith("comptype:"), CompetitionStates.waiting_for_comp_type)
async def process_comp_type(callback: CallbackQuery, state: FSMContext):
    """Обработать тип соревнования"""

    comp_type_map = {
        "running": "бег",
        "swimming": "плавание",
        "cycling": "велоспорт",
        "triathlon": "триатлон",
        "trail": "трейл"
    }

    comp_type_key = callback.data.split(":")[1]
    comp_type = comp_type_map.get(comp_type_key, "бег")

    # Сохраняем тип
    await state.update_data(comp_type=comp_type)

    user_id = callback.from_user.id
    distance_unit = await get_distance_unit_name(user_id)

    text = (
        f"✅ Вид спорта: <b>{comp_type}</b>\n\n"
        f"📝 <b>Шаг 5 из 6</b>\n\n"
        f"Введите <b>дистанцию</b> в <b>{distance_unit}</b>:\n"
    )

    if distance_unit == 'км':
        text += (
            f"<i>Например:\n"
            f"• 42.195 (для марафона)\n"
            f"• 21.1 (для полумарафона)\n"
            f"• 10 (для 10 км)</i>"
        )
    else:
        text += (
            f"<i>Например:\n"
            f"• 26.2 (для марафона)\n"
            f"• 13.1 (для полумарафона)\n"
            f"• 6.2 (для 10 км)</i>"
        )

    await callback.message.edit_text(text, parse_mode="HTML")
    await state.set_state(CompetitionStates.waiting_for_comp_distance)
    await callback.answer()


@router.message(CompetitionStates.waiting_for_comp_distance)
async def process_comp_distance(message: Message, state: FSMContext):
    """Обработать дистанцию соревнования"""

    distance_text = message.text.strip().replace(',', '.')
    user_id = message.from_user.id

    # Парсим дистанцию с учетом единиц пользователя
    distance_km = await parse_user_distance_input(distance_text, user_id)

    if distance_km is None:
        distance_unit = await get_distance_unit_name(user_id)
        await message.answer(
            f"❌ Неверный формат дистанции.\n"
            f"Введите число в {distance_unit} (например: 42.195 или 10):"
        )
        return

    if distance_km <= 0 or distance_km > 500:
        distance_unit = await get_distance_unit_name(user_id)
        await message.answer(
            f"❌ Дистанция должна быть от 0.1 до 500 км.\n"
            f"Введите корректное значение в {distance_unit}:"
        )
        return

    # Сохраняем дистанцию в км
    await state.update_data(comp_distance=distance_km)

    # Форматируем название дистанции
    distance_name = await format_competition_distance(distance_km, user_id)

    # Создаем клавиатуру с кнопкой "Пропустить"
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⏭️ Пропустить", callback_data="comp:skip_target"))

    text = (
        f"✅ Дистанция: <b>{distance_name}</b>\n\n"
        f"📝 <b>Шаг 6 из 6</b>\n\n"
        f"Введите <b>целевое время</b>:\n"
        f"<i>Формат: ЧЧ:ММ:СС или Ч:М:С\n"
        f"Например: 03:30:00 или 3:30:0 (3 часа 30 минут)\n"
        f"Или: 00:45:00 или 0:45:0 (45 минут)</i>\n\n"
        f"Или нажмите кнопку ниже, чтобы пропустить."
    )

    await message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await state.set_state(CompetitionStates.waiting_for_comp_target)


async def create_competition_from_state(user_id: int, state: FSMContext, target_time: str = None, message_obj=None):
    """Создать соревнование из сохраненных данных FSM"""
    # Получаем сохранённые данные
    data = await state.get_data()
    comp_name = data.get('comp_name')
    comp_city = data.get('comp_city')
    comp_date = data.get('comp_date')
    comp_type = data.get('comp_type')
    comp_distance = data.get('comp_distance')

    # Создаём соревнование в БД
    try:
        competition_data = {
            'name': comp_name,
            'date': comp_date,
            'city': comp_city,
            'country': 'Россия',
            'type': comp_type,
            'distances': json.dumps([comp_distance]),
            'status': 'upcoming',
            'created_by': user_id,
            'is_official': 0,  # Пользовательское соревнование
            'registration_status': 'open'
        }

        comp_id = await add_competition(competition_data)

        # Регистрируем пользователя на соревнование
        await register_for_competition(
            user_id=user_id,
            competition_id=comp_id,
            distance=comp_distance,
            target_time=target_time
        )

        logger.info(f"User {user_id} created custom competition {comp_id}: {comp_name}")

        # Создаём напоминания
        from competitions.reminder_scheduler import create_reminders_for_competition
        await create_reminders_for_competition(user_id, comp_id, comp_date)

        # Форматируем сообщение об успехе с учетом настроек пользователя
        formatted_date = await format_competition_date(comp_date, user_id)
        formatted_distance = await format_competition_distance(comp_distance, user_id)

        text = (
            "✅ <b>Соревнование создано!</b>\n\n"
            f"🏆 <b>{comp_name}</b>\n"
            f"🏙️ Город: {comp_city}\n"
            f"📅 Дата: {formatted_date}\n"
            f"🏃 Вид: {comp_type}\n"
            f"📏 Дистанция: {formatted_distance}\n"
        )

        if target_time:
            text += f"🎯 Цель: {target_time}\n"

        text += (
            "\n🔔 <b>Напоминания настроены</b>\n"
            "Вы будете получать напоминания:\n"
            "• За 30 дней до старта\n"
            "• За 14 дней до старта\n"
            "• За 7 дней до старта\n"
            "• За 3 дня до старта\n"
            "• За 1 день до старта\n"
            "• На следующий день после старта (для ввода результатов)\n\n"
            "Соревнование добавлено в раздел 'Мои соревнования'"
        )

        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="✅ Мои соревнования", callback_data="comp:my"))
        builder.row(InlineKeyboardButton(text="🔙 Главное меню", callback_data="comp:menu"))

        if message_obj:
            if isinstance(message_obj, Message):
                await message_obj.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())
            else:  # CallbackQuery
                await message_obj.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())

        # Очищаем состояние
        await state.clear()

    except Exception as e:
        logger.error(f"Error creating custom competition: {e}")
        error_text = "❌ Произошла ошибка при создании соревнования.\nПопробуйте ещё раз позже."

        if message_obj:
            if isinstance(message_obj, Message):
                await message_obj.answer(error_text, parse_mode="HTML")
            else:
                await message_obj.edit_text(error_text, parse_mode="HTML")

        await state.clear()


@router.callback_query(F.data == "comp:skip_target", CompetitionStates.waiting_for_comp_target)
async def skip_target_time(callback: CallbackQuery, state: FSMContext):
    """Пропустить целевое время и создать соревнование"""
    await create_competition_from_state(callback.from_user.id, state, None, callback.message)
    await callback.answer()


@router.message(CompetitionStates.waiting_for_comp_target)
async def process_comp_target_and_create(message: Message, state: FSMContext):
    """Обработать целевое время и создать соревнование"""

    target_text = message.text.strip()
    target_time = None

    # Парсим время
    try:
        # Проверяем формат ЧЧ:ММ:СС
        time_parts = target_text.split(':')
        if len(time_parts) == 3:
            hours, minutes, seconds = map(int, time_parts)
            if 0 <= hours <= 24 and 0 <= minutes < 60 and 0 <= seconds < 60:
                target_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                raise ValueError
        elif len(time_parts) == 2:
            # Формат ММ:СС
            minutes, seconds = map(int, time_parts)
            if 0 <= minutes < 60 and 0 <= seconds < 60:
                target_time = f"00:{minutes:02d}:{seconds:02d}"
            else:
                raise ValueError
        else:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer(
            "❌ Неверный формат времени.\n"
            "Используйте формат: ЧЧ:ММ:СС (например: 03:30:00)\n"
            "Или нажмите кнопку 'Пропустить'."
        )
        return

    # Создаем соревнование
    await create_competition_from_state(message.from_user.id, state, target_time, message)


# ========== СТАТИСТИКА СОРЕВНОВАНИЙ ==========

@router.callback_query(F.data == "comp:statistics")
async def show_competition_statistics(callback: CallbackQuery):
    """Показать статистику соревнований пользователя"""

    from competitions.statistics_queries import get_user_competition_stats

    user_id = callback.from_user.id
    stats = await get_user_competition_stats(user_id)

    if not stats or stats['total_competitions'] == 0:
        text = (
            "📊 <b>СТАТИСТИКА СОРЕВНОВАНИЙ</b>\n\n"
            "У вас пока нет завершённых соревнований с результатами.\n\n"
            "Участвуйте в соревнованиях и добавляйте результаты, "
            "чтобы отслеживать свой прогресс!"
        )
    else:
        text = "📊 <b>СТАТИСТИКА СОРЕВНОВАНИЙ</b>\n\n"

        text += f"🏆 <b>Всего соревнований:</b> {stats['total_competitions']}\n"
        text += f"✅ <b>Завершено:</b> {stats['total_completed']}\n\n"

        if stats['total_marathons'] > 0:
            text += f"🏃 <b>Марафоны (42.2 км):</b> {stats['total_marathons']}\n"
            if stats.get('best_marathon_time'):
                normalized_time = normalize_time(stats['best_marathon_time'])
                text += f"   ⏱️ Лучшее время: {normalized_time}\n"
            text += "\n"

        if stats['total_half_marathons'] > 0:
            text += f"🏃 <b>Полумарафоны (21.1 км):</b> {stats['total_half_marathons']}\n"
            if stats.get('best_half_marathon_time'):
                normalized_time = normalize_time(stats['best_half_marathon_time'])
                text += f"   ⏱️ Лучшее время: {normalized_time}\n"
            text += "\n"

        if stats['total_10k'] > 0:
            text += f"🏃 <b>10 км:</b> {stats['total_10k']}\n"
            if stats.get('best_10k_time'):
                normalized_time = normalize_time(stats['best_10k_time'])
                text += f"   ⏱️ Лучшее время: {normalized_time}\n"
            text += "\n"

        if stats['total_5k'] > 0:
            text += f"🏃 <b>5 км:</b> {stats['total_5k']}\n"
            if stats.get('best_5k_time'):
                normalized_time = normalize_time(stats['best_5k_time'])
                text += f"   ⏱️ Лучшее время: {normalized_time}\n"
            text += "\n"

        if stats.get('total_distance_km', 0) > 0:
            text += f"📏 <b>Общая дистанция:</b> {stats['total_distance_km']:.1f} км\n"

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏅 Мои результаты", callback_data="comp:my_results"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="comp:menu"))

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()


# ========== ДОБАВЛЕНИЕ ПРОШЕДШЕГО СОРЕВНОВАНИЯ ==========

@router.callback_query(F.data == "comp:add_past")
async def start_add_past_competition(callback: CallbackQuery, state: FSMContext):
    """Начать добавление прошедшего соревнования"""

    text = (
        "🏁 <b>ДОБАВЛЕНИЕ ПРОШЕДШЕГО СОРЕВНОВАНИЯ</b>\n\n"
        "Вы можете добавить соревнование, в котором уже участвовали.\n\n"
        "📝 <b>Шаг 1 из 9</b>\n\n"
        "Введите <b>название</b> соревнования:\n"
        "<i>Например: Московский марафон 2024</i>"
    )

    await callback.message.edit_text(text, parse_mode="HTML")
    await state.set_state(CompetitionStates.waiting_for_past_comp_name)
    await callback.answer()


@router.message(CompetitionStates.waiting_for_past_comp_name)
async def process_past_comp_name(message: Message, state: FSMContext):
    """Обработать название прошедшего соревнования"""

    comp_name = message.text.strip()

    if not comp_name or len(comp_name) < 3:
        await message.answer(
            "❌ Название слишком короткое. Введите название минимум из 3 символов."
        )
        return

    # Сохраняем название
    await state.update_data(comp_name=comp_name, is_past_competition=True)

    text = (
        f"✅ Название: <b>{comp_name}</b>\n\n"
        f"📝 <b>Шаг 2 из 9</b>\n\n"
        f"Введите <b>город</b>, где проходило соревнование:\n"
        f"<i>Например: Москва, Санкт-Петербург, Казань</i>"
    )

    await message.answer(text, parse_mode="HTML")
    await state.set_state(CompetitionStates.waiting_for_past_comp_city)


@router.message(CompetitionStates.waiting_for_past_comp_city)
async def process_past_comp_city(message: Message, state: FSMContext):
    """Обработать город прошедшего соревнования"""

    comp_city = message.text.strip()

    if not comp_city or len(comp_city) < 2:
        await message.answer(
            "❌ Название города слишком короткое. Введите корректное название города."
        )
        return

    # Сохраняем город
    await state.update_data(comp_city=comp_city)

    # Показываем календарь для выбора даты (без ограничения на прошлые даты)
    calendar = CalendarKeyboard.create_calendar(
        calendar_format=1,
        current_date=datetime.now(),
        callback_prefix="cal_past_comp"
    )

    user_id = message.from_user.id
    date_format_desc = await get_date_format_description(user_id)

    text = (
        f"✅ Город: <b>{comp_city}</b>\n\n"
        f"📝 <b>Шаг 3 из 9</b>\n\n"
        f"Выберите <b>дату</b> соревнования из календаря\n"
        f"или введите вручную в формате: <b>{date_format_desc}</b>\n\n"
        f"<i>Например: {datetime.now().strftime('%d.%m.%Y')}</i>"
    )

    await message.answer(text, parse_mode="HTML", reply_markup=calendar)
    await state.set_state(CompetitionStates.waiting_for_past_comp_date)


# Обработчики календаря для выбора даты прошедшего соревнования
@router.callback_query(F.data.startswith("cal_past_comp_1_select_"), CompetitionStates.waiting_for_past_comp_date)
async def handle_past_comp_calendar_day_select(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора дня в календаре для прошедшего соревнования"""

    parsed = CalendarKeyboard.parse_callback_data(callback.data.replace("cal_past_comp_", "cal_"))
    selected_date = parsed.get("date")

    if not selected_date:
        await callback.answer("❌ Ошибка выбора даты", show_alert=True)
        return

    comp_date = selected_date.date()

    # Для прошедших соревнований не проверяем, что дата в будущем
    # Но проверяем, что дата не слишком далеко в прошлом (например, не более 10 лет)
    years_ago = (date.today() - comp_date).days // 365
    if years_ago > 10:
        await callback.answer("❌ Дата не может быть более 10 лет назад!", show_alert=True)
        return

    # Проверяем, что дата не в будущем
    if comp_date > date.today():
        await callback.answer("❌ Для прошедших соревнований дата должна быть в прошлом!", show_alert=True)
        return

    # Сохраняем дату
    await state.update_data(comp_date=comp_date.strftime('%Y-%m-%d'))

    user_id = callback.from_user.id
    formatted_date = await format_competition_date(comp_date.strftime('%Y-%m-%d'), user_id)

    # Создаём клавиатуру с типами
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏃 Бег", callback_data="pastcomptype:running"))
    builder.row(InlineKeyboardButton(text="🏊 Плавание", callback_data="pastcomptype:swimming"))
    builder.row(InlineKeyboardButton(text="🚴 Велоспорт", callback_data="pastcomptype:cycling"))
    builder.row(InlineKeyboardButton(text="🏊‍♂️🚴‍♂️🏃 Триатлон", callback_data="pastcomptype:triathlon"))
    builder.row(InlineKeyboardButton(text="⛰️ Трейл", callback_data="pastcomptype:trail"))

    text = (
        f"✅ Дата: <b>{formatted_date}</b>\n\n"
        f"📝 <b>Шаг 4 из 9</b>\n\n"
        f"Выберите <b>вид спорта</b>:"
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await state.set_state(CompetitionStates.waiting_for_past_comp_type)
    await callback.answer()


@router.callback_query(F.data.startswith("cal_past_comp_"), CompetitionStates.waiting_for_past_comp_date)
async def handle_past_comp_calendar_navigation(callback: CallbackQuery, state: FSMContext):
    """Обработка навигации по календарю для прошедшего соревнования"""

    parsed = CalendarKeyboard.parse_callback_data(callback.data.replace("cal_past_comp_", "cal_"))

    # Получаем текущую дату из callback или используем текущую
    current_date = parsed.get("date")
    if not current_date:
        current_date = datetime.now()

    action = parsed.get("action", "")
    cal_format = parsed.get("format", 1)

    # Обрабатываем навигацию (аналогично обычному календарю)
    if action == "less":
        if cal_format == 1:
            current_date = current_date.replace(day=1)
            if current_date.month == 1:
                current_date = current_date.replace(year=current_date.year - 1, month=12)
            else:
                current_date = current_date.replace(month=current_date.month - 1)
        elif cal_format == 2:
            current_date = current_date.replace(year=current_date.year - 1)
    elif action == "more":
        if cal_format == 1:
            current_date = current_date.replace(day=1)
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        elif cal_format == 2:
            current_date = current_date.replace(year=current_date.year + 1)
    elif action == "change":
        # Переключаем формат календаря
        if cal_format == 1:
            cal_format = 2  # С дней на месяцы
        elif cal_format == 2:
            cal_format = 3  # С месяцев на годы
    elif action == "select_month":
        cal_format = 2
    elif action == "select_year":
        cal_format = 3

    # Создаём обновлённый календарь
    calendar = CalendarKeyboard.create_calendar(
        calendar_format=cal_format,
        current_date=current_date,
        callback_prefix="cal_past_comp"
    )

    await callback.message.edit_reply_markup(reply_markup=calendar)
    await callback.answer()


@router.message(CompetitionStates.waiting_for_past_comp_date)
async def process_past_comp_date_text(message: Message, state: FSMContext):
    """Обработать дату прошедшего соревнования (текстовый ввод)"""

    date_text = message.text.strip()
    user_id = message.from_user.id

    # Парсим дату с учетом формата пользователя
    comp_date = await parse_user_date_input(date_text, user_id)

    if comp_date is None:
        date_format_desc = await get_date_format_description(user_id)
        await message.answer(
            f"❌ Неверный формат даты.\n"
            f"Используйте формат: {date_format_desc}\n"
            f"Или выберите дату из календаря выше."
        )
        return

    # Проверяем что дата не в будущем
    if comp_date > date.today():
        await message.answer(
            "❌ Для прошедших соревнований дата должна быть в прошлом или сегодня.\n"
            "Введите корректную дату или выберите из календаря:"
        )
        return

    # Проверяем, что дата не более 10 лет назад
    years_ago = (date.today() - comp_date).days // 365
    if years_ago > 10:
        await message.answer(
            "❌ Дата не может быть более 10 лет назад.\n"
            "Введите корректную дату:"
        )
        return

    # Сохраняем дату
    await state.update_data(comp_date=comp_date.strftime('%Y-%m-%d'))

    formatted_date = await format_competition_date(comp_date.strftime('%Y-%m-%d'), user_id)

    # Создаём клавиатуру с типами
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏃 Бег", callback_data="pastcomptype:running"))
    builder.row(InlineKeyboardButton(text="🏊 Плавание", callback_data="pastcomptype:swimming"))
    builder.row(InlineKeyboardButton(text="🚴 Велоспорт", callback_data="pastcomptype:cycling"))
    builder.row(InlineKeyboardButton(text="🏊‍♂️🚴‍♂️🏃 Триатлон", callback_data="pastcomptype:triathlon"))
    builder.row(InlineKeyboardButton(text="⛰️ Трейл", callback_data="pastcomptype:trail"))

    text = (
        f"✅ Дата: <b>{formatted_date}</b>\n\n"
        f"📝 <b>Шаг 4 из 9</b>\n\n"
        f"Выберите <b>вид спорта</b>:"
    )

    await message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await state.set_state(CompetitionStates.waiting_for_past_comp_type)


@router.callback_query(F.data.startswith("pastcomptype:"))
async def process_past_comp_type(callback: CallbackQuery, state: FSMContext):
    """Обработать тип прошедшего соревнования"""

    comp_type_map = {
        "running": "бег",
        "swimming": "плавание",
        "cycling": "велоспорт",
        "triathlon": "триатлон",
        "trail": "трейл"
    }

    comp_type_key = callback.data.split(":")[1]
    comp_type = comp_type_map.get(comp_type_key, "забег")

    await state.update_data(comp_type=comp_type)

    user_id = callback.from_user.id
    distance_unit = await get_distance_unit_name(user_id)

    text = (
        f"✅ Вид спорта: <b>{comp_type}</b>\n\n"
        f"📝 <b>Шаг 5 из 9</b>\n\n"
        f"Введите <b>дистанцию</b> в {distance_unit}:\n"
        f"<i>Например: 42.195, 21.1, 10, 5</i>"
    )

    await callback.message.edit_text(text, parse_mode="HTML")
    await state.set_state(CompetitionStates.waiting_for_past_comp_distance)
    await callback.answer()


@router.message(CompetitionStates.waiting_for_past_comp_distance)
async def process_past_comp_distance(message: Message, state: FSMContext):
    """Обработать дистанцию прошедшего соревнования"""

    user_id = message.from_user.id
    distance_km = await parse_user_distance_input(message.text, user_id)

    if not distance_km or distance_km <= 0:
        await message.answer(
            "❌ Некорректная дистанция. Введите положительное число."
        )
        return

    await state.update_data(comp_distance=distance_km)

    # Для прошедших соревнований запрашиваем результат
    text = (
        f"✅ Дистанция: <b>{await format_competition_distance(distance_km, user_id)}</b>\n\n"
        f"📝 <b>Шаг 6 из 9: Финишное время</b>\n\n"
        f"Введите <b>ваше финишное время</b>:\n"
        f"Формат: ЧЧ:ММ:СС или ММ:СС или Ч:М:С (можно с сотыми: ЧЧ:ММ:СС.сс)\n\n"
        f"<i>Примеры:\n"
        f"• 1:23:45.50\n"
        f"• 42:30.25\n"
        f"• 1:23:45\n"
        f"• 2:0:0</i>\n\n"
        f"Или нажмите \"Пропустить\", если не добавляете результат"
    )

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⏭️ Пропустить результат", callback_data="skip_past_comp_all_result"))

    await message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await state.set_state(CompetitionStates.waiting_for_past_comp_result)


@router.callback_query(F.data == "skip_past_comp_all_result")
async def skip_past_comp_all_result(callback: CallbackQuery, state: FSMContext):
    """Пропустить ввод результата полностью"""
    await finalize_past_competition(callback, state, has_result=False)
    await callback.answer()


@router.message(CompetitionStates.waiting_for_past_comp_result)
async def process_past_comp_result_time(message: Message, state: FSMContext):
    """Обработать время прошедшего соревнования"""

    time_text = message.text.strip()

    # Валидация формата времени
    if not validate_time_format(time_text):
        await message.answer(
            "❌ Некорректный формат времени. Используйте формат ЧЧ:ММ:СС.сс или ММ:СС.сс или Ч:М:С\n"
            "Примеры: 1:23:45.50 или 42:30.25 или 2:0:0"
        )
        return

    # Нормализуем время перед сохранением
    normalized_time = normalize_time(time_text)
    await state.update_data(finish_time=normalized_time)

    # Запрашиваем место в общем зачёте
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_past_place_overall"))

    text = (
        f"✅ Время: <b>{normalized_time}</b>\n\n"
        f"📝 <b>Шаг 7 из 9: Место в общем зачёте</b>\n\n"
        f"Введите ваше <b>место в общем зачёте</b> (число):\n"
        f"Или нажмите \"Пропустить\", если не помните"
    )

    await message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await state.set_state(CompetitionStates.waiting_for_past_comp_place_overall)


@router.callback_query(F.data == "skip_past_place_overall")
async def skip_past_place_overall(callback: CallbackQuery, state: FSMContext):
    """Пропустить место в общем зачёте"""
    await state.update_data(place_overall=None)
    await ask_past_comp_place_age(callback.message, state)
    await callback.answer()


@router.message(CompetitionStates.waiting_for_past_comp_place_overall)
async def process_past_comp_place_overall(message: Message, state: FSMContext):
    """Обработать место в общем зачёте"""

    try:
        place = int(message.text.strip())
        if place <= 0:
            await message.answer("❌ Место должно быть положительным числом")
            return
        await state.update_data(place_overall=place)
    except ValueError:
        await message.answer(
            "❌ Некорректное значение. Введите число или нажмите \"Пропустить\""
        )
        return

    await ask_past_comp_place_age(message, state)


async def ask_past_comp_place_age(message, state: FSMContext):
    """Запросить место в возрастной категории"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_past_place_age"))

    text = (
        "📝 <b>Шаг 8 из 9: Место в возрастной категории</b>\n\n"
        "Введите ваше <b>место в возрастной категории</b> (число):\n"
        "Или нажмите \"Пропустить\", если не помните"
    )

    await message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await state.set_state(CompetitionStates.waiting_for_past_comp_place_age)


@router.callback_query(F.data == "skip_past_place_age")
async def skip_past_place_age(callback: CallbackQuery, state: FSMContext):
    """Пропустить место в категории"""
    await state.update_data(place_age=None)
    await ask_past_comp_heart_rate(callback.message, state)
    await callback.answer()


@router.message(CompetitionStates.waiting_for_past_comp_place_age)
async def process_past_comp_place_age(message: Message, state: FSMContext):
    """Обработать место в возрастной категории"""

    try:
        place = int(message.text.strip())
        if place <= 0:
            await message.answer("❌ Место должно быть положительным числом")
            return
        await state.update_data(place_age=place)
    except ValueError:
        await message.answer(
            "❌ Некорректное значение. Введите число или нажмите \"Пропустить\""
        )
        return

    await ask_past_comp_heart_rate(message, state)


async def ask_past_comp_heart_rate(message, state: FSMContext):
    """Запросить средний пульс"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_past_heart_rate"))

    text = (
        "📝 <b>Шаг 9 из 9: Средний пульс</b>\n\n"
        "Введите ваш <b>средний пульс</b> за соревнование (уд/мин):\n"
        "Или нажмите \"Пропустить\", если не помните"
    )

    await message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await state.set_state(CompetitionStates.waiting_for_past_comp_heart_rate)


@router.callback_query(F.data == "skip_past_heart_rate")
async def skip_past_heart_rate(callback: CallbackQuery, state: FSMContext):
    """Пропустить пульс и завершить"""
    await state.update_data(heart_rate=None)
    await finalize_past_competition(callback, state, has_result=True)
    await callback.answer()


@router.message(CompetitionStates.waiting_for_past_comp_heart_rate)
async def process_past_comp_heart_rate(message: Message, state: FSMContext):
    """Обработать средний пульс и завершить"""

    try:
        hr = int(message.text.strip())
        if hr <= 0 or hr > 250:
            await message.answer("❌ Пульс должен быть в диапазоне 1-250 уд/мин")
            return
        await state.update_data(heart_rate=hr)
    except ValueError:
        await message.answer(
            "❌ Некорректное значение. Введите число или нажмите \"Пропустить\""
        )
        return

    # Создаём заглушку для callback
    from types import SimpleNamespace
    fake_callback = SimpleNamespace(
        message=message,
        answer=lambda *args, **kwargs: None
    )

    await finalize_past_competition(fake_callback, state, has_result=True)


async def finalize_past_competition(callback, state: FSMContext, has_result: bool):
    """Завершить добавление прошедшего соревнования"""

    data = await state.get_data()

    # Создаём соревнование в БД
    comp_data = {
        'name': data['comp_name'],
        'date': data['comp_date'],
        'city': data['comp_city'],
        'country': 'Россия',
        'type': data['comp_type'],
        'distances': json.dumps([data['comp_distance']]),
        'status': 'finished',  # Важно: статус "finished" для прошедших соревнований
        'is_official': 0,  # Пользовательское соревнование
        'organizer': 'Добавлено пользователем',
        'description': 'Прошедшее соревнование, добавленное вручную'
    }

    try:
        comp_id = await add_competition(comp_data)

        # Регистрируем пользователя на это соревнование
        user_id = callback.message.chat.id if hasattr(callback.message, 'chat') else callback.message.from_user.id
        await register_for_competition(user_id, comp_id, data['comp_distance'])

        # Если есть результат, добавляем его
        if has_result and 'finish_time' in data:
            await add_competition_result(
                user_id=user_id,
                competition_id=comp_id,
                distance=data['comp_distance'],
                finish_time=data['finish_time'],
                place_overall=data.get('place_overall'),
                place_age_category=data.get('place_age'),
                heart_rate=data.get('heart_rate')
            )

        text = (
            "✅ <b>ПРОШЕДШЕЕ СОРЕВНОВАНИЕ ДОБАВЛЕНО!</b>\n\n"
            f"🏆 <b>{data['comp_name']}</b>\n"
            f"📍 {data['comp_city']}\n"
            f"📅 {data['comp_date']}\n"
            f"📏 {data['comp_distance']} км\n"
        )

        if has_result:
            text += f"⏱️ Время: {data['finish_time']}\n"
            if data.get('place_overall'):
                text += f"🏆 Место общее: {data['place_overall']}\n"
            if data.get('place_age'):
                text += f"🏅 Место в категории: {data['place_age']}\n"
            if data.get('heart_rate'):
                text += f"❤️ Средний пульс: {data['heart_rate']} уд/мин\n"

        text += "\n✅ Соревнование добавлено в ваши результаты!"

        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🏅 Мои результаты", callback_data="comp:my_results"))
        builder.row(InlineKeyboardButton(text="◀️ Главное меню", callback_data="comp:menu"))

        await callback.message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())

    except Exception as e:
        logger.error(f"Error adding past competition: {e}")
        await callback.message.answer(
            "❌ Ошибка при добавлении соревнования. Попробуйте снова."
        )

    await state.clear()
