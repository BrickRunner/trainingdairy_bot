"""
Обработчики для предложения соревнований от тренера ученику
"""

import logging
import json
from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.fsm import CompetitionStates
from bot.keyboards import get_main_menu_keyboard
from coach.coach_training_queries import can_coach_access_student, get_student_display_name
from competitions.competitions_queries import add_competition, get_competition, get_upcoming_competitions
from competitions.competitions_fetcher import fetch_all_competitions, SERVICE_CODES
from database.queries import get_user

logger = logging.getLogger(__name__)
router = Router()


# ========== ГЛАВНОЕ МЕНЮ СОРЕВНОВАНИЙ ДЛЯ ТРЕНЕРА ==========

@router.callback_query(F.data.startswith("coach:competitions_menu:"))
async def show_coach_competitions_menu(callback: CallbackQuery, state: FSMContext):
    """Главное меню раздела 'Соревнования' для тренера"""

    student_id = int(callback.data.split(":")[2])
    coach_id = callback.from_user.id

    # Проверяем доступ
    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    display_name = await get_student_display_name(coach_id, student_id)

    # Очищаем состояние при входе в меню
    await state.clear()

    text = (
        f"🏆 <b>СОРЕВНОВАНИЯ</b>\n\n"
        f"Ученик: <b>{display_name}</b>\n\n"
        f"Выберите раздел:"
    )

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📅 Предстоящие соревнования",
            callback_data=f"coach:comp_upcoming_main:{student_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🔍 Найти соревнование вручную",
            callback_data=f"coach:comp_manual:{student_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📋 Соревнования ученика",
            callback_data=f"coach:student_competitions:{student_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="« Назад",
            callback_data=f"coach:student:{student_id}"
        )
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()


# ========== ПРЕДЛОЖЕНИЕ СОРЕВНОВАНИЯ УЧЕНИКУ (СТАРАЯ КНОПКА - РЕДИРЕКТ) ==========

@router.callback_query(F.data.startswith("coach:propose_comp:"))
async def start_propose_competition(callback: CallbackQuery, state: FSMContext):
    """Редирект старой кнопки на новое меню соревнований"""

    student_id = int(callback.data.split(":")[2])
    coach_id = callback.from_user.id

    # Проверяем доступ
    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    # Перенаправляем на новое меню
    await show_coach_competitions_menu(callback, state)


@router.callback_query(F.data.startswith("coach:comp_manual:"))
async def coach_propose_manual_competition(callback: CallbackQuery, state: FSMContext):
    """Начать процесс ручного создания соревнования для ученика"""

    student_id = int(callback.data.split(":")[2])
    coach_id = callback.from_user.id

    # Проверяем доступ
    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    display_name = await get_student_display_name(coach_id, student_id)

    # Сохраняем student_id в состоянии
    await state.update_data(
        propose_student_id=student_id,
        coach_propose_mode=True
    )

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="❌ Отменить",
            callback_data=f"coach:cancel_propose_comp:{student_id}"
        )
    )

    text = (
        f"🏆 <b>ПРЕДЛОЖИТЬ СОРЕВНОВАНИЕ</b>\n\n"
        f"Ученик: <b>{display_name}</b>\n\n"
        f"📝 <b>Шаг 1 из 4</b>\n\n"
        f"Введите <b>название</b> соревнования:\n"
        f"<i>Например: Московский марафон 2026</i>"
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await state.set_state(CompetitionStates.waiting_for_comp_name)
    await callback.answer()


@router.callback_query(F.data.startswith("coach:cancel_propose_comp:"))
async def cancel_propose_competition(callback: CallbackQuery, state: FSMContext):
    """Отменить предложение соревнования"""
    parts = callback.data.split(":")
    student_id = int(parts[2])
    coach_id = callback.from_user.id

    await state.clear()

    # Возвращаемся к меню предложения соревнования
    display_name = await get_student_display_name(coach_id, student_id)

    text = (
        f"🏆 <b>ПРЕДЛОЖИТЬ СОРЕВНОВАНИЕ</b>\n\n"
        f"Ученик: <b>{display_name}</b>\n\n"
        f"Выберите способ:"
    )

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📅 Предстоящие соревнования",
            callback_data=f"coach:comp_upcoming:{student_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🔍 Найти соревнование вручную",
            callback_data=f"coach:comp_manual:{student_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="« Назад",
            callback_data=f"coach:student:{student_id}"
        )
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer("❌ Отменено")


@router.message(CompetitionStates.waiting_for_comp_name)
async def process_proposed_comp_name(message: Message, state: FSMContext):
    """Обработать название предложенного соревнования"""

    # Проверяем что это flow от тренера (есть propose_student_id)
    data = await state.get_data()
    if 'propose_student_id' not in data:
        # Это обычный пользовательский flow, пропускаем
        return

    comp_name = message.text.strip()

    if not comp_name or len(comp_name) < 3:
        await message.answer(
            "❌ Название слишком короткое. Введите название минимум из 3 символов."
        )
        return

    # Сохраняем название
    await state.update_data(comp_name=comp_name)

    student_id = data.get('propose_student_id')
    coach_id = message.from_user.id

    # Получаем формат даты тренера для подсказки
    from utils.date_formatter import get_user_date_format
    coach_date_format = await get_user_date_format(coach_id)

    # Определяем формат для примера
    if coach_date_format == 'ММ/ДД/ГГГГ':
        format_example = "ММ/ДД/ГГГГ"
        date_example = "09/25/2026"
    elif coach_date_format == 'ГГГГ-ММ-ДД':
        format_example = "ГГГГ-ММ-ДД"
        date_example = "2026-09-25"
    else:  # ДД.ММ.ГГГГ
        format_example = "ДД.ММ.ГГГГ"
        date_example = "25.09.2026"

    # Сразу показываем календарь
    from datetime import date
    from bot.calendar_keyboard import CalendarKeyboard

    today = date.today()
    calendar_markup = CalendarKeyboard.create_calendar(
        calendar_format=1,
        current_date=datetime(today.year, today.month, 1),
        callback_prefix="coach_comp_cal"
    )

    text = (
        f"✅ Название: <b>{comp_name}</b>\n\n"
        f"📝 <b>Шаг 2 из 4</b>\n\n"
        f"📅 Выберите <b>дату</b> соревнования из календаря\n\n"
        f"Или введите дату вручную в формате: <b>{format_example}</b>\n"
        f"<i>Например: {date_example}</i>"
    )

    await message.answer(text, parse_mode="HTML", reply_markup=calendar_markup)
    await state.set_state(CompetitionStates.waiting_for_comp_date)


@router.callback_query(F.data.startswith("coach:comp_calendar:"))
async def show_competition_calendar(callback: CallbackQuery, state: FSMContext):
    """Показать календарь для выбора даты соревнования"""
    student_id = int(callback.data.split(":")[2])

    from datetime import date
    from bot.calendar_keyboard import CalendarKeyboard

    # Создаём календарь начиная с текущего месяца
    today = date.today()
    calendar_markup = CalendarKeyboard.create_calendar(
        calendar_format=1,
        current_date=datetime(today.year, today.month, 1),
        callback_prefix="coach_comp_cal"
    )

    data = await state.get_data()
    comp_name = data.get('comp_name', '')

    text = (
        f"✅ Название: <b>{comp_name}</b>\n\n"
        f"📝 <b>Шаг 2 из 4</b>\n\n"
        f"📅 Выберите дату соревнования из календаря:"
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=calendar_markup)
    # ВАЖНО: Устанавливаем FSM состояние для обработки выбора даты
    await state.set_state(CompetitionStates.waiting_for_comp_date)
    await callback.answer()


@router.callback_query(F.data.startswith("coach_comp_cal_"), CompetitionStates.waiting_for_comp_date)
async def process_calendar_selection(callback: CallbackQuery, state: FSMContext):
    """Обработать выбор даты из календаря"""
    from bot.calendar_keyboard import CalendarKeyboard
    from datetime import date

    logger.info(f"Calendar callback received: {callback.data}")

    # Парсим callback данные СРАЗУ для навигации
    parsed = CalendarKeyboard.parse_callback_data(callback.data, prefix="coach_comp_cal")

    # Если это навигация по календарю (смена месяца/года) - обрабатываем БЕЗ проверки данных
    if parsed.get('action') in ['less', 'more', 'change']:
        logger.info(f"Calendar navigation: action={parsed.get('action')}")
        new_calendar = CalendarKeyboard.handle_navigation(
            callback.data,
            prefix="coach_comp_cal"
        )
        if new_calendar:
            await callback.message.edit_reply_markup(reply_markup=new_calendar)
        await callback.answer()
        return

    # Для выбора даты ПРОВЕРЯЕМ данные состояния
    data = await state.get_data()
    logger.info(f"FSM state data: {data}")

    if 'propose_student_id' not in data:
        logger.warning("No propose_student_id in state data, ignoring callback")
        await callback.answer("❌ Сессия истекла. Начните заново.", show_alert=True)
        return

    student_id = data.get('propose_student_id')

    # Если это выбор даты
    if parsed.get('action') == 'select' and parsed.get('format') == 1:
        selected_date = parsed.get('date')

        if not selected_date:
            await callback.answer("❌ Ошибка при выборе даты", show_alert=True)
            return

        if selected_date.date() < date.today():
            await callback.answer("❌ Выберите дату в будущем", show_alert=True)
            return

        await state.update_data(comp_date=selected_date.strftime('%Y-%m-%d'))

        # Переходим к выбору типа спорта
        from aiogram.types import InlineKeyboardButton
        from aiogram.utils.keyboard import InlineKeyboardBuilder

        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🏃 Бег", callback_data="comptype:running"))
        builder.row(InlineKeyboardButton(text="🏊 Плавание", callback_data="comptype:swimming"))
        builder.row(InlineKeyboardButton(text="🚴 Велоспорт", callback_data="comptype:cycling"))
        builder.row(InlineKeyboardButton(text="❌ Отменить", callback_data=f"coach:cancel_propose_comp:{student_id}"))

        from utils.date_formatter import get_user_date_format, DateFormatter
        coach_id = callback.from_user.id
        user_date_format = await get_user_date_format(coach_id)
        formatted_date = DateFormatter.format_date(selected_date.strftime('%Y-%m-%d'), user_date_format)

        comp_name = data.get('comp_name', '')

        text = (
            f"✅ Название: <b>{comp_name}</b>\n"
            f"✅ Дата: <b>{formatted_date}</b>\n\n"
            f"📝 <b>Шаг 3 из 4</b>\n\n"
            f"Выберите <b>вид спорта</b>:"
        )

        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
        await state.set_state(CompetitionStates.waiting_for_comp_type)
        await callback.answer()
    else:
        # Игнорируем пустые ячейки
        await callback.answer()


@router.message(CompetitionStates.waiting_for_comp_date)
async def process_proposed_comp_date(message: Message, state: FSMContext):
    """Обработать дату предложенного соревнования (ручной ввод)"""

    # Проверяем что это flow от тренера
    data = await state.get_data()
    if 'propose_student_id' not in data:
        return

    from datetime import date
    from utils.date_formatter import get_user_date_format

    date_text = message.text.strip()
    coach_id = message.from_user.id
    student_id = data.get('propose_student_id')

    # Получаем формат даты тренера
    coach_date_format = await get_user_date_format(coach_id)

    # Пробуем разные форматы
    comp_date = None
    for fmt in ['%d.%m.%Y', '%m/%d/%Y', '%Y-%m-%d']:
        try:
            comp_date = datetime.strptime(date_text, fmt).date()
            break
        except ValueError:
            continue

    if not comp_date:
        # Определяем формат для подсказки
        if coach_date_format == 'ММ/ДД/ГГГГ':
            format_hint = "ММ/ДД/ГГГГ (например: 09/25/2026)"
        elif coach_date_format == 'ГГГГ-ММ-ДД':
            format_hint = "ГГГГ-ММ-ДД (например: 2026-09-25)"
        else:
            format_hint = "ДД.ММ.ГГГГ (например: 25.09.2026)"

        await message.answer(
            f"❌ Неверный формат даты.\n"
            f"Используйте формат: {format_hint}"
        )
        return

    if comp_date < date.today():
        await message.answer(
            "❌ Дата соревнования должна быть в будущем.\n"
            "Введите корректную дату:"
        )
        return

    await state.update_data(comp_date=comp_date.strftime('%Y-%m-%d'))

    # Создаём клавиатуру с типами (только 3 вида)
    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏃 Бег", callback_data="comptype:running"))
    builder.row(InlineKeyboardButton(text="🏊 Плавание", callback_data="comptype:swimming"))
    builder.row(InlineKeyboardButton(text="🚴 Велоспорт", callback_data="comptype:cycling"))
    builder.row(InlineKeyboardButton(text="❌ Отменить", callback_data=f"coach:cancel_propose_comp:{student_id}"))

    from utils.date_formatter import DateFormatter
    formatted_date = DateFormatter.format_date(comp_date.strftime('%Y-%m-%d'), coach_date_format)

    comp_name = data.get('comp_name', '')

    text = (
        f"✅ Название: <b>{comp_name}</b>\n"
        f"✅ Дата: <b>{formatted_date}</b>\n\n"
        f"📝 <b>Шаг 3 из 4</b>\n\n"
        f"Выберите <b>вид спорта</b>:"
    )

    await message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await state.set_state(CompetitionStates.waiting_for_comp_type)


@router.callback_query(F.data.startswith("comptype:"), CompetitionStates.waiting_for_comp_type)
async def process_proposed_comp_type(callback: CallbackQuery, state: FSMContext):
    """Обработать тип предложенного соревнования"""

    # Проверяем что это flow от тренера
    data = await state.get_data()
    if 'propose_student_id' not in data:
        return

    comp_type_map = {
        "running": "бег",
        "swimming": "плавание",
        "cycling": "велоспорт"
    }

    comp_type_key = callback.data.split(":")[1]
    comp_type = comp_type_map.get(comp_type_key, "бег")

    await state.update_data(comp_type=comp_type)

    # Получаем единицы измерения тренера
    student_id = data.get('propose_student_id')
    from database.queries import get_user_settings

    coach_settings = await get_user_settings(callback.from_user.id)
    distance_unit = coach_settings.get('distance_unit', 'км') if coach_settings else 'км'

    # Определяем падеж для единиц измерения
    if distance_unit == 'миль':
        unit_text = "милях"
    else:
        unit_text = "километрах"

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="❌ Отменить",
            callback_data=f"coach:cancel_propose_comp:{student_id}"
        )
    )

    comp_name = data.get('comp_name', '')
    comp_date = data.get('comp_date', '')

    from utils.date_formatter import get_user_date_format, DateFormatter
    coach_date_format = await get_user_date_format(callback.from_user.id)
    formatted_date = DateFormatter.format_date(comp_date, coach_date_format)

    text = (
        f"✅ Название: <b>{comp_name}</b>\n"
        f"✅ Дата: <b>{formatted_date}</b>\n"
        f"✅ Вид спорта: <b>{comp_type.capitalize()}</b>\n\n"
        f"📝 <b>Шаг 4 из 4</b>\n\n"
        f"Введите <b>дистанцию в {unit_text}</b>:\n"
        f"<i>Например:\n"
        f"• 42.195\n"
        f"• 21.1\n"
        f"• 10</i>"
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await state.set_state(CompetitionStates.waiting_for_comp_distance)
    await callback.answer()


@router.message(CompetitionStates.waiting_for_comp_distance)
async def process_proposed_comp_distance(message: Message, state: FSMContext):
    """Обработать дистанцию предложенного соревнования и создать предложение"""

    # Проверяем что это flow от тренера
    data = await state.get_data()
    if 'propose_student_id' not in data:
        return

    distance_text = message.text.strip().replace(',', '.')

    try:
        distance = float(distance_text)

        if distance <= 0 or distance > 500:
            await message.answer(
                "❌ Дистанция должна быть от 0.1 до 500.\n"
                "Введите корректное значение:"
            )
            return

    except ValueError:
        await message.answer(
            "❌ Неверный формат дистанции.\n"
            "Введите число (например: 42.195 или 10):"
        )
        return

    await state.update_data(comp_distance=distance)

    # Получаем все сохранённые данные
    student_id = data.get('propose_student_id')
    comp_name = data.get('comp_name')
    comp_date = data.get('comp_date')
    comp_type = data.get('comp_type')
    comp_distance = distance
    coach_id = message.from_user.id

    # Создаём соревнование без целевого времени
    try:
        import aiosqlite
        import os
        import json
        DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

        # Создаём новое соревнование в БД
        competition_data = {
            'name': comp_name,
            'date': comp_date,
            'type': comp_type,
            'distances': json.dumps([comp_distance]),
            'status': 'upcoming',
            'created_by': coach_id,
            'is_official': 0,
            'registration_status': 'open'
        }

        from competitions.competitions_queries import add_competition
        comp_id = await add_competition(competition_data)

        # Создаём запись участия с флагом "предложено тренером"
        async with aiosqlite.connect(DB_PATH) as db:
            # ВАЖНО: Добавляем соревнование УЧЕНИКУ (student_id), а НЕ тренеру (coach_id)
            await db.execute(
                """
                INSERT INTO competition_participants
                (user_id, competition_id, distance, target_time,
                 proposed_by_coach, proposed_by_coach_id, proposal_status, reminders_enabled)
                VALUES (?, ?, ?, NULL, 1, ?, 'pending', 0)
                """,
                (student_id, comp_id, comp_distance, coach_id)
            )
            await db.commit()

        logger.info(f"✓ Coach {coach_id} proposed competition {comp_id} to STUDENT {student_id}")

        # Получаем имя тренера из настроек
        from database.queries import get_user_settings
        coach_settings = await get_user_settings(coach_id)
        coach_name = coach_settings.get('name') if coach_settings else None

        if not coach_name:
            # Если имени нет в настройках, пробуем получить из users
            from database.queries import get_user
            coach = await get_user(coach_id)
            coach_name = coach.get('name') or coach.get('username') or 'Ваш тренер'

        # Отправляем уведомление ученику
        from utils.date_formatter import get_user_date_format, DateFormatter
        from competitions.competitions_utils import format_competition_distance

        student_date_format = await get_user_date_format(student_id)
        formatted_date = DateFormatter.format_date(comp_date, student_date_format)
        formatted_distance = await format_competition_distance(comp_distance, student_id)

        notification_text = (
            f"🏆 <b>ПРЕДЛОЖЕНИЕ ОТ ТРЕНЕРА</b>\n\n"
            f"<b>{coach_name}</b> предлагает вам участие в соревновании:\n\n"
            f"📌 <b>{comp_name}</b>\n"
            f"📅 Дата: {formatted_date}\n"
            f"🏃 Вид: {comp_type.capitalize()}\n"
            f"📏 Дистанция: {formatted_distance}\n\n"
            f"Принять предложение?"
        )

        from aiogram.types import InlineKeyboardButton
        from aiogram.utils.keyboard import InlineKeyboardBuilder

        notification_builder = InlineKeyboardBuilder()
        notification_builder.row(
            InlineKeyboardButton(
                text="✅ Принять",
                callback_data=f"accept_coach_comp:{comp_id}:{coach_id}"
            ),
            InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=f"reject_coach_comp:{comp_id}:{coach_id}"
            )
        )

        await message.bot.send_message(
            student_id,
            notification_text,
            parse_mode="HTML",
            reply_markup=notification_builder.as_markup()
        )

        # Подтверждение тренеру
        student_display_name = await get_student_display_name(coach_id, student_id)

        await message.answer(
            f"✅ <b>Предложение отправлено!</b>\n\n"
            f"Ученик <b>{student_display_name}</b> получил уведомление о соревновании:\n"
            f"📌 {comp_name}\n"
            f"📅 {formatted_date}\n"
            f"🏃 {comp_type.capitalize()}\n"
            f"📏 {formatted_distance}\n\n"
            f"Ожидайте ответа от ученика.",
            parse_mode="HTML"
        )

        await state.clear()

    except Exception as e:
        logger.error(f"Error proposing competition: {e}", exc_info=True)
        await message.answer(
            "❌ Произошла ошибка при создании предложения. Попробуйте позже."
        )
        await state.clear()


@router.message(CompetitionStates.waiting_for_comp_target)
async def process_proposed_comp_target_and_send(message: Message, state: FSMContext):
    """Обработать целевое время и отправить предложение ученику"""

    # Проверяем что это flow от тренера
    data = await state.get_data()
    if 'propose_student_id' not in data:
        return

    target_text = message.text.strip()
    target_time = None

    if target_text != "0":
        try:
            time_parts = target_text.split(':')
            if len(time_parts) == 3:
                hours, minutes, seconds = map(int, time_parts)
                if 0 <= hours <= 24 and 0 <= minutes < 60 and 0 <= seconds < 60:
                    target_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                else:
                    raise ValueError
            elif len(time_parts) == 2:
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
                "Используйте формат: ЧЧ:ММ:СС или ММ:СС\n"
                "Примеры: 03:30:00 или 45:00\n"
                "Или отправьте 0, чтобы пропустить."
            )
            return

    # Получаем сохранённые данные
    student_id = data.get('propose_student_id')
    comp_name = data.get('comp_name')
    comp_date = data.get('comp_date')
    comp_type = data.get('comp_type')
    comp_distance = data.get('comp_distance')
    selected_comp_id = data.get('selected_comp_id')  # Для flow из предстоящих соревнований

    coach_id = message.from_user.id

    try:
        # Проверяем, это flow из предстоящих соревнований или ручной ввод
        if selected_comp_id:
            # Flow из предстоящих соревнований - используем существующее соревнование
            comp_id = selected_comp_id
        else:
            # Ручной ввод - создаём новое соревнование в БД
            competition_data = {
                'name': comp_name,
                'date': comp_date,
                'type': comp_type,
                'distances': json.dumps([comp_distance]),
                'status': 'upcoming',
                'created_by': coach_id,
                'is_official': 0,
                'registration_status': 'open'
            }

            comp_id = await add_competition(competition_data)

        # Создаём запись участия с флагом "предложено тренером"
        import aiosqlite
        import os
        DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

        async with aiosqlite.connect(DB_PATH) as db:
            # ВАЖНО: Добавляем соревнование УЧЕНИКУ (student_id), а НЕ тренеру (coach_id)
            await db.execute(
                """
                INSERT INTO competition_participants
                (user_id, competition_id, distance, target_time,
                 proposed_by_coach, proposed_by_coach_id, proposal_status, reminders_enabled)
                VALUES (?, ?, ?, ?, 1, ?, 'pending', 0)
                """,
                (student_id, comp_id, comp_distance, target_time, coach_id)
            )
            await db.commit()

            # Проверка: убеждаемся что запись создалась для ученика
            async with db.execute(
                "SELECT user_id, proposed_by_coach_id FROM competition_participants WHERE competition_id = ? AND user_id = ?",
                (comp_id, student_id)
            ) as cursor:
                check = await cursor.fetchone()
                if check:
                    logger.info(f"✓ VERIFIED: Competition {comp_id} registered to user_id={check[0]} (STUDENT), proposed by coach_id={check[1]}")
                else:
                    logger.error(f"✗ ERROR: Failed to verify competition registration!")

        logger.info(f"✓ Coach {coach_id} proposed competition {comp_id} to STUDENT {student_id} (user_id={student_id})")
        logger.info(f"  Competition will appear in STUDENT'S 'My competitions' after acceptance")

        # Получаем имя тренера
        coach = await get_user(coach_id)
        coach_name = coach.get('name') or coach.get('username') or 'Ваш тренер'

        # Отправляем уведомление ученику
        student_display_name = await get_student_display_name(coach_id, student_id)

        from utils.date_formatter import get_user_date_format, DateFormatter
        from competitions.competitions_utils import format_competition_distance

        student_date_format = await get_user_date_format(student_id)
        formatted_date = DateFormatter.format_date(comp_date, student_date_format)
        formatted_distance = await format_competition_distance(comp_distance, student_id)

        notification_text = (
            f"🏆 <b>ПРЕДЛОЖЕНИЕ ОТ ТРЕНЕРА</b>\n\n"
            f"<b>{coach_name}</b> предлагает вам участие в соревновании:\n\n"
            f"📌 <b>{comp_name}</b>\n"
            f"📅 Дата: {formatted_date}\n"
            f"🏃 Вид: {comp_type}\n"
            f"📏 Дистанция: {formatted_distance}\n"
        )

        if target_time:
            notification_text += f"🎯 Рекомендуемая цель: {target_time}\n"

        notification_text += "\nЧто вы решите?"

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="✅ Принять",
                callback_data=f"accept_coach_comp:{comp_id}:{coach_id}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=f"reject_coach_comp:{comp_id}:{coach_id}"
            )
        )

        try:
            await message.bot.send_message(
                student_id,
                notification_text,
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
            logger.info(f"Notification sent to student {student_id} about competition {comp_id}")
        except Exception as e:
            logger.error(f"Failed to send notification to student {student_id}: {e}")
            await message.answer(
                f"⚠️ Не удалось отправить уведомление ученику. Ошибка: {e}",
                parse_mode="HTML"
            )
            await state.clear()
            return

        # Подтверждение тренеру
        coach_date_format = await get_user_date_format(coach_id)
        coach_formatted_date = DateFormatter.format_date(comp_date, coach_date_format)
        coach_formatted_distance = await format_competition_distance(comp_distance, coach_id)

        text = (
            "✅ <b>Предложение отправлено!</b>\n\n"
            f"Ученик <b>{student_display_name}</b> получил уведомление о соревновании:\n\n"
            f"🏆 <b>{comp_name}</b>\n"
            f"📅 {coach_formatted_date}\n"
            f"📏 {coach_formatted_distance}\n\n"
            f"Вы получите уведомление, когда ученик примет решение."
        )

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text=f"« К ученику {student_display_name}",
                callback_data=f"coach:student:{student_id}"
            )
        )

        await message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())

        await state.clear()

    except Exception as e:
        logger.error(f"Error proposing competition: {e}")
        await message.answer(
            "❌ Произошла ошибка при отправке предложения.\n"
            "Попробуйте ещё раз позже."
        )
        await state.clear()


# ========== ОТМЕНА ПРЕДЛОЖЕНИЯ СОРЕВНОВАНИЯ ==========

@router.callback_query(F.data == "coach:cancel_propose_comp")
async def cancel_propose_competition_callback(callback: CallbackQuery, state: FSMContext):
    """Отмена предложения соревнования (через инлайн-кнопку)"""

    data = await state.get_data()
    student_id = data.get('propose_student_id')

    if not student_id:
        await callback.answer("Ошибка: студент не найден", show_alert=True)
        await state.clear()
        return

    await state.clear()

    # Редирект в меню ученика
    from coach.coach_keyboards import get_student_detail_keyboard
    from coach.coach_training_queries import get_student_display_name

    coach_id = callback.from_user.id
    display_name = await get_student_display_name(coach_id, student_id)

    text = f"👤 <b>{display_name}</b>\n\nВыберите действие:"

    await callback.message.edit_text(
        text,
        reply_markup=get_student_detail_keyboard(student_id),
        parse_mode="HTML"
    )
    await callback.answer("❌ Отменено")


@router.message(F.text == "❌ Отменить", CompetitionStates.waiting_for_comp_name)
async def cancel_propose_comp_name(message: Message, state: FSMContext):
    """Отмена на этапе ввода названия"""

    data = await state.get_data()
    if 'propose_student_id' not in data:
        return

    student_id = data.get('propose_student_id')
    await state.clear()

    # Редирект в меню ученика
    from coach.coach_keyboards import get_student_detail_keyboard
    from coach.coach_training_queries import get_student_display_name
    from bot.keyboards import get_main_menu_keyboard
    from coach.coach_queries import is_user_coach

    coach_id = message.from_user.id
    display_name = await get_student_display_name(coach_id, student_id)
    is_coach = await is_user_coach(coach_id)

    text = f"👤 <b>{display_name}</b>\n\nВыберите действие:"

    await message.answer(
        text,
        reply_markup=get_student_detail_keyboard(student_id),
        parse_mode="HTML"
    )
    await message.answer(
        "Главное меню:",
        reply_markup=get_main_menu_keyboard(is_coach)
    )


@router.message(F.text == "❌ Отменить", CompetitionStates.waiting_for_comp_date)
async def cancel_propose_comp_date(message: Message, state: FSMContext):
    """Отмена на этапе ввода даты"""

    data = await state.get_data()
    if 'propose_student_id' not in data:
        return

    student_id = data.get('propose_student_id')
    await state.clear()

    # Редирект в меню ученика
    from coach.coach_keyboards import get_student_detail_keyboard
    from coach.coach_training_queries import get_student_display_name
    from bot.keyboards import get_main_menu_keyboard
    from coach.coach_queries import is_user_coach

    coach_id = message.from_user.id
    display_name = await get_student_display_name(coach_id, student_id)
    is_coach = await is_user_coach(coach_id)

    text = f"👤 <b>{display_name}</b>\n\nВыберите действие:"

    await message.answer(
        text,
        reply_markup=get_student_detail_keyboard(student_id),
        parse_mode="HTML"
    )
    await message.answer(
        "Главное меню:",
        reply_markup=get_main_menu_keyboard(is_coach)
    )


@router.message(F.text == "❌ Отменить", CompetitionStates.waiting_for_comp_distance)
async def cancel_propose_comp_distance(message: Message, state: FSMContext):
    """Отмена на этапе ввода дистанции"""

    data = await state.get_data()
    if 'propose_student_id' not in data:
        return

    student_id = data.get('propose_student_id')
    await state.clear()

    # Редирект в меню ученика
    from coach.coach_keyboards import get_student_detail_keyboard
    from coach.coach_training_queries import get_student_display_name
    from bot.keyboards import get_main_menu_keyboard
    from coach.coach_queries import is_user_coach

    coach_id = message.from_user.id
    display_name = await get_student_display_name(coach_id, student_id)
    is_coach = await is_user_coach(coach_id)

    text = f"👤 <b>{display_name}</b>\n\nВыберите действие:"

    await message.answer(
        text,
        reply_markup=get_student_detail_keyboard(student_id),
        parse_mode="HTML"
    )
    await message.answer(
        "Главное меню:",
        reply_markup=get_main_menu_keyboard(is_coach)
    )


@router.message(F.text == "❌ Отменить", CompetitionStates.waiting_for_comp_target)
async def cancel_propose_comp_target(message: Message, state: FSMContext):
    """Отмена на этапе ввода целевого времени"""

    data = await state.get_data()
    if 'propose_student_id' not in data:
        return

    student_id = data.get('propose_student_id')
    await state.clear()

    # Редирект в меню ученика
    from coach.coach_keyboards import get_student_detail_keyboard
    from coach.coach_training_queries import get_student_display_name
    from bot.keyboards import get_main_menu_keyboard
    from coach.coach_queries import is_user_coach

    coach_id = message.from_user.id
    display_name = await get_student_display_name(coach_id, student_id)
    is_coach = await is_user_coach(coach_id)

    text = f"👤 <b>{display_name}</b>\n\nВыберите действие:"

    await message.answer(
        text,
        reply_markup=get_student_detail_keyboard(student_id),
        parse_mode="HTML"
    )
    await message.answer(
        "Главное меню:",
        reply_markup=get_main_menu_keyboard(is_coach)
    )


# ========== ПРЕДСТОЯЩИЕ СОРЕВНОВАНИЯ С ФИЛЬТРАМИ ==========

@router.callback_query(F.data.startswith("coach:comp_upcoming_main:"))
async def coach_show_upcoming_competitions_filters(callback: CallbackQuery, state: FSMContext):
    """Показать выбор города для фильтрации предстоящих соревнований"""

    student_id = int(callback.data.split(":")[2])
    coach_id = callback.from_user.id

    # Проверяем доступ
    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    display_name = await get_student_display_name(coach_id, student_id)

    # Сохраняем student_id в состоянии для всех последующих обработчиков
    await state.update_data(
        propose_student_id=student_id,
        coach_propose_mode=True  # Флаг что мы в режиме предложения от тренера
    )

    text = (
        f"📅 <b>ПРЕДСТОЯЩИЕ СОРЕВНОВАНИЯ</b>\n\n"
        f"Ученик: <b>{display_name}</b>\n\n"
        f"Выберите город:"
    )

    # Популярные города с короткими кодами для callback_data
    POPULAR_CITIES = [
        ("Москва", "msk"),
        ("Санкт-Петербург", "spb")
    ]

    builder = InlineKeyboardBuilder()
    for city_name, city_code in POPULAR_CITIES:
        builder.row(
            InlineKeyboardButton(text=city_name, callback_data=f"coach:comp_flt_city:{student_id}:{city_code}")
        )
    builder.row(
        InlineKeyboardButton(text="🌍 Все города", callback_data=f"coach:comp_flt_city:{student_id}:all")
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data=f"coach:competitions_menu:{student_id}")
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("coach:comp_flt_city:"))
async def coach_process_city_filter(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора города и переход к выбору периода"""

    parts = callback.data.split(":")
    student_id = int(parts[2])
    city_code = parts[3]
    coach_id = callback.from_user.id

    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    # Декодируем город из кода
    CITY_CODES = {
        "msk": "Москва",
        "spb": "Санкт-Петербург",
        "all": "Все города"
    }

    if city_code == "all":
        city = None
        city_display = "Все города"
    else:
        city_display = CITY_CODES.get(city_code, city_code)
        city = city_display

    await state.update_data(
        propose_student_id=student_id,
        coach_propose_mode=True,
        filter_city=city,
        filter_city_display=city_display,
        filter_city_code=city_code  # Сохраняем код для кнопки "Назад"
    )

    # Переходим к выбору периода
    display_name = await get_student_display_name(coach_id, student_id)

    text = (
        f"📅 <b>ПРЕДСТОЯЩИЕ СОРЕВНОВАНИЯ</b>\n\n"
        f"Ученик: <b>{display_name}</b>\n"
        f"📍 Город: <b>{city_display}</b>\n\n"
        f"Выберите период:"
    )

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📅 1 месяц", callback_data=f"coach:comp_flt_per:{student_id}:1"))
    builder.row(InlineKeyboardButton(text="📅 6 месяцев", callback_data=f"coach:comp_flt_per:{student_id}:6"))
    builder.row(InlineKeyboardButton(text="📅 1 год", callback_data=f"coach:comp_flt_per:{student_id}:12"))
    builder.row(InlineKeyboardButton(text="« Назад", callback_data=f"coach:comp_upcoming_main:{student_id}"))

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("coach:comp_flt_per:"))
async def coach_process_period_filter(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора периода и переход к выбору вида спорта"""

    parts = callback.data.split(":")
    student_id = int(parts[2])
    period_months = int(parts[3])
    coach_id = callback.from_user.id

    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    # Сохраняем выбранный период
    period_display = {
        1: "1 месяц",
        6: "6 месяцев",
        12: "1 год"
    }.get(period_months, f"{period_months} мес.")

    data = await state.get_data()
    city_display = data.get('filter_city_display', 'Все города')
    city_code = data.get('filter_city_code', 'all')

    await state.update_data(
        filter_period_months=period_months,
        filter_period_display=period_display
    )

    # Переходим к выбору вида спорта
    display_name = await get_student_display_name(coach_id, student_id)

    text = (
        f"📅 <b>ПРЕДСТОЯЩИЕ СОРЕВНОВАНИЯ</b>\n\n"
        f"Ученик: <b>{display_name}</b>\n"
        f"📍 Город: <b>{city_display}</b>\n"
        f"📅 Период: <b>{period_display}</b>\n\n"
        f"Выберите вид спорта:"
    )

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏃 Бег", callback_data=f"coach:comp_flt_spt:{student_id}:run"))
    builder.row(InlineKeyboardButton(text="🏊 Плавание", callback_data=f"coach:comp_flt_spt:{student_id}:swim"))
    builder.row(InlineKeyboardButton(text="🚴 Велоспорт", callback_data=f"coach:comp_flt_spt:{student_id}:bike"))
    builder.row(InlineKeyboardButton(text="🏊‍♂️🚴‍♂️🏃 Все виды", callback_data=f"coach:comp_flt_spt:{student_id}:all"))
    builder.row(InlineKeyboardButton(text="« Назад", callback_data=f"coach:comp_flt_city:{student_id}:{city_code}"))

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("coach:comp_flt_spt:"))
async def coach_process_sport_filter(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора спорта и переход к выбору сервиса"""

    parts = callback.data.split(":")
    student_id = int(parts[2])
    sport_code = parts[3]
    coach_id = callback.from_user.id

    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    # Сохраняем выбранный спорт
    sport_map = {
        "run": "Бег",
        "swim": "Плавание",
        "bike": "Велоспорт",
        "all": "Все виды"
    }
    sport_display = sport_map.get(sport_code, "Все виды")
    sport_filter = None if sport_code == "all" else sport_code

    data = await state.get_data()
    city_display = data.get('filter_city_display', 'Все города')
    period_display = data.get('filter_period_display', '1 месяц')

    await state.update_data(
        filter_sport=sport_filter,
        filter_sport_display=sport_display,
        filter_sport_code=sport_code  # Сохраняем код для кнопки "Назад"
    )

    # Переходим к выбору сервиса
    display_name = await get_student_display_name(coach_id, student_id)

    text = (
        f"📅 <b>ПРЕДСТОЯЩИЕ СОРЕВНОВАНИЯ</b>\n\n"
        f"Ученик: <b>{display_name}</b>\n"
        f"📍 Город: <b>{city_display}</b>\n"
        f"📅 Период: <b>{period_display}</b>\n"
        f"🏃 Спорт: <b>{sport_display}</b>\n\n"
        f"Выберите сервис для регистрации:"
    )

    builder = InlineKeyboardBuilder()

    # Добавляем сервисы
    for service_name, service_code in SERVICE_CODES.items():
        builder.row(
            InlineKeyboardButton(
                text=service_name,
                callback_data=f"coach:comp_flt_srv:{student_id}:{service_code}"
            )
        )

    builder.row(InlineKeyboardButton(text="« Назад", callback_data=f"coach:comp_flt_per:{student_id}:{data.get('filter_period_months', 1)}"))

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("coach:comp_flt_srv:"))
async def coach_show_filtered_competitions(callback: CallbackQuery, state: FSMContext):
    """Показать отфильтрованные соревнования после выбора сервиса"""

    parts = callback.data.split(":")
    student_id = int(parts[2])
    service_code = parts[3]  # Получаем сервис из callback
    coach_id = callback.from_user.id

    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    data = await state.get_data()
    city = data.get('filter_city')
    period_months = data.get('filter_period_months', 1)
    city_display = data.get('filter_city_display', 'Все города')
    period_display = data.get('filter_period_display', '1 месяц')

    # Получаем спорт из state (был сохранен на предыдущем шаге)
    sport_filter = data.get('filter_sport')
    sport_display = data.get('filter_sport_display', 'Все виды')

    # Декодируем сервис
    if service_code == "all":
        service = None
        service_display = "Все сервисы"
    else:
        service = service_code
        service_display = next(
            (name for name, code in SERVICE_CODES.items() if code == service_code),
            service_code
        )

    # Сохраняем выбранный сервис
    await state.update_data(
        filter_service=service,
        filter_service_display=service_display
    )

    display_name = await get_student_display_name(coach_id, student_id)

    # Показываем сообщение о загрузке
    loading_text = (
        f"🔍 <b>Поиск соревнований...</b>\n\n"
        f"Ученик: <b>{display_name}</b>\n"
        f"📍 Город: <b>{city_display}</b>\n"
        f"📅 Период: <b>{period_display}</b>\n"
        f"🏃 Спорт: <b>{sport_display}</b>\n"
        f"📋 Сервис: <b>{service_display}</b>"
    )

    try:
        await callback.message.edit_text(loading_text, parse_mode="HTML")
    except:
        pass

    # Получаем соревнования из API с правильными фильтрами
    try:
        logger.info(f"Coach fetching competitions: city={city}, sport={sport_filter}, period_months={period_months}, service={service}")

        competitions = await fetch_all_competitions(
            city=city,
            sport=sport_filter,
            limit=1000,
            period_months=period_months,
            service=service
        )

        logger.info(f"Coach received {len(competitions)} competitions after filtering")

    except Exception as e:
        logger.error(f"Error fetching competitions for coach: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при получении данных.\n"
            "Попробуйте позже.",
            parse_mode="HTML"
        )
        await callback.answer()
        return

    if not competitions:
        text = (
            f"😔 <b>Соревнования не найдены</b>\n\n"
            f"Ученик: <b>{display_name}</b>\n"
            f"📍 Город: <b>{city_display}</b>\n"
            f"📅 Период: <b>{period_display}</b>\n"
            f"🏃 Спорт: <b>{sport_display}</b>\n"
            f"📋 Сервис: <b>{service_display}</b>\n\n"
            f"Попробуйте изменить параметры фильтрации.\n\n"
            f"Также вы можете создать соревнование вручную через раздел \"🔍 Найти соревнование вручную\"."
        )
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="« Изменить фильтры", callback_data=f"coach:comp_upcoming_main:{student_id}"))
        builder.row(InlineKeyboardButton(text="🔍 Найти вручную", callback_data=f"coach:comp_manual:{student_id}"))
        builder.row(InlineKeyboardButton(text="« К меню", callback_data=f"coach:competitions_menu:{student_id}"))
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
        await callback.answer()
        return

    # Показываем результаты
    from utils.date_formatter import get_user_date_format, DateFormatter
    coach_date_format = await get_user_date_format(coach_id)

    text = (
        f"📅 <b>ПРЕДСТОЯЩИЕ СОРЕВНОВАНИЯ</b>\n\n"
        f"Ученик: <b>{display_name}</b>\n"
        f"📍 Город: <b>{city_display}</b>\n"
        f"📅 Период: <b>{period_display}</b>\n"
        f"🏃 Спорт: <b>{sport_display}</b>\n"
        f"📋 Сервис: <b>{service_display}</b>\n\n"
        f"Найдено соревнований: {len(competitions)}\n\n"
        f"Выберите соревнование для предложения ученику:"
    )

    builder = InlineKeyboardBuilder()

    type_emoji = {
        'бег': '🏃',
        'run': '🏃',
        'плавание': '🏊',
        'swim': '🏊',
        'велоспорт': '🚴',
        'bike': '🚴',
        'триатлон': '🏊‍♂️🚴‍♂️🏃',
        'triathlon': '🏊‍♂️🚴‍♂️🏃'
    }

    for comp in competitions[:20]:  # Показываем первые 20
        # Безопасный доступ к полям соревнования
        comp_name = comp.get('title') or comp.get('name', 'Без названия')
        comp_type = comp.get('sport_code') or comp.get('type', '')
        comp_id = comp.get('id', '')

        emoji = type_emoji.get(comp_type, '🏃')
        short_name = comp_name[:35] + '...' if len(comp_name) > 35 else comp_name

        builder.row(
            InlineKeyboardButton(
                text=f"{emoji} {short_name}",
                callback_data=f"coach:sel_comp:{student_id}:{comp_id}"
            )
        )

    builder.row(InlineKeyboardButton(text="« Изменить фильтры", callback_data=f"coach:comp_upcoming_main:{student_id}"))
    builder.row(InlineKeyboardButton(text="« К меню", callback_data=f"coach:competitions_menu:{student_id}"))

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()


# ========== ПРЕДЛОЖЕНИЕ ИЗ ПРЕДСТОЯЩИХ СОРЕВНОВАНИЙ (ПРОСТОЙ СПИСОК БЕЗ ФИЛЬТРОВ) ==========

@router.callback_query(F.data.startswith("coach:comp_upcoming:"))
async def coach_show_upcoming_competitions(callback: CallbackQuery, state: FSMContext):
    """Показать предстоящие соревнования для предложения ученику"""

    student_id = int(callback.data.split(":")[2])
    coach_id = callback.from_user.id

    # Проверяем доступ
    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    display_name = await get_student_display_name(coach_id, student_id)

    # Сохраняем student_id в состоянии
    await state.update_data(
        propose_student_id=student_id,
        coach_propose_mode=True
    )

    # Загружаем предстоящие соревнования из БД
    competitions = await get_upcoming_competitions(limit=50)

    if not competitions:
        text = (
            f"🏆 <b>ПРЕДЛОЖИТЬ СОРЕВНОВАНИЕ</b>\n\n"
            f"Ученик: <b>{display_name}</b>\n\n"
            f"📅 Предстоящих соревнований не найдено.\n\n"
            f"Вы можете создать соревнование вручную."
        )
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="🔍 Найти соревнование вручную",
                callback_data=f"coach:comp_manual:{student_id}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="« Назад",
                callback_data=f"coach:student:{student_id}"
            )
        )
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
        await callback.answer()
        return

    # Показываем список соревнований
    from utils.date_formatter import get_user_date_format, DateFormatter
    coach_date_format = await get_user_date_format(coach_id)

    text = (
        f"🏆 <b>ПРЕДЛОЖИТЬ СОРЕВНОВАНИЕ</b>\n\n"
        f"Ученик: <b>{display_name}</b>\n\n"
        f"📅 Выберите соревнование:"
    )

    builder = InlineKeyboardBuilder()

    type_emoji = {
        'бег': '🏃',
        'плавание': '🏊',
        'велоспорт': '🚴',
        'триатлон': '🏊‍♂️🚴‍♂️🏃',
        'трейл': '⛰️'
    }

    for comp in competitions[:20]:  # Показываем первые 20 соревнований
        emoji = type_emoji.get(comp.get('type', ''), '🏃')
        comp_date = DateFormatter.format_date(comp['date'], coach_date_format)
        # Короткое название для кнопки (30 символов)
        short_name = comp['name'][:30] + '...' if len(comp['name']) > 30 else comp['name']

        builder.row(
            InlineKeyboardButton(
                text=f"{emoji} {short_name}",
                callback_data=f"coach:sel_comp:{student_id}:{comp['id']}"
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="« Назад",
            callback_data=f"coach:propose_comp:{student_id}"
        )
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("coach:sel_comp:"))
async def coach_select_competition_for_student(callback: CallbackQuery, state: FSMContext):
    """Тренер выбрал соревнование для ученика - выбор дистанции"""

    parts = callback.data.split(":")
    student_id = int(parts[2])
    comp_id = int(parts[3])
    coach_id = callback.from_user.id

    # Проверяем доступ
    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    # Получаем соревнование
    competition = await get_competition(comp_id)
    if not competition:
        await callback.answer("Соревнование не найдено", show_alert=True)
        return

    display_name = await get_student_display_name(coach_id, student_id)

    # Парсим дистанции
    distances_json = competition.get('distances', '[]')
    try:
        distances = json.loads(distances_json) if isinstance(distances_json, str) else distances_json
    except:
        distances = []

    # Сохраняем данные соревнования в state
    await state.update_data(
        propose_student_id=student_id,
        coach_propose_mode=True,
        selected_comp_id=comp_id,
        comp_name=competition['name'],
        comp_date=competition['date'],
        comp_type=competition.get('type', 'бег')
    )

    from utils.date_formatter import get_user_date_format, DateFormatter
    coach_date_format = await get_user_date_format(coach_id)
    formatted_date = DateFormatter.format_date(competition['date'], coach_date_format)

    if len(distances) == 0:
        # Нет дистанций, просим ввести вручную
        text = (
            f"🏆 <b>ПРЕДЛОЖИТЬ СОРЕВНОВАНИЕ</b>\n\n"
            f"Ученик: <b>{display_name}</b>\n\n"
            f"📌 <b>{competition['name']}</b>\n"
            f"📅 {formatted_date}\n\n"
            f"Введите <b>дистанцию</b> (в км):\n"
            f"<i>Например: 42.195 или 10</i>"
        )
        await callback.message.edit_text(text, parse_mode="HTML")
        await state.set_state(CompetitionStates.waiting_for_comp_distance)
        await callback.answer()
        return

    if len(distances) == 1:
        # Одна дистанция, автоматически выбираем
        distance = distances[0]
        await state.update_data(comp_distance=distance)

        from competitions.competitions_utils import format_competition_distance
        formatted_distance = await format_competition_distance(distance, coach_id)

        text = (
            f"🏆 <b>ПРЕДЛОЖИТЬ СОРЕВНОВАНИЕ</b>\n\n"
            f"Ученик: <b>{display_name}</b>\n\n"
            f"📌 <b>{competition['name']}</b>\n"
            f"📅 {formatted_date}\n"
            f"📏 {formatted_distance}\n\n"
            f"Введите <b>рекомендуемое целевое время</b>:\n"
            f"<i>Формат: ЧЧ:ММ:СС или ММ:СС\n"
            f"Например: 03:30:00 или 45:00\n"
            f"Или отправьте <b>0</b> чтобы пропустить.</i>"
        )
        await callback.message.edit_text(text, parse_mode="HTML")
        await state.set_state(CompetitionStates.waiting_for_comp_target)
        await callback.answer()
        return

    # Несколько дистанций, показываем выбор
    text = (
        f"🏆 <b>ПРЕДЛОЖИТЬ СОРЕВНОВАНИЕ</b>\n\n"
        f"Ученик: <b>{display_name}</b>\n\n"
        f"📌 <b>{competition['name']}</b>\n"
        f"📅 {formatted_date}\n\n"
        f"Выберите дистанцию:"
    )

    builder = InlineKeyboardBuilder()
    from competitions.competitions_utils import format_competition_distance
    for dist in distances:
        formatted_dist = await format_competition_distance(dist, coach_id)
        builder.row(
            InlineKeyboardButton(
                text=formatted_dist,
                callback_data=f"coach:sel_dist:{student_id}:{comp_id}:{dist}"
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="« Назад",
            callback_data=f"coach:comp_upcoming:{student_id}"
        )
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("coach:sel_dist:"))
async def coach_select_distance_for_student(callback: CallbackQuery, state: FSMContext):
    """Тренер выбрал дистанцию для ученика - ввод целевого времени"""

    parts = callback.data.split(":")
    student_id = int(parts[2])
    comp_id = int(parts[3])
    distance = float(parts[4])
    coach_id = callback.from_user.id

    # Проверяем доступ
    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    display_name = await get_student_display_name(coach_id, student_id)

    # Обновляем данные в state
    data = await state.get_data()
    comp_name = data.get('comp_name')
    comp_date = data.get('comp_date')

    await state.update_data(comp_distance=distance)

    from utils.date_formatter import get_user_date_format, DateFormatter
    from competitions.competitions_utils import format_competition_distance

    coach_date_format = await get_user_date_format(coach_id)
    formatted_date = DateFormatter.format_date(comp_date, coach_date_format)
    formatted_distance = await format_competition_distance(distance, coach_id)

    text = (
        f"🏆 <b>ПРЕДЛОЖИТЬ СОРЕВНОВАНИЕ</b>\n\n"
        f"Ученик: <b>{display_name}</b>\n\n"
        f"📌 <b>{comp_name}</b>\n"
        f"📅 {formatted_date}\n"
        f"📏 {formatted_distance}\n\n"
        f"Введите <b>рекомендуемое целевое время</b>:\n"
        f"<i>Формат: ЧЧ:ММ:СС или ММ:СС\n"
        f"Например: 03:30:00 или 45:00\n"
        f"Или отправьте <b>0</b> чтобы пропустить.</i>"
    )

    await callback.message.edit_text(text, parse_mode="HTML")
    await state.set_state(CompetitionStates.waiting_for_comp_target)
    await callback.answer()


# Обработчик для ввода дистанции (когда нет дистанций в соревновании)
# используется существующий обработчик process_proposed_comp_distance

# Обработчик для ввода целевого времени (для предстоящих соревнований)
# используется существующий обработчик process_proposed_comp_target_and_send, но нужно его адаптировать


# ========== СОРЕВНОВАНИЯ УЧЕНИКА (АДАПТАЦИЯ "МОИ СОРЕВНОВАНИЯ" ДЛЯ ТРЕНЕРА) ==========

@router.callback_query(F.data.startswith("coach:student_competitions:"))
async def show_student_competitions(callback: CallbackQuery, state: FSMContext):
    """Показать соревнования ученика (адаптация раздела 'Мои соревнования')"""

    student_id = int(callback.data.split(":")[2])
    coach_id = callback.from_user.id

    # Проверяем доступ
    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    display_name = await get_student_display_name(coach_id, student_id)

    # Получаем соревнования ученика из БД
    from competitions.competitions_queries import get_user_competitions
    all_competitions = await get_user_competitions(student_id, status_filter='upcoming')

    if not all_competitions:
        text = (
            f"📋 <b>СОРЕВНОВАНИЯ УЧЕНИКА</b>\n\n"
            f"Ученик: <b>{display_name}</b>\n\n"
            f"У ученика пока нет запланированных соревнований.\n\n"
            f"Вы можете предложить ему соревнование."
        )

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="🏆 Предложить соревнование",
                callback_data=f"coach:comp_upcoming_main:{student_id}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="« Назад",
                callback_data=f"coach:competitions_menu:{student_id}"
            )
        )

        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    # Показываем соревнования
    from utils.date_formatter import get_user_date_format
    from competitions.competitions_utils import format_competition_distance as format_dist_with_units, format_competition_date
    from competitions.competitions_keyboards import format_time_until_competition
    from database.queries import get_user_settings
    from utils.unit_converter import safe_convert_distance_name

    # Получаем настройки ТРЕНЕРА для отображения
    coach_date_format = await get_user_date_format(coach_id)
    coach_settings = await get_user_settings(coach_id)
    distance_unit = coach_settings.get('distance_unit', 'км') if coach_settings else 'км'

    text = f"📋 <b>СОРЕВНОВАНИЯ УЧЕНИКА</b>\n\n"
    text += f"Ученик: <b>{display_name}</b>\n\n"

    # Показываем соревнования (максимум 15)
    for i, comp in enumerate(all_competitions[:15], 1):
        time_until = format_time_until_competition(comp['date'])

        # Получаем название дистанции
        distance_value = comp.get('distance', 0)
        distance_name = comp.get('distance_name')

        # Нормализуем distance_name
        if distance_name and isinstance(distance_name, str):
            distance_name = distance_name.strip()
            if distance_name.lower() in ('none', 'null', '0', '0.0', ''):
                distance_name = None

        # Если distance_name нет, ищем в массиве distances
        if not distance_name and comp.get('distances') and isinstance(comp['distances'], list):
            for dist_obj in comp['distances']:
                if isinstance(dist_obj, dict):
                    if dist_obj.get('distance') == distance_value:
                        distance_name = dist_obj.get('name', '')
                        break

            # Если не нашли по значению и distance_value = 0, берем первую дистанцию
            if not distance_name and (distance_value == 0 or distance_value is None):
                for dist_obj in comp['distances']:
                    if isinstance(dist_obj, dict):
                        distance_name = dist_obj.get('name', '')
                        distance_value = dist_obj.get('distance', 0)
                        break

        # Форматируем дистанцию
        if distance_name:
            import re
            if re.match(r'^\d+(\.\d+)?$', distance_name):
                dist_str = f"{distance_name} {distance_unit}"
            else:
                dist_str = safe_convert_distance_name(distance_name, distance_unit)
        elif distance_value is not None and distance_value > 0:
            dist_str = await format_dist_with_units(distance_value, coach_id)
        else:
            dist_str = "Не указана"

        # Форматируем дату с учетом настроек тренера
        date_str = await format_competition_date(comp['date'], coach_id)

        # Форматируем целевое время
        target_time = comp.get('target_time')
        if target_time is None or target_time == 'None' or target_time == '':
            target_time_str = 'Нет цели'
            target_pace_str = ''
        else:
            target_time_str = target_time
            # Рассчитываем темп для целевого времени
            from utils.time_formatter import calculate_pace_with_unit
            target_pace = await calculate_pace_with_unit(target_time, comp['distance'], coach_id)
            target_pace_str = f" ({target_pace})" if target_pace else ''

        # Отметка если предложено тренером
        proposal_mark = ""
        if comp.get('proposed_by_coach'):
            proposal_status = comp.get('proposal_status', 'pending')
            if proposal_status == 'pending':
                proposal_mark = " ⏳"  # Ожидает решения
            elif proposal_status == 'accepted':
                proposal_mark = " ✅"  # Принято
            elif proposal_status == 'rejected':
                proposal_mark = " ❌"  # Отклонено

        text += (
            f"{i}. <b>{comp['name']}</b>{proposal_mark}\n"
            f"   📏 {dist_str}\n"
            f"   📅 {date_str} ({time_until})\n"
            f"   🎯 Цель: {target_time_str}{target_pace_str}\n\n"
        )

    builder = InlineKeyboardBuilder()

    # Кнопки для просмотра деталей соревнований
    for comp in all_competitions[:15]:
        # Короткое название для кнопки
        short_name = comp['name'][:30] + '...' if len(comp['name']) > 30 else comp['name']
        builder.row(
            InlineKeyboardButton(
                text=f"📋 {short_name}",
                callback_data=f"coach:view_student_comp:{student_id}:{comp['id']}"
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="« Назад",
            callback_data=f"coach:competitions_menu:{student_id}"
        )
    )

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("coach:view_student_comp:"))
async def view_student_competition_details(callback: CallbackQuery):
    """Показать детали соревнования ученика (только чтение)"""

    parts = callback.data.split(":")
    student_id = int(parts[2])
    competition_id = int(parts[3])
    coach_id = callback.from_user.id

    # Проверяем доступ
    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    display_name = await get_student_display_name(coach_id, student_id)

    # Получаем информацию о соревновании
    from competitions.competitions_queries import get_competition, get_user_competition_registration

    comp = await get_competition(competition_id)
    if not comp:
        await callback.answer("Соревнование не найдено", show_alert=True)
        return

    # Получаем регистрацию ученика на это соревнование
    registration = await get_user_competition_registration(student_id, competition_id)
    if not registration:
        await callback.answer("Регистрация не найдена", show_alert=True)
        return

    # Форматируем информацию
    from utils.date_formatter import get_user_date_format, DateFormatter
    from competitions.competitions_utils import format_competition_distance as format_dist_with_units
    from competitions.competitions_keyboards import format_time_until_competition
    from datetime import datetime

    coach_date_format = await get_user_date_format(coach_id)

    # Форматируем дату
    comp_date = datetime.strptime(comp['date'], '%Y-%m-%d')
    date_str = DateFormatter.format_date(comp['date'], coach_date_format)
    time_until = format_time_until_competition(comp['date'])

    # Форматируем дистанцию
    distance_value = registration.get('distance', 0)
    distance_name = registration.get('distance_name')

    if distance_name:
        from utils.unit_converter import safe_convert_distance_name
        from database.queries import get_user_settings
        coach_settings = await get_user_settings(coach_id)
        distance_unit = coach_settings.get('distance_unit', 'км') if coach_settings else 'км'
        dist_str = safe_convert_distance_name(distance_name, distance_unit)
    elif distance_value > 0:
        dist_str = await format_dist_with_units(distance_value, coach_id)
    else:
        dist_str = "Не указана"

    # Статус предложения
    proposal_status_text = ""
    if registration.get('proposed_by_coach'):
        proposal_status = registration.get('proposal_status', 'pending')
        if proposal_status == 'pending':
            proposal_status_text = "\n\n⏳ Статус: Ожидает решения ученика"
        elif proposal_status == 'accepted':
            proposal_status_text = "\n\n✅ Статус: Принято учеником"
        elif proposal_status == 'rejected':
            proposal_status_text = "\n\n❌ Статус: Отклонено учеником"

    # Формируем текст
    text = (
        f"📋 <b>ДЕТАЛИ СОРЕВНОВАНИЯ</b>\n\n"
        f"Ученик: <b>{display_name}</b>\n\n"
        f"🏆 <b>{comp['name']}</b>\n"
        f"{'=' * 40}\n\n"
        f"📅 Дата: {date_str}\n"
        f"⏳ {time_until}\n"
        f"📍 Место: {comp.get('city', 'Не указано')}\n"
        f"📏 Дистанция: {dist_str}\n\n"
    )

    # Целевое время
    target_time = registration.get('target_time')
    if target_time:
        text += f"🎯 Целевое время: {target_time}\n"
        # Рассчитываем темп
        from utils.time_formatter import calculate_pace_with_unit
        target_pace = await calculate_pace_with_unit(target_time, registration['distance'], coach_id)
        if target_pace:
            text += f"   Темп: {target_pace}\n"
    else:
        text += f"🎯 Целевое время: Не установлено\n"

    # Результат
    result = registration.get('result')
    if result:
        text += f"\n✅ Результат: {result}\n"
        # Рассчитываем темп результата
        from utils.time_formatter import calculate_pace_with_unit
        result_pace = await calculate_pace_with_unit(result, registration['distance'], coach_id)
        if result_pace:
            text += f"   Темп: {result_pace}\n"

        # Квалификация
        qualification = registration.get('qualification')
        if qualification:
            text += f"🏅 Квалификация: {qualification}\n"
    else:
        text += f"\n📊 Результат: Еще не добавлен\n"

    text += proposal_status_text

    # Если есть официальный сайт
    builder = InlineKeyboardBuilder()

    if comp.get('official_url'):
        builder.row(
            InlineKeyboardButton(
                text="🌐 Официальный сайт",
                url=comp['official_url']
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="« К списку",
            callback_data=f"coach:student_competitions:{student_id}"
        )
    )

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("accept_coach_comp:"))
async def accept_coach_competition_proposal(callback: CallbackQuery):
    """Ученик принимает предложение соревнования от тренера"""
    try:
        parts = callback.data.split(":")
        comp_id = int(parts[1])
        coach_id = int(parts[2])
    except (IndexError, ValueError) as e:
        logger.error(f"Error parsing accept callback: {callback.data}, error: {e}")
        await callback.answer("❌ Ошибка формата данных", show_alert=True)
        return

    student_id = callback.from_user.id

    import aiosqlite
    import os
    DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

    try:
        async with aiosqlite.connect(DB_PATH) as db:
            # Обновляем статус предложения
            await db.execute(
                """
                UPDATE competition_participants
                SET proposal_status = 'accepted'
                WHERE user_id = ? AND competition_id = ? AND proposed_by_coach_id = ?
                """,
                (student_id, comp_id, coach_id)
            )
            await db.commit()

        # Получаем имя ученика из настроек (не юзернейм!)
        from database.queries import get_user_settings
        student_settings = await get_user_settings(student_id)
        student_name = student_settings.get('name') if student_settings else None

        if not student_name:
            # Если имени нет, пробуем получить из users
            from database.queries import get_user
            student = await get_user(student_id)
            student_name = student.get('name') or student.get('username') or 'Ученик'

        # Уведомляем тренера с редиректом в главное меню
        from coach.coach_queries import is_user_coach
        coach_is_coach = await is_user_coach(coach_id)

        await callback.bot.send_message(
            coach_id,
            f"✅ <b>Предложение принято!</b>\n\n"
            f"<b>{student_name}</b> принял ваше предложение участвовать в соревновании.",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard(coach_is_coach)
        )

        # Обновляем сообщение ученику с редиректом в "Мои соревнования"
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="📋 Мои соревнования", callback_data="comp:my")
        )

        await callback.message.edit_text(
            f"{callback.message.text}\n\n"
            f"✅ <b>Вы приняли предложение!</b>\n"
            f"Соревнование добавлено в раздел «Мои соревнования».",
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
        await callback.answer("✅ Предложение принято!", show_alert=True)

    except Exception as e:
        logger.error(f"Error accepting competition proposal: {e}")
        await callback.answer("❌ Ошибка при принятии предложения", show_alert=True)


@router.callback_query(F.data.startswith("reject_coach_comp:"))
async def reject_coach_competition_proposal(callback: CallbackQuery):
    """Ученик отклоняет предложение соревнования от тренера"""
    try:
        parts = callback.data.split(":")
        comp_id = int(parts[1])
        coach_id = int(parts[2])
    except (IndexError, ValueError) as e:
        logger.error(f"Error parsing reject callback: {callback.data}, error: {e}")
        await callback.answer("❌ Ошибка формата данных", show_alert=True)
        return

    student_id = callback.from_user.id

    import aiosqlite
    import os
    DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

    try:
        async with aiosqlite.connect(DB_PATH) as db:
            # Обновляем статус предложения
            await db.execute(
                """
                UPDATE competition_participants
                SET proposal_status = 'rejected'
                WHERE user_id = ? AND competition_id = ? AND proposed_by_coach_id = ?
                """,
                (student_id, comp_id, coach_id)
            )
            await db.commit()

        # Получаем имя ученика из настроек (не юзернейм!)
        from database.queries import get_user_settings
        student_settings = await get_user_settings(student_id)
        student_name = student_settings.get('name') if student_settings else None

        if not student_name:
            # Если имени нет, пробуем получить из users
            from database.queries import get_user
            student = await get_user(student_id)
            student_name = student.get('name') or student.get('username') or 'Ученик'

        # Уведомляем тренера с редиректом в главное меню
        from coach.coach_queries import is_user_coach
        coach_is_coach = await is_user_coach(coach_id)

        await callback.bot.send_message(
            coach_id,
            f"❌ <b>Предложение отклонено</b>\n\n"
            f"<b>{student_name}</b> отклонил ваше предложение участвовать в соревновании.",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard(coach_is_coach)
        )

        # Обновляем сообщение ученику - редактируем текст без клавиатуры
        await callback.message.edit_text(
            f"{callback.message.text}\n\n"
            f"❌ <b>Вы отклонили предложение</b>",
            parse_mode="HTML"
        )

        # Отправляем новое сообщение с главным меню
        from coach.coach_queries import is_user_coach
        student_is_coach = await is_user_coach(student_id)

        await callback.message.answer(
            "Вы в главном меню",
            reply_markup=get_main_menu_keyboard(student_is_coach)
        )
        await callback.answer("Предложение отклонено", show_alert=True)

    except Exception as e:
        logger.error(f"Error rejecting competition proposal: {e}")
        await callback.answer("❌ Ошибка при отклонении предложения", show_alert=True)
