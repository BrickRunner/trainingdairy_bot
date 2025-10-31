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
        f"<i>Формат: ЧЧ:ММ:СС\n"
        f"Например: 03:30:00 (3 часа 30 минут)\n"
        f"Или: 00:45:00 (45 минут)</i>\n\n"
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
                text += f"   ⏱️ Лучшее время: {stats['best_marathon_time']}\n"
            text += "\n"

        if stats['total_half_marathons'] > 0:
            text += f"🏃 <b>Полумарафоны (21.1 км):</b> {stats['total_half_marathons']}\n"
            if stats.get('best_half_marathon_time'):
                text += f"   ⏱️ Лучшее время: {stats['best_half_marathon_time']}\n"
            text += "\n"

        if stats['total_10k'] > 0:
            text += f"🏃 <b>10 км:</b> {stats['total_10k']}\n"
            if stats.get('best_10k_time'):
                text += f"   ⏱️ Лучшее время: {stats['best_10k_time']}\n"
            text += "\n"

        if stats['total_5k'] > 0:
            text += f"🏃 <b>5 км:</b> {stats['total_5k']}\n"
            if stats.get('best_5k_time'):
                text += f"   ⏱️ Лучшее время: {stats['best_5k_time']}\n"
            text += "\n"

        if stats.get('total_distance_km', 0) > 0:
            text += f"📏 <b>Общая дистанция:</b> {stats['total_distance_km']:.1f} км\n"

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏅 Мои результаты", callback_data="comp:my_results"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="comp:menu"))

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()
