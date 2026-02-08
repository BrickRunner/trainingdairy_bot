"""
Обработчики для предложения соревнований от тренера ученику
"""

import logging
import json
from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.fsm import CompetitionStates, CoachStates
from bot.keyboards import get_main_menu_keyboard, get_cancel_keyboard
from coach.coach_training_queries import can_coach_access_student, get_student_display_name
from competitions.competitions_queries import add_competition, get_competition, get_upcoming_competitions
from competitions.competitions_fetcher import fetch_all_competitions, SERVICE_CODES
from database.queries import get_user

logger = logging.getLogger(__name__)
router = Router()


def is_coach_propose_flow():
    """Фильтр: проверяет что это предложение соревнования от тренера"""
    async def check(message: Message, state: FSMContext) -> bool:
        data = await state.get_data()
        return 'propose_student_id' in data
    return check



@router.callback_query(F.data.startswith("coach:competitions_menu:"))
async def show_coach_competitions_menu(callback: CallbackQuery, state: FSMContext):
    """Главное меню раздела 'Соревнования' для тренера"""

    student_id = int(callback.data.split(":")[2])
    coach_id = callback.from_user.id

    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    display_name = await get_student_display_name(coach_id, student_id)

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



@router.callback_query(F.data.startswith("coach:propose_comp:"))
async def start_propose_competition(callback: CallbackQuery, state: FSMContext):
    """Редирект старой кнопки на новое меню соревнований"""

    student_id = int(callback.data.split(":")[2])
    coach_id = callback.from_user.id

    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await show_coach_competitions_menu(callback, state)


@router.callback_query(F.data.startswith("coach:comp_manual:"))
async def coach_propose_manual_competition(callback: CallbackQuery, state: FSMContext):
    """Начать процесс ручного создания соревнования для ученика"""

    student_id = int(callback.data.split(":")[2])
    coach_id = callback.from_user.id

    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    display_name = await get_student_display_name(coach_id, student_id)

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

    display_name = await get_student_display_name(coach_id, student_id)

    text = (
        f"🏆 <b>СОРЕВНОВАНИЯ</b>\n\n"
        f"Ученик: <b>{display_name}</b>\n\n"
        f"Выберите раздел:"
    )

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

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
    await callback.answer("❌ Отменено")


@router.message(CompetitionStates.waiting_for_comp_name)
async def process_proposed_comp_name(message: Message, state: FSMContext):
    """Обработать название предложенного соревнования"""

    data = await state.get_data()
    if 'propose_student_id' not in data:
        return

    comp_name = message.text.strip()

    if not comp_name or len(comp_name) < 3:
        await message.answer(
            "❌ Название слишком короткое. Введите название минимум из 3 символов."
        )
        return

    await state.update_data(comp_name=comp_name)

    student_id = data.get('propose_student_id')
    coach_id = message.from_user.id

    from utils.date_formatter import get_user_date_format
    coach_date_format = await get_user_date_format(coach_id)

    if coach_date_format == 'ММ/ДД/ГГГГ':
        format_example = "ММ/ДД/ГГГГ"
        date_example = "09/25/2026"
    elif coach_date_format == 'ГГГГ-ММ-ДД':
        format_example = "ГГГГ-ММ-ДД"
        date_example = "2026-09-25"
    else:  
        format_example = "ДД.ММ.ГГГГ"
        date_example = "25.09.2026"

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
        f"📅 Выберите дату соревнования из календаря:"
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=calendar_markup)
    await state.set_state(CompetitionStates.waiting_for_comp_date)
    await callback.answer()


@router.callback_query(F.data.startswith("coach_comp_cal_"), CompetitionStates.waiting_for_comp_date)
async def process_calendar_selection(callback: CallbackQuery, state: FSMContext):
    """Обработать выбор даты из календаря"""
    from bot.calendar_keyboard import CalendarKeyboard
    from datetime import date

    logger.info(f"Calendar callback received: {callback.data}")

    parsed = CalendarKeyboard.parse_callback_data(callback.data, prefix="coach_comp_cal")

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

    data = await state.get_data()
    logger.info(f"FSM state data: {data}")

    if 'propose_student_id' not in data:
        logger.warning("No propose_student_id in state data, ignoring callback")
        await callback.answer("❌ Сессия истекла. Начните заново.", show_alert=True)
        return

    student_id = data.get('propose_student_id')

    if parsed.get('action') == 'select' and parsed.get('format') == 1:
        selected_date = parsed.get('date')

        if not selected_date:
            await callback.answer("❌ Ошибка при выборе даты", show_alert=True)
            return

        if selected_date.date() < date.today():
            await callback.answer("❌ Выберите дату в будущем", show_alert=True)
            return

        await state.update_data(comp_date=selected_date.strftime('%Y-%m-%d'))

        from aiogram.types import InlineKeyboardButton
        from aiogram.utils.keyboard import InlineKeyboardBuilder

        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🏃 Бег", callback_data="comptype:running"))
        builder.row(InlineKeyboardButton(text="🏊 Плавание", callback_data="comptype:swimming"))
        builder.row(InlineKeyboardButton(text="🚴 Велоспорт", callback_data="comptype:cycling"))

        from utils.date_formatter import get_user_date_format, DateFormatter
        coach_id = callback.from_user.id
        user_date_format = await get_user_date_format(coach_id)
        formatted_date = DateFormatter.format_date(selected_date.strftime('%Y-%m-%d'), user_date_format)

        comp_name = data.get('comp_name', '')

        text = (
            f"✅ Название: <b>{comp_name}</b>\n"
            f"✅ Дата: <b>{formatted_date}</b>\n\n"
            f"Выберите <b>вид спорта</b>:"
        )

        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
        await state.set_state(CompetitionStates.waiting_for_comp_type)
        await callback.answer()
    else:
        await callback.answer()


@router.message(CompetitionStates.waiting_for_comp_date)
async def process_proposed_comp_date(message: Message, state: FSMContext):
    """Обработать дату предложенного соревнования (ручной ввод)"""

    data = await state.get_data()
    if 'propose_student_id' not in data:
        return

    from datetime import date
    from utils.date_formatter import get_user_date_format

    date_text = message.text.strip()
    coach_id = message.from_user.id
    student_id = data.get('propose_student_id')

    coach_date_format = await get_user_date_format(coach_id)

    comp_date = None
    for fmt in ['%d.%m.%Y', '%m/%d/%Y', '%Y-%m-%d']:
        try:
            comp_date = datetime.strptime(date_text, fmt).date()
            break
        except ValueError:
            continue

    if not comp_date:
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

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏃 Бег", callback_data="comptype:running"))
    builder.row(InlineKeyboardButton(text="🏊 Плавание", callback_data="comptype:swimming"))
    builder.row(InlineKeyboardButton(text="🚴 Велоспорт", callback_data="comptype:cycling"))

    from utils.date_formatter import DateFormatter
    formatted_date = DateFormatter.format_date(comp_date.strftime('%Y-%m-%d'), coach_date_format)

    comp_name = data.get('comp_name', '')

    text = (
        f"✅ Название: <b>{comp_name}</b>\n"
        f"✅ Дата: <b>{formatted_date}</b>\n\n"
        f"Выберите <b>вид спорта</b>:"
    )

    await message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await state.set_state(CompetitionStates.waiting_for_comp_type)


@router.callback_query(F.data.startswith("comptype:"), CompetitionStates.waiting_for_comp_type)
async def process_proposed_comp_type(callback: CallbackQuery, state: FSMContext):
    """Обработать тип предложенного соревнования"""

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

    student_id = data.get('propose_student_id')
    from database.queries import get_user_settings

    coach_settings = await get_user_settings(callback.from_user.id)
    distance_unit = coach_settings.get('distance_unit', 'км') if coach_settings else 'км'

    if distance_unit == 'миль':
        unit_text = "милях"
    else:
        unit_text = "километрах"

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    comp_name = data.get('comp_name', '')
    comp_date = data.get('comp_date', '')

    from utils.date_formatter import get_user_date_format, DateFormatter
    coach_date_format = await get_user_date_format(callback.from_user.id)
    formatted_date = DateFormatter.format_date(comp_date, coach_date_format)

    text = (
        f"✅ Название: <b>{comp_name}</b>\n"
        f"✅ Дата: <b>{formatted_date}</b>\n"
        f"✅ Вид спорта: <b>{comp_type.capitalize()}</b>\n\n"
        f"Введите <b>дистанцию в {unit_text}</b>:\n"
        f"<i>Например:\n"
        f"• 42.195\n"
        f"• 21.1\n"
        f"• 10</i>"
    )

    await callback.message.edit_text(text, parse_mode="HTML")
    await state.set_state(CompetitionStates.waiting_for_comp_distance)
    await callback.answer()


@router.message(CompetitionStates.waiting_for_comp_distance)
async def process_proposed_comp_distance(message: Message, state: FSMContext):
    """Обработать дистанцию предложенного соревнования и перейти к вводу целевого времени"""

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

    student_id = data.get('propose_student_id')
    comp_name = data.get('comp_name')
    comp_date = data.get('comp_date')
    comp_type = data.get('comp_type')
    coach_id = message.from_user.id

    from utils.date_formatter import get_user_date_format, DateFormatter
    from competitions.competitions_utils import format_competition_distance

    coach_date_format = await get_user_date_format(coach_id)
    formatted_date = DateFormatter.format_date(comp_date, coach_date_format)
    formatted_distance = await format_competition_distance(distance, coach_id)

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="⏭ Пропустить",
            callback_data=f"coach:skip_target:{student_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Отменить",
            callback_data=f"coach:cancel_propose_comp:{student_id}"
        )
    )

    text = (
        f"✅ Название: <b>{comp_name}</b>\n"
        f"✅ Дата: <b>{formatted_date}</b>\n"
        f"✅ Вид спорта: <b>{comp_type.capitalize()}</b>\n"
        f"✅ Дистанция: <b>{formatted_distance}</b>\n\n"
        f"Введите <b>рекомендуемое целевое время</b> для ученика:\n"
        f"<i>Формат: ЧЧ:ММ:СС или ММ:СС\n"
        f"Например: 03:30:00 или 45:00</i>\n\n"
        f"Или нажмите <b>Пропустить</b>, чтобы не устанавливать целевое время."
    )

    await message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await state.set_state(CompetitionStates.waiting_for_comp_target)


@router.callback_query(F.data.startswith("coach:skip_target:"))
async def coach_skip_target_time(callback: CallbackQuery, state: FSMContext):
    """Тренер пропускает ввод целевого времени"""
    data = await state.get_data()
    if 'propose_student_id' not in data:
        await callback.answer("Ошибка: данные не найдены", show_alert=True)
        return

    coach_id = callback.from_user.id

    await process_proposed_comp_target_and_send_internal(
        callback.message,
        state,
        target_time=None,
        from_callback=True,
        coach_id=coach_id
    )
    await callback.answer()


async def process_proposed_comp_target_and_send_internal(message: Message, state: FSMContext, target_time: str = None, from_callback: bool = False, coach_id: int = None):
    """Внутренняя функция для отправки предложения ученику с целевым временем"""
    data = await state.get_data()
    if 'propose_student_id' not in data:
        return

    student_id = data.get('propose_student_id')
    comp_name = data.get('comp_name')
    comp_date = data.get('comp_date')
    comp_type = data.get('comp_type')
    comp_distance = data.get('comp_distance')
    selected_comp_id = data.get('selected_comp_id')  

    if coach_id is None:
        coach_id = message.from_user.id if hasattr(message, 'from_user') else message.chat.id

    try:
        if selected_comp_id:
            comp_id = selected_comp_id
        else:
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

        import aiosqlite
        import os
        DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                """
                SELECT id FROM competition_participants
                WHERE user_id = ? AND competition_id = ? AND distance = ?
                AND (distance_name IS NULL OR distance_name = '')
                """,
                (student_id, comp_id, comp_distance)
            ) as cursor:
                existing = await cursor.fetchone()

            logger.info(f"Checking existing record: student_id={student_id}, comp_id={comp_id}, distance={comp_distance}, existing={existing}")

            if existing:
                logger.info(f"Updating existing record (id={existing[0]})")
                cursor = await db.execute(
                    """
                    UPDATE competition_participants
                    SET target_time = ?, proposal_status = 'pending',
                        proposed_by_coach = 1, proposed_by_coach_id = ?, reminders_enabled = 0
                    WHERE user_id = ? AND competition_id = ? AND distance = ?
                    AND (distance_name IS NULL OR distance_name = '')
                    """,
                    (target_time, coach_id, student_id, comp_id, comp_distance)
                )
                logger.info(f"Updated {cursor.rowcount} rows with target_time={target_time}")
            else:
                logger.info(f"Inserting new record: student_id={student_id}, comp_id={comp_id}, distance={comp_distance}, target_time={target_time}, coach_id={coach_id}")
                cursor = await db.execute(
                    """
                    INSERT INTO competition_participants
                    (user_id, competition_id, distance, distance_name, target_time,
                     proposed_by_coach, proposed_by_coach_id, proposal_status, reminders_enabled)
                    VALUES (?, ?, ?, NULL, ?, 1, ?, 'pending', 0)
                    """,
                    (student_id, comp_id, comp_distance, target_time, coach_id)
                )
                logger.info(f"Inserted new record with ID={cursor.lastrowid}")
            await db.commit()
            logger.info(f"Database commit successful")

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

        coach = await get_user(coach_id)
        coach_name = coach.get('name') or coach.get('username') or 'Ваш тренер'

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

        coach_date_format = await get_user_date_format(coach_id)
        coach_formatted_date = DateFormatter.format_date(comp_date, coach_date_format)
        coach_formatted_distance = await format_competition_distance(comp_distance, coach_id)

        text = (
            "✅ <b>Предложение отправлено!</b>\n\n"
            f"Ученик <b>{student_display_name}</b> получил уведомление о соревновании:\n\n"
            f"🏆 <b>{comp_name}</b>\n"
            f"📅 {coach_formatted_date}\n"
            f"📏 {coach_formatted_distance}\n"
        )

        if target_time:
            text += f"🎯 Целевое время: {target_time}\n"

        text += "\nВы получите уведомление, когда ученик примет решение."

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text=f"« К ученику {student_display_name}",
                callback_data=f"coach:student:{student_id}"
            )
        )

        if from_callback:
            await message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
        else:
            await message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())

        await state.clear()

    except Exception as e:
        logger.error(f"Error proposing competition: {e}")
        if from_callback:
            await message.answer(
                "❌ Произошла ошибка при отправке предложения.\n"
                "Попробуйте ещё раз позже."
            )
        else:
            await message.answer(
                "❌ Произошла ошибка при отправке предложения.\n"
                "Попробуйте ещё раз позже."
            )
        await state.clear()


@router.message(CompetitionStates.waiting_for_comp_target)
async def process_proposed_comp_target_and_send(message: Message, state: FSMContext):
    """Обработать целевое время и отправить предложение ученику"""

    data = await state.get_data()
    if 'propose_student_id' not in data:
        return

    target_text = message.text.strip()
    target_time = None

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
        student_id = data.get('propose_student_id')

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="⏭ Пропустить",
                callback_data=f"coach:skip_target:{student_id}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="❌ Отменить",
                callback_data=f"coach:cancel_propose_comp:{student_id}"
            )
        )

        await message.answer(
            "❌ Неверный формат времени.\n"
            "Используйте формат: ЧЧ:ММ:СС или ММ:СС\n"
            "Примеры: 03:30:00 или 45:00\n\n"
            "Или нажмите <b>Пропустить</b>, чтобы не устанавливать целевое время.",
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
        return

    coach_id = message.from_user.id
    await process_proposed_comp_target_and_send_internal(message, state, target_time=target_time, from_callback=False, coach_id=coach_id)



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



@router.callback_query(F.data.startswith("coach:comp_upcoming_main:"))
async def coach_show_upcoming_competitions_filters(callback: CallbackQuery, state: FSMContext):
    """Показать выбор города для фильтрации предстоящих соревнований"""

    student_id = int(callback.data.split(":")[2])
    coach_id = callback.from_user.id

    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    display_name = await get_student_display_name(coach_id, student_id)

    await state.update_data(
        propose_student_id=student_id,
        coach_propose_mode=True  
    )

    text = (
        f"📅 <b>ПРЕДСТОЯЩИЕ СОРЕВНОВАНИЯ</b>\n\n"
        f"Ученик: <b>{display_name}</b>\n\n"
        f"Выберите город:"
    )

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
        filter_city_code=city_code  
    )

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
        filter_sport_code=sport_code  
    )

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
    service_code = parts[3]  
    coach_id = callback.from_user.id

    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    data = await state.get_data()
    city = data.get('filter_city')
    period_months = data.get('filter_period_months', 1)
    city_display = data.get('filter_city_display', 'Все города')
    period_display = data.get('filter_period_display', '1 месяц')

    sport_filter = data.get('filter_sport')
    sport_display = data.get('filter_sport_display', 'Все виды')

    if service_code == "all":
        service = None
        service_display = "Все сервисы"
    else:
        service = service_code
        service_display = next(
            (name for name, code in SERVICE_CODES.items() if code == service_code),
            service_code
        )

    await state.update_data(
        filter_service=service,
        filter_service_display=service_display
    )

    display_name = await get_student_display_name(coach_id, student_id)

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

        from database.queries import is_user_registered_all_distances, get_user_participant_competition_urls

        participant_urls = await get_user_participant_competition_urls(student_id)
        logger.info(f"Student is participant in {len(participant_urls)} competitions")

        filtered_competitions = []
        for comp in competitions:
            comp_url = comp.get('url', '')
            distances = comp.get('distances', [])
            distances_count = len(distances)
            sport_code = comp.get('sport_code', '')

            if not comp_url:
                filtered_competitions.append(comp)
                continue

            if distances_count <= 1:
                if sport_code == "camp":
                    if comp_url not in participant_urls:
                        filtered_competitions.append(comp)
                    else:
                        logger.info(f"Hiding competition (camp, registered): {comp.get('title', 'Unknown')}")
                else:
                    filtered_competitions.append(comp)
            else:
                is_all_registered = await is_user_registered_all_distances(student_id, comp_url, distances_count)
                if not is_all_registered:
                    filtered_competitions.append(comp)
                else:
                    logger.info(f"Hiding competition (all distances registered): {comp.get('title', 'Unknown')}")

        competitions = filtered_competitions
        logger.info(f"After filtering participant competitions: {len(competitions)} competitions")

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

    from competitions.competitions_queries import get_or_create_competition_from_api

    competitions_with_db_ids = []
    for comp in competitions[:20]:  
        try:
            db_id = await get_or_create_competition_from_api(comp)
            comp['db_id'] = db_id
            competitions_with_db_ids.append(comp)
        except Exception as e:
            logger.error(f"Error saving competition to DB: {e}, comp: {comp.get('title', 'unknown')}")
            continue

    from utils.date_formatter import get_user_date_format, DateFormatter
    from database.queries import get_user_settings
    from utils.unit_converter import safe_convert_distance_name

    coach_date_format = await get_user_date_format(coach_id)

    coach_settings = await get_user_settings(coach_id)
    distance_unit = coach_settings.get('distance_unit', 'км') if coach_settings else 'км'

    text = (
        f"📅 <b>ПРЕДСТОЯЩИЕ СОРЕВНОВАНИЯ</b>\n\n"
        f"Ученик: <b>{display_name}</b>\n"
        f"📍 Город: <b>{city_display}</b>\n"
        f"📅 Период: <b>{period_display}</b>\n"
        f"🏃 Спорт: <b>{sport_display}</b>\n"
        f"📋 Сервис: <b>{service_display}</b>\n\n"
        f"Найдено соревнований: {len(competitions_with_db_ids)}\n\n"
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

    for comp in competitions_with_db_ids:
        comp_name = comp.get('title') or comp.get('name', 'Без названия')
        comp_type = comp.get('sport_code') or comp.get('type', '')
        comp_db_id = comp.get('db_id')  

        comp_date_raw = comp.get('date') or comp.get('begin_date', '')
        try:
            if comp_date_raw:
                if 'T' in comp_date_raw:
                    date_obj = datetime.fromisoformat(comp_date_raw.replace('Z', '+00:00'))
                    date_str = DateFormatter.format_date(date_obj, coach_date_format)
                else:
                    date_str = DateFormatter.format_date(comp_date_raw, coach_date_format)
            else:
                date_str = ""
        except:
            date_str = ""

        emoji = type_emoji.get(comp_type, '🏃')

        distances_str = ""
        distances = comp.get('distances', [])
        if distances:
            converted_distances = []
            for dist in distances[:3]:
                if isinstance(dist, dict):
                    distance_name = dist.get('name', str(dist.get('distance', '')))
                else:
                    distance_name = str(dist)

                if distance_name:
                    converted_name = safe_convert_distance_name(distance_name, distance_unit)
                    converted_distances.append(converted_name)

            if converted_distances:
                distances_str = f" ({', '.join(converted_distances)})"
                if len(distances) > 3:
                    distances_str = distances_str[:-1] + f", +{len(distances)-3})"

        if date_str:
            max_name_len = 25 if distances_str else 30
            short_name = comp_name[:max_name_len] + '...' if len(comp_name) > max_name_len else comp_name
            button_text = f"{date_str} | {short_name}{distances_str}"
        else:
            max_name_len = 30 if distances_str else 35
            short_name = comp_name[:max_name_len] + '...' if len(comp_name) > max_name_len else comp_name
            button_text = f"{emoji} {short_name}{distances_str}"

        builder.row(
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"coach:sel_comp:{student_id}:{comp_db_id}"
            )
        )

    builder.row(InlineKeyboardButton(text="« Изменить фильтры", callback_data=f"coach:comp_upcoming_main:{student_id}"))
    builder.row(InlineKeyboardButton(text="« К меню", callback_data=f"coach:competitions_menu:{student_id}"))

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()



@router.callback_query(F.data.startswith("coach:comp_upcoming:"))
async def coach_show_upcoming_competitions(callback: CallbackQuery, state: FSMContext):
    """Показать предстоящие соревнования для предложения ученику"""

    student_id = int(callback.data.split(":")[2])
    coach_id = callback.from_user.id

    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    display_name = await get_student_display_name(coach_id, student_id)

    await state.update_data(
        propose_student_id=student_id,
        coach_propose_mode=True
    )

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

    for comp in competitions[:20]:  
        emoji = type_emoji.get(comp.get('type', ''), '🏃')
        comp_date = DateFormatter.format_date(comp['date'], coach_date_format)
        short_name = comp['name'][:25] + '...' if len(comp['name']) > 25 else comp['name']

        button_text = f"{comp_date} | {short_name}"

        builder.row(
            InlineKeyboardButton(
                text=button_text,
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

    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    competition = await get_competition(comp_id)
    if not competition:
        await callback.answer("Соревнование не найдено", show_alert=True)
        return

    display_name = await get_student_display_name(coach_id, student_id)

    distances_json = competition.get('distances', '[]')
    try:
        distances = json.loads(distances_json) if isinstance(distances_json, str) else distances_json
    except:
        distances = []

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

        from database.queries import get_user_settings
        coach_settings = await get_user_settings(coach_id)
        distance_unit = coach_settings.get('distance_unit', 'км') if coach_settings else 'км'

        if distance_unit == 'миль':
            examples = "26.2 или 6.2"
        else:
            examples = "42.195 или 10"

        text = (
            f"🏆 <b>ПРЕДЛОЖИТЬ СОРЕВНОВАНИЕ</b>\n\n"
            f"Ученик: <b>{display_name}</b>\n\n"
            f"📌 <b>{competition['name']}</b>\n"
            f"📅 {formatted_date}\n\n"
            f"Введите <b>дистанцию</b> (в {distance_unit}):\n"
            f"<i>Например: {examples}</i>"
        )

        await callback.message.edit_text(text, parse_mode="HTML")
        await state.set_state(CompetitionStates.waiting_for_comp_distance)
        await callback.answer()
        return

    if len(distances) == 1:
        distance = distances[0]
        await state.update_data(comp_distance=distance)

        from database.queries import get_user_settings
        from utils.unit_converter import safe_convert_distance_name
        from competitions.competitions_utils import format_competition_distance

        if isinstance(distance, dict):
            distance_km = distance.get('distance', 0)
            distance_name = distance.get('name', str(distance_km))
        else:
            distance_km = float(distance) if distance else 0
            distance_name = str(distance)

        coach_settings = await get_user_settings(coach_id)
        distance_unit = coach_settings.get('distance_unit', 'км') if coach_settings else 'км'

        if distance_name and (not distance_name.replace('.', '').replace(',', '').isdigit()):
            formatted_distance = safe_convert_distance_name(distance_name, distance_unit)
        else:
            formatted_distance = await format_competition_distance(distance_km, coach_id)

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="⏭ Пропустить",
                callback_data=f"coach:skip_target:{student_id}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="❌ Отменить",
                callback_data=f"coach:cancel_propose_comp:{student_id}"
            )
        )

        text = (
            f"🏆 <b>ПРЕДЛОЖИТЬ СОРЕВНОВАНИЕ</b>\n\n"
            f"Ученик: <b>{display_name}</b>\n\n"
            f"📌 <b>{competition['name']}</b>\n"
            f"📅 {formatted_date}\n"
            f"📏 {formatted_distance}\n\n"
            f"Введите <b>рекомендуемое целевое время</b> для ученика:\n"
            f"<i>Формат: ЧЧ:ММ:СС или ММ:СС\n"
            f"Например: 03:30:00 или 45:00</i>\n\n"
            f"Или нажмите <b>Пропустить</b>, чтобы не устанавливать целевое время."
        )
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
        await state.set_state(CompetitionStates.waiting_for_comp_target)
        await callback.answer()
        return


    from database.queries import get_user_registered_distances
    comp_url = competition.get('url', str(comp_id))
    registered_indices = await get_user_registered_distances(student_id, comp_url, distances)

    await state.update_data(
        coach_selected_distances=[],
        coach_all_distances=distances,
        coach_registered_distances=registered_indices
    )

    text = (
        f"🏆 <b>ПРЕДЛОЖИТЬ СОРЕВНОВАНИЕ</b>\n\n"
        f"Ученик: <b>{display_name}</b>\n\n"
        f"📌 <b>{competition['name']}</b>\n"
        f"📅 {formatted_date}\n\n"
    )

    if registered_indices:
        text += "🔒 Ученик уже зарегистрирован на некоторые дистанции (отмечены замком).\n"
        text += "Выберите дополнительные дистанции для предложения.\n\n"
    else:
        text += "Выберите дистанции (можно несколько):\n"

    builder = InlineKeyboardBuilder()

    from database.queries import get_user_settings
    from utils.unit_converter import safe_convert_distance_name

    coach_settings = await get_user_settings(coach_id)
    distance_unit = coach_settings.get('distance_unit', 'км') if coach_settings else 'км'

    for i, dist in enumerate(distances[:15]):  
        if isinstance(dist, dict):
            distance_km = dist.get('distance', 0)
            distance_name = dist.get('name', 'Дистанция')
        else:
            distance_km = float(dist)
            distance_name = str(dist)

        converted_name = safe_convert_distance_name(distance_name, distance_unit)

        if i in registered_indices:
            button_text = f"🔒 {converted_name} (зарегистрирован)"
            callback_data = f"coach:already_registered:{student_id}:{i}"
        else:
            button_text = f"☐ {converted_name}"
            callback_data = f"coach:toggle_dist:{student_id}:{comp_id}:{i}"

        builder.row(InlineKeyboardButton(
            text=button_text,
            callback_data=callback_data
        ))

    builder.row(InlineKeyboardButton(
        text="✅ Продолжить",
        callback_data=f"coach:confirm_distances:{student_id}:{comp_id}"
    ))

    builder.row(
        InlineKeyboardButton(
            text="« Назад",
            callback_data=f"coach:comp_upcoming_main:{student_id}"
        )
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("coach:toggle_dist:"))
async def coach_toggle_distance_selection(callback: CallbackQuery, state: FSMContext):
    """Переключить выбор дистанции (чекбокс) - копия из главного раздела"""
    try:
        parts = callback.data.split(":")
        student_id = int(parts[2])
        comp_id = int(parts[3])
        distance_idx = int(parts[4])
        coach_id = callback.from_user.id

        if not await can_coach_access_student(coach_id, student_id):
            await callback.answer("Нет доступа", show_alert=True)
            return

        data = await state.get_data()
        selected_distances = data.get('coach_selected_distances', [])
        all_distances = data.get('coach_all_distances', [])
        registered_distances = data.get('coach_registered_distances', [])

        if distance_idx in registered_distances:
            await callback.answer(
                "🔒 Ученик уже зарегистрирован на эту дистанцию. "
                "Её нельзя удалить или добавить повторно.",
                show_alert=True
            )
            return

        if distance_idx in selected_distances:
            selected_distances.remove(distance_idx)
        else:
            selected_distances.append(distance_idx)

        await state.update_data(coach_selected_distances=selected_distances)

        from database.queries import get_user_settings
        from utils.unit_converter import safe_convert_distance_name

        coach_settings = await get_user_settings(coach_id)
        distance_unit = coach_settings.get('distance_unit', 'км') if coach_settings else 'км'

        builder = InlineKeyboardBuilder()

        for i, dist in enumerate(all_distances[:15]):
            if isinstance(dist, dict):
                distance_km = dist.get('distance', 0)
                distance_name = dist.get('name', 'Дистанция')
            else:
                distance_km = float(dist)
                distance_name = str(dist)

            converted_name = safe_convert_distance_name(distance_name, distance_unit)

            if i in registered_distances:
                button_text = f"🔒 {converted_name} (зарегистрирован)"
                callback_data = f"coach:already_registered:{student_id}:{i}"
            else:
                checkbox = "✓" if i in selected_distances else "☐"
                button_text = f"{checkbox} {converted_name}"
                callback_data = f"coach:toggle_dist:{student_id}:{comp_id}:{i}"

            builder.row(InlineKeyboardButton(
                text=button_text,
                callback_data=callback_data
            ))

        builder.row(InlineKeyboardButton(
            text="✅ Продолжить",
            callback_data=f"coach:confirm_distances:{student_id}:{comp_id}"
        ))

        builder.row(InlineKeyboardButton(
            text="« Назад",
            callback_data=f"coach:comp_upcoming_main:{student_id}"
        ))

        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
        await callback.answer()

    except Exception as e:
        logger.error(f"Error toggling distance for coach: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("coach:already_registered:"))
async def coach_already_registered_distance(callback: CallbackQuery, state: FSMContext):
    """Обработка нажатия на уже зарегистрированную дистанцию ученика"""
    await callback.answer(
        "⚠️ Ученик уже зарегистрирован на эту дистанцию.\n"
        "Невозможно предложить её повторно.",
        show_alert=True
    )


@router.callback_query(F.data.startswith("coach:confirm_distances:"))
async def coach_confirm_distances_selection(callback: CallbackQuery, state: FSMContext):
    """Подтвердить выбор дистанций и начать последовательный ввод целевого времени - копия из главного раздела"""
    try:
        parts = callback.data.split(":")
        student_id = int(parts[2])
        comp_id = int(parts[3])
        coach_id = callback.from_user.id

        if not await can_coach_access_student(coach_id, student_id):
            await callback.answer("Нет доступа", show_alert=True)
            return

        data = await state.get_data()
        selected_distances = data.get('coach_selected_distances', [])
        all_distances = data.get('coach_all_distances', [])

        if not selected_distances:
            await callback.answer("⚠️ Выберите хотя бы одну дистанцию", show_alert=True)
            return

        distances_to_process = []
        for idx in selected_distances:
            if idx < len(all_distances):
                dist = all_distances[idx]

                if isinstance(dist, dict):
                    distance_km = dist.get('distance', 0)
                    distance_name = dist.get('name', str(distance_km))
                else:
                    distance_km = float(dist)
                    distance_name = str(dist)

                distances_to_process.append({
                    'distance': distance_km,
                    'name': distance_name
                })

        await state.update_data(
            coach_distances_to_process=distances_to_process,
            coach_current_distance_idx=0,
            coach_distance_times=[]  
        )

        await coach_prompt_for_next_distance_target(callback, state, student_id)

    except Exception as e:
        logger.error(f"Error confirming distances for coach: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


async def coach_prompt_for_next_distance_target(callback: CallbackQuery, state: FSMContext, student_id: int):
    """Запросить целевое время для следующей дистанции"""
    data = await state.get_data()
    distances_to_process = data.get('coach_distances_to_process', [])
    current_idx = data.get('coach_current_distance_idx', 0)
    coach_id = callback.from_user.id

    if current_idx >= len(distances_to_process):
        await coach_send_all_distance_proposals(callback, state, student_id)
        return

    current_dist = distances_to_process[current_idx]
    display_name = await get_student_display_name(coach_id, student_id)

    comp_name = data.get('comp_name')
    comp_date = data.get('comp_date')

    from utils.date_formatter import get_user_date_format, DateFormatter
    from utils.unit_converter import safe_convert_distance_name
    from database.queries import get_user_settings

    coach_settings = await get_user_settings(coach_id)
    distance_unit = coach_settings.get('distance_unit', 'км') if coach_settings else 'км'

    coach_date_format = await get_user_date_format(coach_id)
    formatted_date = DateFormatter.format_date(comp_date, coach_date_format)
    formatted_distance = safe_convert_distance_name(current_dist['name'], distance_unit)

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="⏭ Пропустить эту дистанцию",
        callback_data=f"coach:skip_dist_target:{student_id}:{current_idx}"
    ))
    builder.row(InlineKeyboardButton(
        text="❌ Отменить",
        callback_data=f"coach:cancel_propose_comp:{student_id}"
    ))

    text = (
        f"🏆 <b>ПРЕДЛОЖИТЬ СОРЕВНОВАНИЕ</b>\n\n"
        f"Ученик: <b>{display_name}</b>\n\n"
        f"📌 <b>{comp_name}</b>\n"
        f"📅 {formatted_date}\n"
        f"📏 {formatted_distance}\n\n"
        f"<b>Дистанция {current_idx + 1} из {len(distances_to_process)}</b>\n\n"
        f"Введите <b>рекомендуемое целевое время</b> для этой дистанции:\n"
        f"<i>Формат: ЧЧ:ММ:СС или ММ:СС\n"
        f"Например: 03:30:00 или 45:00</i>\n\n"
        f"Или нажмите <b>Пропустить</b>, чтобы не устанавливать целевое время для этой дистанции."
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await state.set_state(CompetitionStates.waiting_for_coach_multi_target)
    await callback.answer()


@router.callback_query(F.data.startswith("coach:skip_dist_target:"))
async def coach_skip_distance_target(callback: CallbackQuery, state: FSMContext):
    """Пропустить ввод целевого времени для текущей дистанции"""
    parts = callback.data.split(":")
    student_id = int(parts[2])

    data = await state.get_data()
    distance_times = data.get('coach_distance_times', [])
    distance_times.append(None)

    current_idx = data.get('coach_current_distance_idx', 0)
    await state.update_data(
        coach_distance_times=distance_times,
        coach_current_distance_idx=current_idx + 1
    )

    await coach_prompt_for_next_distance_target(callback, state, student_id)


async def coach_send_all_distance_proposals(callback: CallbackQuery, state: FSMContext, student_id: int):
    """Отправить предложения для всех выбранных дистанций (КАЖДАЯ ДИСТАНЦИЯ ОТДЕЛЬНЫМ СООБЩЕНИЕМ)"""
    data = await state.get_data()
    distances_to_process = data.get('coach_distances_to_process', [])
    distance_times = data.get('coach_distance_times', [])
    comp_id = data.get('selected_comp_id')
    comp_name = data.get('comp_name')
    comp_date = data.get('comp_date')
    comp_type = data.get('comp_type')
    coach_id = callback.from_user.id

    try:
        import aiosqlite
        import os
        DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

        from database.queries import get_user_settings, get_user
        coach_settings = await get_user_settings(coach_id)
        coach_name = coach_settings.get('name') if coach_settings else None

        if not coach_name:
            coach = await get_user(coach_id)
            coach_name = coach.get('name') or coach.get('username') or 'Ваш тренер'

        student_display_name = await get_student_display_name(coach_id, student_id)

        from utils.date_formatter import get_user_date_format, DateFormatter
        from utils.unit_converter import safe_convert_distance_name

        student_settings = await get_user_settings(student_id)
        student_distance_unit = student_settings.get('distance_unit', 'км') if student_settings else 'км'
        student_date_format = await get_user_date_format(student_id)
        formatted_date = DateFormatter.format_date(comp_date, student_date_format)

        sent_count = 0
        for i, dist_info in enumerate(distances_to_process):
            distance = dist_info['distance']
            target_time = distance_times[i] if i < len(distance_times) else None

            async with aiosqlite.connect(DB_PATH) as db:
                async with db.execute(
                    """
                    SELECT id FROM competition_participants
                    WHERE user_id = ? AND competition_id = ? AND distance = ? AND distance_name = ?
                    """,
                    (student_id, comp_id, distance, dist_info['name'])
                ) as cursor:
                    existing = await cursor.fetchone()

                if existing:
                    await db.execute(
                        """
                        UPDATE competition_participants
                        SET target_time = ?, proposal_status = 'pending',
                            proposed_by_coach = 1, proposed_by_coach_id = ?, reminders_enabled = 0
                        WHERE user_id = ? AND competition_id = ? AND distance = ? AND distance_name = ?
                        """,
                        (target_time, coach_id, student_id, comp_id, distance, dist_info['name'])
                    )
                else:
                    await db.execute(
                        """
                        INSERT INTO competition_participants
                        (user_id, competition_id, distance, distance_name, target_time,
                         proposed_by_coach, proposed_by_coach_id, proposal_status, reminders_enabled)
                        VALUES (?, ?, ?, ?, ?, 1, ?, 'pending', 0)
                        """,
                        (student_id, comp_id, distance, dist_info['name'], target_time, coach_id)
                    )
                await db.commit()

            formatted_dist = safe_convert_distance_name(dist_info['name'], student_distance_unit)

            if student_distance_unit == 'мили' and 'миль' not in formatted_dist and 'миля' not in formatted_dist and 'ярд' not in formatted_dist:
                formatted_dist = f"{formatted_dist} (мили)"
            elif student_distance_unit == 'км' and 'км' not in formatted_dist and 'м' not in formatted_dist:
                formatted_dist = f"{formatted_dist} км"

            notification_text = (
                f"🏆 <b>ПРЕДЛОЖЕНИЕ ОТ ТРЕНЕРА</b>\n\n"
                f"<b>{coach_name}</b> предлагает вам участие в соревновании:\n\n"
                f"📌 <b>{comp_name}</b>\n"
                f"📅 Дата: {formatted_date}\n"
                f"🏃 Вид: {comp_type}\n"
                f"📏 Дистанция: <b>{formatted_dist}</b>\n"
            )

            if target_time:
                notification_text += f"⏱ Целевое время: <b>{target_time}</b>\n"

            notification_text += "\n<b>Что вы решите?</b>"

            builder = InlineKeyboardBuilder()

            dist_name_encoded = dist_info['name'][:30]  

            builder.row(InlineKeyboardButton(
                text="✅ Принять",
                callback_data=f"accept_coach_dist:{comp_id}:{coach_id}:{i}"
            ))
            builder.row(InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=f"reject_coach_dist:{comp_id}:{coach_id}:{i}"
            ))

            await callback.bot.send_message(
                student_id,
                notification_text,
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
            sent_count += 1

        coach_date_format = await get_user_date_format(coach_id)
        coach_formatted_date = DateFormatter.format_date(comp_date, coach_date_format)

        coach_settings = await get_user_settings(coach_id)
        coach_distance_unit = coach_settings.get('distance_unit', 'км') if coach_settings else 'км'

        distances_text_coach = ""
        for i, dist_info in enumerate(distances_to_process):
            formatted_dist = safe_convert_distance_name(dist_info['name'], coach_distance_unit)
            target_time = distance_times[i] if i < len(distance_times) else None

            distances_text_coach += f"  📏 {formatted_dist}"
            if target_time:
                distances_text_coach += f" (цель: {target_time})"
            distances_text_coach += "\n"

        text = (
            "✅ <b>Предложения отправлены!</b>\n\n"
            f"Ученик <b>{student_display_name}</b> получил {sent_count} предложений о соревновании:\n\n"
            f"🏆 <b>{comp_name}</b>\n"
            f"📅 {coach_formatted_date}\n\n"
            f"<b>Дистанции:</b>\n{distances_text_coach}\n"
            f"Каждая дистанция отправлена отдельным сообщением.\n"
            f"Вы получите уведомление, когда ученик примет решение по каждой из них."
        )

        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text=f"« К ученику {student_display_name}",
            callback_data=f"coach:student:{student_id}"
        ))

        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
        await state.clear()

    except Exception as e:
        logger.error(f"Error sending multi-distance proposals: {e}")
        await callback.message.answer(
            "❌ Произошла ошибка при отправке предложения.\n"
            "Попробуйте ещё раз позже."
        )
        await state.clear()


@router.message(CompetitionStates.waiting_for_coach_multi_target)
async def coach_process_multi_distance_target(message: Message, state: FSMContext):
    """Обработать целевое время для текущей дистанции (множественный выбор)"""
    data = await state.get_data()
    if 'propose_student_id' not in data:
        return

    student_id = data.get('propose_student_id')
    target_text = message.text.strip()
    target_time = None

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
        current_idx = data.get('coach_current_distance_idx', 0)

        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="⏭ Пропустить эту дистанцию",
            callback_data=f"coach:skip_dist_target:{student_id}:{current_idx}"
        ))
        builder.row(InlineKeyboardButton(
            text="❌ Отменить",
            callback_data=f"coach:cancel_propose_comp:{student_id}"
        ))

        await message.answer(
            "❌ Неверный формат времени.\n"
            "Используйте формат: ЧЧ:ММ:СС или ММ:СС\n"
            "Примеры: 03:30:00 или 45:00\n\n"
            "Или нажмите <b>Пропустить</b>, чтобы не устанавливать целевое время для этой дистанции.",
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
        return

    distance_times = data.get('coach_distance_times', [])
    distance_times.append(target_time)

    current_idx = data.get('coach_current_distance_idx', 0)
    await state.update_data(
        coach_distance_times=distance_times,
        coach_current_distance_idx=current_idx + 1
    )

    from aiogram.types import CallbackQuery as FakeCallback

    await coach_prompt_for_next_distance_target_via_message(message, state, student_id)


async def coach_prompt_for_next_distance_target_via_message(message: Message, state: FSMContext, student_id: int):
    """Запросить целевое время для следующей дистанции (вызов из message handler)"""
    data = await state.get_data()
    distances_to_process = data.get('coach_distances_to_process', [])
    current_idx = data.get('coach_current_distance_idx', 0)
    coach_id = message.from_user.id

    if current_idx >= len(distances_to_process):
        await coach_send_all_distance_proposals_via_message(message, state, student_id)
        return

    current_dist = distances_to_process[current_idx]
    display_name = await get_student_display_name(coach_id, student_id)

    comp_name = data.get('comp_name')
    comp_date = data.get('comp_date')

    from utils.date_formatter import get_user_date_format, DateFormatter
    from utils.unit_converter import safe_convert_distance_name
    from database.queries import get_user_settings

    coach_settings = await get_user_settings(coach_id)
    distance_unit = coach_settings.get('distance_unit', 'км') if coach_settings else 'км'

    coach_date_format = await get_user_date_format(coach_id)
    formatted_date = DateFormatter.format_date(comp_date, coach_date_format)
    formatted_distance = safe_convert_distance_name(current_dist['name'], distance_unit)

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="⏭ Пропустить эту дистанцию",
        callback_data=f"coach:skip_dist_target:{student_id}:{current_idx}"
    ))
    builder.row(InlineKeyboardButton(
        text="❌ Отменить",
        callback_data=f"coach:cancel_propose_comp:{student_id}"
    ))

    text = (
        f"🏆 <b>ПРЕДЛОЖИТЬ СОРЕВНОВАНИЕ</b>\n\n"
        f"Ученик: <b>{display_name}</b>\n\n"
        f"📌 <b>{comp_name}</b>\n"
        f"📅 {formatted_date}\n"
        f"📏 {formatted_distance}\n\n"
        f"<b>Дистанция {current_idx + 1} из {len(distances_to_process)}</b>\n\n"
        f"Введите <b>рекомендуемое целевое время</b> для этой дистанции:\n"
        f"<i>Формат: ЧЧ:ММ:СС или ММ:СС\n"
        f"Например: 03:30:00 или 45:00</i>\n\n"
        f"Или нажмите <b>Пропустить</b>, чтобы не устанавливать целевое время для этой дистанции."
    )

    await message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())


async def coach_send_all_distance_proposals_via_message(message: Message, state: FSMContext, student_id: int):
    """Отправить предложения для всех выбранных дистанций (КАЖДАЯ ДИСТАНЦИЯ ОТДЕЛЬНЫМ СООБЩЕНИЕМ, вызов из message handler)"""
    data = await state.get_data()
    distances_to_process = data.get('coach_distances_to_process', [])
    distance_times = data.get('coach_distance_times', [])
    comp_id = data.get('selected_comp_id')
    comp_name = data.get('comp_name')
    comp_date = data.get('comp_date')
    comp_type = data.get('comp_type')
    coach_id = message.from_user.id

    try:
        import aiosqlite
        import os
        DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

        from database.queries import get_user_settings, get_user
        coach_settings = await get_user_settings(coach_id)
        coach_name = coach_settings.get('name') if coach_settings else None

        if not coach_name:
            coach = await get_user(coach_id)
            coach_name = coach.get('name') or coach.get('username') or 'Ваш тренер'

        student_display_name = await get_student_display_name(coach_id, student_id)

        from utils.date_formatter import get_user_date_format, DateFormatter
        from utils.unit_converter import safe_convert_distance_name

        student_settings = await get_user_settings(student_id)
        student_distance_unit = student_settings.get('distance_unit', 'км') if student_settings else 'км'
        student_date_format = await get_user_date_format(student_id)
        formatted_date = DateFormatter.format_date(comp_date, student_date_format)

        sent_count = 0
        for i, dist_info in enumerate(distances_to_process):
            distance = dist_info['distance']
            target_time = distance_times[i] if i < len(distance_times) else None

            async with aiosqlite.connect(DB_PATH) as db:
                async with db.execute(
                    """
                    SELECT id FROM competition_participants
                    WHERE user_id = ? AND competition_id = ? AND distance = ? AND distance_name = ?
                    """,
                    (student_id, comp_id, distance, dist_info['name'])
                ) as cursor:
                    existing = await cursor.fetchone()

                if existing:
                    await db.execute(
                        """
                        UPDATE competition_participants
                        SET target_time = ?, proposal_status = 'pending',
                            proposed_by_coach = 1, proposed_by_coach_id = ?, reminders_enabled = 0
                        WHERE user_id = ? AND competition_id = ? AND distance = ? AND distance_name = ?
                        """,
                        (target_time, coach_id, student_id, comp_id, distance, dist_info['name'])
                    )
                else:
                    await db.execute(
                        """
                        INSERT INTO competition_participants
                        (user_id, competition_id, distance, distance_name, target_time,
                         proposed_by_coach, proposed_by_coach_id, proposal_status, reminders_enabled)
                        VALUES (?, ?, ?, ?, ?, 1, ?, 'pending', 0)
                        """,
                        (student_id, comp_id, distance, dist_info['name'], target_time, coach_id)
                    )
                await db.commit()

            formatted_dist = safe_convert_distance_name(dist_info['name'], student_distance_unit)

            if student_distance_unit == 'мили' and 'миль' not in formatted_dist and 'миля' not in formatted_dist and 'ярд' not in formatted_dist:
                formatted_dist = f"{formatted_dist} (мили)"
            elif student_distance_unit == 'км' and 'км' not in formatted_dist and 'м' not in formatted_dist:
                formatted_dist = f"{formatted_dist} км"

            notification_text = (
                f"🏆 <b>ПРЕДЛОЖЕНИЕ ОТ ТРЕНЕРА</b>\n\n"
                f"<b>{coach_name}</b> предлагает вам участие в соревновании:\n\n"
                f"📌 <b>{comp_name}</b>\n"
                f"📅 Дата: {formatted_date}\n"
                f"🏃 Вид: {comp_type}\n"
                f"📏 Дистанция: <b>{formatted_dist}</b>\n"
            )

            if target_time:
                notification_text += f"⏱ Целевое время: <b>{target_time}</b>\n"

            notification_text += "\n<b>Что вы решите?</b>"

            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(
                text="✅ Принять",
                callback_data=f"accept_coach_dist:{comp_id}:{coach_id}:{i}"
            ))
            builder.row(InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=f"reject_coach_dist:{comp_id}:{coach_id}:{i}"
            ))

            await message.bot.send_message(
                student_id,
                notification_text,
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
            sent_count += 1

        coach_date_format = await get_user_date_format(coach_id)
        coach_formatted_date = DateFormatter.format_date(comp_date, coach_date_format)

        coach_settings = await get_user_settings(coach_id)
        coach_distance_unit = coach_settings.get('distance_unit', 'км') if coach_settings else 'км'

        distances_text_coach = ""
        for i, dist_info in enumerate(distances_to_process):
            formatted_dist = safe_convert_distance_name(dist_info['name'], coach_distance_unit)
            target_time = distance_times[i] if i < len(distance_times) else None

            distances_text_coach += f"  📏 {formatted_dist}"
            if target_time:
                distances_text_coach += f" (цель: {target_time})"
            distances_text_coach += "\n"

        text = (
            "✅ <b>Предложения отправлены!</b>\n\n"
            f"Ученик <b>{student_display_name}</b> получил {sent_count} предложений о соревновании:\n\n"
            f"🏆 <b>{comp_name}</b>\n"
            f"📅 {coach_formatted_date}\n\n"
            f"<b>Дистанции:</b>\n{distances_text_coach}\n"
            f"Каждая дистанция отправлена отдельным сообщением.\n"
            f"Вы получите уведомление, когда ученик примет решение по каждой из них."
        )

        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text=f"« К ученику {student_display_name}",
            callback_data=f"coach:student:{student_id}"
        ))

        await message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())
        await state.clear()

    except Exception as e:
        logger.error(f"Error sending multi-distance proposals: {e}")
        await message.answer(
            "❌ Произошла ошибка при отправке предложения.\n"
            "Попробуйте ещё раз позже."
        )
        await state.clear()






@router.callback_query(F.data.startswith("coach:student_competitions:"))
async def show_student_competitions(callback: CallbackQuery, state: FSMContext):
    """Показать соревнования ученика (адаптация раздела 'Мои соревнования')"""

    parts = callback.data.split(":")
    student_id = int(parts[2])
    page = int(parts[3]) if len(parts) > 3 else 1
    coach_id = callback.from_user.id

    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    display_name = await get_student_display_name(coach_id, student_id)

    from competitions.competitions_queries import get_user_competitions
    all_competitions = await get_user_competitions(student_id, status_filter='upcoming')

    ITEMS_PER_PAGE = 10
    total_pages = (len(all_competitions) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE if all_competitions else 1
    page = max(1, min(page, total_pages))  

    start_idx = (page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    competitions = all_competitions[start_idx:end_idx]

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

    from utils.date_formatter import get_user_date_format
    from competitions.competitions_utils import format_competition_distance as format_dist_with_units, format_competition_date
    from competitions.competitions_keyboards import format_time_until_competition
    from database.queries import get_user_settings
    from utils.unit_converter import safe_convert_distance_name

    coach_date_format = await get_user_date_format(coach_id)
    coach_settings = await get_user_settings(coach_id)
    distance_unit = coach_settings.get('distance_unit', 'км') if coach_settings else 'км'

    if total_pages > 1:
        text = f"📋 <b>СОРЕВНОВАНИЯ УЧЕНИКА</b> (стр. {page}/{total_pages})\n\n"
    else:
        text = f"📋 <b>СОРЕВНОВАНИЯ УЧЕНИКА</b>\n\n"
    text += f"Ученик: <b>{display_name}</b>\n\n"

    for i, comp in enumerate(competitions, start_idx + 1):
        time_until = format_time_until_competition(comp['date'])

        distance_value = comp.get('distance', 0)
        distance_name = comp.get('distance_name')

        if distance_name and isinstance(distance_name, str):
            distance_name = distance_name.strip()
            if distance_name.lower() in ('none', 'null', '0', '0.0', ''):
                distance_name = None

        if not distance_name and comp.get('distances') and isinstance(comp['distances'], list):
            for dist_obj in comp['distances']:
                if isinstance(dist_obj, dict):
                    if dist_obj.get('distance') == distance_value:
                        distance_name = dist_obj.get('name', '')
                        break

            if not distance_name and (distance_value == 0 or distance_value is None):
                for dist_obj in comp['distances']:
                    if isinstance(dist_obj, dict):
                        distance_name = dist_obj.get('name', '')
                        distance_value = dist_obj.get('distance', 0)
                        break

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

        date_str = await format_competition_date(comp['date'], coach_id)

        target_time = comp.get('target_time')
        if target_time is None or target_time == 'None' or target_time == '':
            target_time_str = 'Нет цели'
            target_pace_str = ''
        else:
            target_time_str = target_time
            from utils.time_formatter import calculate_pace_with_unit
            target_pace = await calculate_pace_with_unit(target_time, comp['distance'], coach_id)
            target_pace_str = f" ({target_pace})" if target_pace else ''

        proposal_mark = ""
        if comp.get('proposed_by_coach'):
            proposal_status = comp.get('proposal_status', 'pending')
            if proposal_status == 'pending':
                proposal_mark = " ⏳"  
            elif proposal_status == 'accepted':
                proposal_mark = " ✅"  
            elif proposal_status == 'rejected':
                proposal_mark = " ❌"  

        text += (
            f"{i}. <b>{comp['name']}</b>{proposal_mark}\n"
            f"   📏 {dist_str}\n"
            f"   📅 {date_str} ({time_until})\n"
            f"   🎯 Цель: {target_time_str}{target_pace_str}\n\n"
        )

    builder = InlineKeyboardBuilder()

    for comp in competitions:
        distance_for_callback = comp.get('distance') or 0
        builder.row(
            InlineKeyboardButton(
                text=f"{comp['name'][:40]}..." if len(comp['name']) > 40 else comp['name'],
                callback_data=f"coach:view_student_comp:{student_id}:{comp['id']}:{distance_for_callback}"
            )
        )

    if total_pages > 1:
        pagination_buttons = []
        if page > 1:
            pagination_buttons.append(
                InlineKeyboardButton(text="⬅️ Назад", callback_data=f"coach:student_competitions:{student_id}:{page-1}")
            )
        pagination_buttons.append(
            InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="coach:stud_comp_noop")
        )
        if page < total_pages:
            pagination_buttons.append(
                InlineKeyboardButton(text="Вперед ➡️", callback_data=f"coach:student_competitions:{student_id}:{page+1}")
            )
        builder.row(*pagination_buttons)

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


@router.callback_query(F.data == "coach:stud_comp_noop")
async def student_competitions_noop(callback: CallbackQuery):
    """No-op callback для индикатора текущей страницы"""
    await callback.answer()


@router.callback_query(F.data.startswith("coach:view_student_comp:"))
async def view_student_competition_details(callback: CallbackQuery):
    """Показать детали соревнования ученика с возможностью редактирования"""

    parts = callback.data.split(":")
    student_id = int(parts[2])
    competition_id = int(parts[3])
    distance = float(parts[4]) if len(parts) > 4 and parts[4] else None
    distance_name = parts[5] if len(parts) > 5 else None
    coach_id = callback.from_user.id

    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    display_name = await get_student_display_name(coach_id, student_id)

    from competitions.competitions_queries import get_competition, get_user_competition_registration

    comp = await get_competition(competition_id)
    if not comp:
        await callback.answer("Соревнование не найдено", show_alert=True)
        return

    registration = await get_user_competition_registration(
        student_id,
        competition_id,
        distance=distance,
        distance_name=distance_name
    )
    if not registration:
        await callback.answer("Регистрация не найдена", show_alert=True)
        return

    from utils.date_formatter import get_user_date_format, DateFormatter
    from competitions.competitions_utils import format_competition_distance as format_dist_with_units
    from competitions.competitions_keyboards import format_time_until_competition
    from datetime import datetime

    coach_date_format = await get_user_date_format(coach_id)

    comp_date = datetime.strptime(comp['date'], '%Y-%m-%d')
    date_str = DateFormatter.format_date(comp['date'], coach_date_format)
    time_until = format_time_until_competition(comp['date'])

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

    proposal_status_text = ""
    if registration.get('proposed_by_coach'):
        proposal_status = registration.get('proposal_status', 'pending')
        if proposal_status == 'pending':
            proposal_status_text = "\n\n⏳ Статус: Ожидает решения ученика"
        elif proposal_status == 'accepted':
            proposal_status_text = "\n\n✅ Статус: Принято учеником"
        elif proposal_status == 'rejected':
            proposal_status_text = "\n\n❌ Статус: Отклонено учеником"

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

    target_time = registration.get('target_time')
    if target_time:
        text += f"🎯 Целевое время: {target_time}\n"
        from utils.time_formatter import calculate_pace_with_unit
        target_pace = await calculate_pace_with_unit(target_time, registration['distance'], coach_id)
        if target_pace:
            text += f"   Темп: {target_pace}\n"
    else:
        text += f"🎯 Целевое время: Не установлено\n"

    result = registration.get('result')
    if result:
        text += f"\n✅ Результат: {result}\n"
        from utils.time_formatter import calculate_pace_with_unit
        result_pace = await calculate_pace_with_unit(result, registration['distance'], coach_id)
        if result_pace:
            text += f"   Темп: {result_pace}\n"

        qualification = registration.get('qualification')
        if qualification:
            text += f"🏅 Квалификация: {qualification}\n"
    else:
        text += f"\n📊 Результат: Еще не добавлен\n"

    text += proposal_status_text

    builder = InlineKeyboardBuilder()

    try:
        comp_date_obj = datetime.strptime(comp['date'], '%Y-%m-%d').date()
        today = datetime.now().date()
        is_finished = comp_date_obj < today
    except:
        is_finished = False

    has_result = registration.get('finish_time') is not None

    if is_finished:
        if not has_result:
            builder.row(
                InlineKeyboardButton(
                    text="🏆 Добавить результат",
                    callback_data=f"coach:add_student_result:{student_id}:{competition_id}:{distance or 0}"
                )
            )
        else:
            builder.row(
                InlineKeyboardButton(
                    text="📊 Посмотреть результат",
                    callback_data=f"coach:view_student_result:{student_id}:{competition_id}:{distance or 0}"
                )
            )
            builder.row(
                InlineKeyboardButton(
                    text="✏️ Изменить результат",
                    callback_data=f"coach:edit_student_result:{student_id}:{competition_id}:{distance or 0}"
                )
            )
    else:
        builder.row(
            InlineKeyboardButton(
                text="✏️ Изменить целевое время",
                callback_data=f"coach:edit_student_target:{student_id}:{competition_id}:{distance or 0}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="❌ Отменить участие",
                callback_data=f"coach:cancel_student_reg:{student_id}:{competition_id}:{distance or 0}"
            )
        )

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
            await db.execute(
                """
                UPDATE competition_participants
                SET proposal_status = 'accepted'
                WHERE user_id = ? AND competition_id = ? AND proposed_by_coach_id = ?
                """,
                (student_id, comp_id, coach_id)
            )
            await db.commit()

        from database.queries import get_user_settings
        student_settings = await get_user_settings(student_id)
        student_name = student_settings.get('name') if student_settings else None

        if not student_name:
            from database.queries import get_user
            student = await get_user(student_id)
            student_name = student.get('name') or student.get('username') or 'Ученик'

        from coach.coach_queries import is_user_coach
        coach_is_coach = await is_user_coach(coach_id)

        await callback.bot.send_message(
            coach_id,
            f"✅ <b>Предложение принято!</b>\n\n"
            f"<b>{student_name}</b> принял ваше предложение участвовать в соревновании.",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard(coach_is_coach)
        )

        builder = InlineKeyboardBuilder()

        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                """
                SELECT distance, target_time FROM competition_participants
                WHERE user_id = ? AND competition_id = ?
                """,
                (student_id, comp_id)
            ) as cursor:
                participant_data = await cursor.fetchone()

        if participant_data:
            distance_val = participant_data[0]
            current_target = participant_data[1]

            builder.row(
                InlineKeyboardButton(
                    text="🎯 Установить свою цель",
                    callback_data=f"comp:edit_target:{comp_id}:{distance_val}"
                )
            )

        builder.row(
            InlineKeyboardButton(text="📋 Мои соревнования", callback_data="comp:my")
        )

        await callback.message.edit_text(
            f"{callback.message.text}\n\n"
            f"✅ <b>Вы приняли предложение!</b>\n"
            f"Соревнование добавлено в раздел «Мои соревнования».\n\n"
            f"Вы можете установить свою цель или оставить рекомендацию тренера.",
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
            await db.execute(
                """
                UPDATE competition_participants
                SET proposal_status = 'rejected'
                WHERE user_id = ? AND competition_id = ? AND proposed_by_coach_id = ?
                """,
                (student_id, comp_id, coach_id)
            )
            await db.commit()

        from database.queries import get_user_settings
        student_settings = await get_user_settings(student_id)
        student_name = student_settings.get('name') if student_settings else None

        if not student_name:
            from database.queries import get_user
            student = await get_user(student_id)
            student_name = student.get('name') or student.get('username') or 'Ученик'

        from coach.coach_queries import is_user_coach
        coach_is_coach = await is_user_coach(coach_id)

        await callback.bot.send_message(
            coach_id,
            f"❌ <b>Предложение отклонено</b>\n\n"
            f"<b>{student_name}</b> отклонил ваше предложение участвовать в соревновании.",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard(coach_is_coach)
        )

        await callback.message.edit_text(
            f"{callback.message.text}\n\n"
            f"❌ <b>Вы отклонили предложение</b>",
            parse_mode="HTML"
        )

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



@router.callback_query(F.data.startswith("accept_coach_dist:"))
async def accept_coach_distance_proposal(callback: CallbackQuery, state: FSMContext):
    """Ученик принимает предложение ОДНОЙ дистанции от тренера"""
    try:
        parts = callback.data.split(":")
        comp_id = int(parts[1])
        coach_id = int(parts[2])
        distance_km_from_callback = float(parts[3])
        student_id = callback.from_user.id

        import aiosqlite
        import os
        DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

        from competitions.competitions_queries import get_competition
        competition = await get_competition(comp_id)

        if not competition:
            await callback.answer("❌ Соревнование не найдено", show_alert=True)
            return

        distances_json = competition.get('distances', '[]')
        try:
            distances = json.loads(distances_json) if isinstance(distances_json, str) else distances_json
        except:
            distances = []

        distance_km = None
        distance_name = None
        for dist in distances:
            if isinstance(dist, dict):
                dist_km = dist.get('distance', 0)
                if abs(dist_km - distance_km_from_callback) < 0.01:  
                    distance_km = dist_km
                    distance_name = dist.get('name', 'Дистанция')
                    break
            else:
                try:
                    dist_km = float(dist)
                except (ValueError, TypeError):
                    import re
                    match = re.search(r'[\d.]+', str(dist))
                    dist_km = float(match.group()) if match else 0

                if abs(dist_km - distance_km_from_callback) < 0.01:
                    distance_km = dist_km
                    distance_name = str(dist)
                    break

        if distance_km is None:
            logger.error(f"Distance {distance_km_from_callback} not found in competition {comp_id}")
            logger.error(f"Available distances: {distances}")
            await callback.answer("❌ Дистанция не найдена в соревновании", show_alert=True)
            return

        logger.info(f"🔍 ACCEPT PROPOSAL: student={student_id}, comp_id={comp_id}, distance_km={distance_km}")
        logger.info(f"   Found distance: distance_km={distance_km}, distance_name='{distance_name}'")

        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                """
                SELECT id, distance, distance_name, target_time, proposal_status
                FROM competition_participants
                WHERE user_id = ? AND competition_id = ?
                """,
                (student_id, comp_id)
            ) as cursor:
                all_rows = await cursor.fetchall()
                logger.info(f"   Found {len(all_rows)} total records for this user/comp:")
                for r in all_rows:
                    logger.info(f"     - id={r[0]}, dist={r[1]}, dist_name='{r[2]}', target='{r[3]}', proposal='{r[4]}'")

            async with db.execute(
                """
                SELECT id, target_time, distance_name FROM competition_participants
                WHERE user_id = ? AND competition_id = ? AND distance = ? AND distance_name = ?
                """,
                (student_id, comp_id, distance_km, distance_name)
            ) as cursor:
                row = await cursor.fetchone()

            if not row:
                logger.warning(f"⚠️ Exact match not found, trying fallback search by distance + pending status")
                async with db.execute(
                    """
                    SELECT id, target_time, distance_name FROM competition_participants
                    WHERE user_id = ? AND competition_id = ? AND distance = ? AND proposal_status = 'pending'
                    """,
                    (student_id, comp_id, distance_km)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        logger.info(f"   ✅ Found via fallback! Using distance_name='{row[2]}' from DB")
                        distance_name = row[2]

            if not row:
                logger.error(f"❌ CRITICAL: Record NOT FOUND even with fallback!")
                logger.error(f"   Searched: distance={distance_km}, distance_name='{distance_name}'")
                await callback.answer("❌ Ошибка: запись не найдена в БД", show_alert=True)
                return

            record_id = row[0]
            target_time_value = row[1]
            logger.info(f"   ✅ Found record id={record_id}, distance_name='{row[2]}'")

            has_target_time = (
                target_time_value is not None
                and target_time_value != ''
                and str(target_time_value).lower() != 'none'
            )

            logger.info(
                f"   ✅ Record FOUND! target_time='{target_time_value}', has_target_time={has_target_time}"
            )

            logger.info(f"Accepting proposal: student={student_id}, comp={comp_id}, dist={distance_km}, dist_name='{distance_name}', has_target_time={has_target_time}")
            logger.info(f"   Will UPDATE using record_id={record_id}")

            cursor = await db.execute(
                """
                UPDATE competition_participants
                SET proposal_status = NULL, reminders_enabled = 1, status = 'registered'
                WHERE id = ?
                """,
                (record_id,)
            )
            rows_updated = cursor.rowcount
            logger.info(f"UPDATE rows_updated: {rows_updated}")

            if rows_updated == 0:
                logger.error(f"❌ CRITICAL: UPDATE failed! No rows updated for record_id={record_id}")
                await callback.answer("❌ Ошибка при обновлении записи", show_alert=True)
                return

            await db.commit()

            async with db.execute(
                """
                SELECT id, target_time, proposal_status, status FROM competition_participants
                WHERE id = ?
                """,
                (record_id,)
            ) as check_cursor:
                after_row = await check_cursor.fetchone()
                if after_row:
                    logger.info(f"✅ AFTER UPDATE: id={after_row[0]}, target_time='{after_row[1]}', proposal_status='{after_row[2]}', status='{after_row[3]}'")
                else:
                    logger.error(f"❌ CRITICAL: Record NOT FOUND after update!")

        from utils.unit_converter import safe_convert_distance_name
        from database.queries import get_user_settings

        student_settings = await get_user_settings(student_id)
        student_distance_unit = student_settings.get('distance_unit', 'км') if student_settings else 'км'
        formatted_dist = safe_convert_distance_name(distance_name, student_distance_unit)

        if student_distance_unit == 'мили' and 'миль' not in formatted_dist and 'миля' not in formatted_dist and 'ярд' not in formatted_dist:
            formatted_dist = f"{formatted_dist} (мили)"
        elif student_distance_unit == 'км' and 'км' not in formatted_dist and 'м' not in formatted_dist:
            formatted_dist = f"{formatted_dist} км"

        if not has_target_time:
            from bot.fsm import CompetitionStates

            await state.update_data(
                accept_proposal_comp_id=comp_id,
                accept_proposal_coach_id=coach_id,
                accept_proposal_distance_km=distance_km,
                accept_proposal_distance_name=distance_name,
                accept_proposal_competition=competition
            )

            from aiogram.utils.keyboard import ReplyKeyboardBuilder
            from aiogram.types import KeyboardButton

            keyboard_builder = ReplyKeyboardBuilder()
            keyboard_builder.row(KeyboardButton(text="⏩ Пропустить"))

            await callback.message.edit_text(
                f"✅ <b>Вы приняли предложение!</b>\n\n"
                f"Соревнование добавлено в раздел 'Мои соревнования'.\n"
                f"Дистанция: <b>{formatted_dist}</b>",
                parse_mode="HTML"
            )

            await callback.message.answer(
                f"📝 <b>Хотите установить целевое время для этой дистанции?</b>\n\n"
                f"Дистанция: <b>{formatted_dist}</b>\n\n"
                f"Введите целевое время в формате:\n"
                f"• ЧЧ:ММ:СС (например, 01:30:00)\n"
                f"• ММ:СС (например, 45:30)\n\n"
                f"Или нажмите <b>⏩ Пропустить</b> чтобы не устанавливать целевое время.",
                parse_mode="HTML",
                reply_markup=keyboard_builder.as_markup(resize_keyboard=True)
            )

            await state.set_state(CompetitionStates.waiting_for_target_time_after_accept)
            await callback.answer()
            return

        await callback.answer(
            f"✅ Вы приняли предложение! Соревнование добавлено.",
            show_alert=True
        )

        try:
            from database.queries import get_user
            student = await get_user(student_id)
            student_name = student.get('name') or student.get('username') or f'Ученик {student_id}'

            coach_settings = await get_user_settings(coach_id)
            coach_distance_unit = coach_settings.get('distance_unit', 'км') if coach_settings else 'км'
            formatted_dist_coach = safe_convert_distance_name(distance_name, coach_distance_unit)

            if coach_distance_unit == 'мили' and 'миль' not in formatted_dist_coach and 'миля' not in formatted_dist_coach and 'ярд' not in formatted_dist_coach:
                formatted_dist_coach = f"{formatted_dist_coach} (мили)"
            elif coach_distance_unit == 'км' and 'км' not in formatted_dist_coach and 'м' not in formatted_dist_coach:
                formatted_dist_coach = f"{formatted_dist_coach} км"

            await callback.bot.send_message(
                coach_id,
                f"✅ <b>Ученик принял предложение!</b>\n\n"
                f"<b>{student_name}</b> принял участие в соревновании:\n"
                f"🏆 {competition['name']}\n"
                f"📏 Дистанция: {formatted_dist_coach}",
                parse_mode="HTML"
            )

            from bot.keyboards import get_main_menu_keyboard
            from coach.coach_queries import is_user_coach

            coach_is_coach = await is_user_coach(coach_id)
            await callback.bot.send_message(
                coach_id,
                "Вы в главном меню",
                reply_markup=get_main_menu_keyboard(is_coach=coach_is_coach)
            )
        except Exception as e:
            logger.error(f"Error sending notification to coach: {e}")

        try:
            await callback.message.delete()
        except:
            pass  

        from competitions.competitions_handlers import show_my_competitions
        from aiogram.types import Message

        new_message = await callback.bot.send_message(
            callback.from_user.id,
            "⏳ Загрузка..."
        )

        class RedirectCallback:
            def __init__(self, msg, user):
                self.message = msg
                self.from_user = user
                self.data = "comp:my"

            async def answer(self, text="", show_alert=False):
                pass

        redirect_callback = RedirectCallback(new_message, callback.from_user)
        await show_my_competitions(redirect_callback, state, page=1)

    except Exception as e:
        logger.error(f"Error accepting distance proposal: {e}")
        await callback.answer("❌ Ошибка при принятии предложения", show_alert=True)


@router.callback_query(F.data.startswith("change_coach_dist_time:"))
async def change_coach_distance_time(callback: CallbackQuery, state: FSMContext):
    """Ученик хочет изменить целевое время для дистанции"""
    try:
        parts = callback.data.split(":")
        comp_id = int(parts[1])
        coach_id = int(parts[2])
        distance_idx = int(parts[3])
        student_id = callback.from_user.id

        from competitions.competitions_queries import get_competition
        competition = await get_competition(comp_id)

        if not competition:
            await callback.answer("❌ Соревнование не найдено", show_alert=True)
            return

        distances_json = competition.get('distances', '[]')
        try:
            distances = json.loads(distances_json) if isinstance(distances_json, str) else distances_json
        except:
            distances = []

        if distance_idx >= len(distances):
            await callback.answer("❌ Дистанция не найдена", show_alert=True)
            return

        dist = distances[distance_idx]
        if isinstance(dist, dict):
            distance_km = dist.get('distance', 0)
            distance_name = dist.get('name', 'Дистанция')
        else:
            distance_km = float(dist)
            distance_name = str(dist)

        import aiosqlite
        import os
        DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                """
                SELECT target_time FROM competition_participants
                WHERE user_id = ? AND competition_id = ? AND distance = ? AND distance_name = ?
                """,
                (student_id, comp_id, distance_km, distance_name)
            ) as cursor:
                row = await cursor.fetchone()
                current_target_time = row[0] if row and row[0] else None

        await state.update_data(
            change_time_comp_id=comp_id,
            change_time_coach_id=coach_id,
            change_time_distance_idx=distance_idx,
            change_time_distance_km=distance_km,
            change_time_distance_name=distance_name,
            change_time_competition=competition
        )

        from utils.unit_converter import safe_convert_distance_name
        from database.queries import get_user_settings

        student_settings = await get_user_settings(student_id)
        student_distance_unit = student_settings.get('distance_unit', 'км') if student_settings else 'км'
        formatted_dist = safe_convert_distance_name(distance_name, student_distance_unit)

        from bot.fsm import CompetitionStates

        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="❌ Отменить",
            callback_data=f"cancel_change_time:{comp_id}:{coach_id}:{distance_idx}"
        ))

        time_text = f"⏱ <b>Изменение целевого времени</b>\n\n" \
                   f"Дистанция: <b>{formatted_dist}</b>\n"

        if current_target_time:
            time_text += f"Текущее целевое время: <b>{current_target_time}</b>\n\n"
        else:
            time_text += "\n"

        time_text += f"Введите новое целевое время в формате:\n" \
                    f"• ЧЧ:ММ:СС (например, 01:30:00)\n" \
                    f"• ММ:СС (например, 45:30)"

        await callback.message.edit_text(
            time_text,
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )

        await state.set_state(CompetitionStates.waiting_for_target_time_edit)
        await callback.answer()

    except Exception as e:
        logger.error(f"Error initiating time change: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.message(CompetitionStates.waiting_for_target_time_edit)
async def process_changed_target_time(message: Message, state: FSMContext):
    """Обработать новое целевое время от ученика"""
    from utils.time_formatter import validate_time_format, normalize_time

    user_id = message.from_user.id
    target_time_text = message.text.strip()

    if not validate_time_format(target_time_text):
        await message.answer(
            "❌ Неверный формат времени!\n\n"
            "Используйте формат ЧЧ:ММ:СС или ММ:СС\n"
            "Примеры: 01:30:00 или 45:30"
        )
        return

    target_time = normalize_time(target_time_text)

    try:
        data = await state.get_data()
        comp_id = data.get('change_time_comp_id')
        coach_id = data.get('change_time_coach_id')
        distance_idx = data.get('change_time_distance_idx')
        distance_km = data.get('change_time_distance_km')
        distance_name = data.get('change_time_distance_name')
        competition = data.get('change_time_competition')

        if not all([comp_id, coach_id is not None, distance_idx is not None, distance_name, competition]):
            await message.answer("❌ Ошибка: данные не найдены")
            await state.clear()
            return

        import aiosqlite
        import os
        DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """
                UPDATE competition_participants
                SET target_time = ?, proposal_status = 'accepted', reminders_enabled = 1
                WHERE user_id = ? AND competition_id = ? AND distance = ? AND distance_name = ?
                """,
                (target_time, user_id, comp_id, distance_km, distance_name)
            )
            await db.commit()

        from utils.unit_converter import safe_convert_distance_name
        from database.queries import get_user_settings

        student_settings = await get_user_settings(user_id)
        student_distance_unit = student_settings.get('distance_unit', 'км') if student_settings else 'км'
        formatted_dist = safe_convert_distance_name(distance_name, student_distance_unit)

        if student_distance_unit == 'мили' and 'миль' not in formatted_dist and 'миля' not in formatted_dist and 'ярд' not in formatted_dist:
            formatted_dist = f"{formatted_dist} (мили)"
        elif student_distance_unit == 'км' and 'км' not in formatted_dist and 'м' not in formatted_dist:
            formatted_dist = f"{formatted_dist} км"

        await message.answer(
            f"✅ <b>Целевое время изменено!</b>\n\n"
            f"Дистанция: <b>{formatted_dist}</b>\n"
            f"Новое целевое время: <b>{target_time}</b>\n\n"
            f"Соревнование добавлено в раздел 'Мои соревнования'.",
            parse_mode="HTML"
        )

        from bot.keyboards import get_main_menu_keyboard
        from coach.coach_queries import is_user_coach

        student_is_coach = await is_user_coach(user_id)
        await message.answer(
            "Вы в главном меню",
            reply_markup=get_main_menu_keyboard(is_coach=student_is_coach)
        )

        try:
            from database.queries import get_user
            student = await get_user(user_id)
            student_name = student.get('name') or student.get('username') or f'Ученик {user_id}'

            coach_settings = await get_user_settings(coach_id)
            coach_distance_unit = coach_settings.get('distance_unit', 'км') if coach_settings else 'км'
            formatted_dist_coach = safe_convert_distance_name(distance_name, coach_distance_unit)

            if coach_distance_unit == 'мили' and 'миль' not in formatted_dist_coach and 'миля' not in formatted_dist_coach and 'ярд' not in formatted_dist_coach:
                formatted_dist_coach = f"{formatted_dist_coach} (мили)"
            elif coach_distance_unit == 'км' and 'км' not in formatted_dist_coach and 'м' not in formatted_dist_coach:
                formatted_dist_coach = f"{formatted_dist_coach} км"

            await message.bot.send_message(
                coach_id,
                f"✅ <b>Ученик принял предложение с изменением!</b>\n\n"
                f"<b>{student_name}</b> принял участие в соревновании:\n"
                f"🏆 {competition['name']}\n"
                f"📏 Дистанция: {formatted_dist_coach}\n"
                f"⏱ Новое целевое время: {target_time}",
                parse_mode="HTML"
            )

            coach_is_coach = await is_user_coach(coach_id)
            await message.bot.send_message(
                coach_id,
                "Вы в главном меню",
                reply_markup=get_main_menu_keyboard(is_coach=coach_is_coach)
            )
        except Exception as e:
            logger.error(f"Error sending notification to coach: {e}")

        await state.clear()

    except Exception as e:
        logger.error(f"Error processing changed target time: {e}")
        await message.answer("❌ Ошибка при сохранении времени")
        await state.clear()


@router.callback_query(F.data.startswith("cancel_change_time:"))
async def cancel_change_time(callback: CallbackQuery, state: FSMContext):
    """Отменить изменение целевого времени"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Изменение времени отменено",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(CompetitionStates.waiting_for_target_time_after_accept)
async def process_target_time_after_accept(message: Message, state: FSMContext):
    """Обработать целевое время после принятия предложения без времени"""
    from utils.time_formatter import validate_time_format, normalize_time
    from aiogram.types import ReplyKeyboardRemove

    user_id = message.from_user.id
    text = message.text.strip()

    data = await state.get_data()
    comp_id = data.get('accept_proposal_comp_id')
    coach_id = data.get('accept_proposal_coach_id')
    distance_km = data.get('accept_proposal_distance_km')
    distance_name = data.get('accept_proposal_distance_name')
    competition = data.get('accept_proposal_competition')

    if not all([comp_id, coach_id is not None, distance_name, competition]):
        await message.answer("❌ Ошибка: данные не найдены", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    try:
        if text == "⏩ Пропустить":
            target_time = None

            import aiosqlite
            import os
            DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

            async with aiosqlite.connect(DB_PATH) as db:
                async with db.execute(
                    """
                    SELECT id, distance, distance_name, proposal_status, status FROM competition_participants
                    WHERE user_id = ? AND competition_id = ?
                    """,
                    (user_id, comp_id)
                ) as cursor:
                    all_rows = await cursor.fetchall()
                    logger.info(f"SKIP: Found {len(all_rows)} records for user={user_id}, comp={comp_id}")
                    for row in all_rows:
                        logger.info(f"  - id={row[0]}, dist={row[1]}, dist_name='{row[2]}', proposal_status='{row[3]}', status='{row[4]}'")

                async with db.execute(
                    """
                    SELECT id, proposal_status, status FROM competition_participants
                    WHERE user_id = ? AND competition_id = ? AND distance = ? AND distance_name = ?
                    """,
                    (user_id, comp_id, distance_km, distance_name)
                ) as cursor:
                    check_row = await cursor.fetchone()
                    if check_row:
                        record_id, prop_status, status = check_row
                        logger.info(f"SKIP: Found record id={record_id}, proposal_status='{prop_status}', status='{status}'")

                        if prop_status is not None or status != 'registered':
                            logger.warning(f"SKIP: FIXING status! Was: proposal_status='{prop_status}', status='{status}'")
                            await db.execute(
                                """
                                UPDATE competition_participants
                                SET proposal_status = NULL, status = 'registered', reminders_enabled = 1
                                WHERE id = ?
                                """,
                                (record_id,)
                            )
                            await db.commit()
                            logger.info(f"SKIP: Status FIXED! Now: proposal_status=NULL, status='registered'")
                    else:
                        logger.error(f"SKIP: Record NOT FOUND! user={user_id}, comp={comp_id}, dist={distance_km}, dist_name='{distance_name}'")

            await message.answer(
                "✅ <b>Вы приняли предложение!</b>\n\n"
                "Соревнование добавлено без целевого времени.",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardRemove()
            )

        elif text == "❌ Отменить":
            import aiosqlite
            import os
            DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    """
                    DELETE FROM competition_participants
                    WHERE user_id = ? AND competition_id = ? AND distance = ? AND distance_name = ?
                    """,
                    (user_id, comp_id, distance_km, distance_name)
                )
                await db.commit()

            await message.answer(
                "❌ Предложение отклонено",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardRemove()
            )
            await state.clear()

            from bot.keyboards import get_main_menu_keyboard
            from coach.coach_queries import is_user_coach

            student_is_coach = await is_user_coach(user_id)
            await message.answer(
                "Вы в главном меню",
                reply_markup=get_main_menu_keyboard(is_coach=student_is_coach)
            )
            return

        else:
            if not validate_time_format(text):
                await message.answer(
                    "❌ Неверный формат времени!\n\n"
                    "Используйте формат ЧЧ:ММ:СС или ММ:СС\n"
                    "Примеры: 01:30:00 или 45:30"
                )
                return

            target_time = normalize_time(text)

            import aiosqlite
            import os
            DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

            logger.info(f"Updating target time after accept: student={user_id}, comp={comp_id}, dist={distance_km}, dist_name={distance_name}, target_time={target_time}")
            async with aiosqlite.connect(DB_PATH) as db:
                cursor = await db.execute(
                    """
                    UPDATE competition_participants
                    SET target_time = ?
                    WHERE user_id = ? AND competition_id = ? AND distance = ? AND distance_name = ?
                    """,
                    (target_time, user_id, comp_id, distance_km, distance_name)
                )
                rows_updated = cursor.rowcount
                logger.info(f"Target time update - rows updated: {rows_updated}")
                await db.commit()
                logger.info(f"Target time update committed to database")

            await message.answer(
                f"✅ <b>Целевое время установлено!</b>\n\n"
                f"⏱ Время: <b>{target_time}</b>",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardRemove()
            )

        from database.queries import get_user, get_user_settings
        from utils.unit_converter import safe_convert_distance_name

        student = await get_user(user_id)
        student_name = student.get('name') or student.get('username') or f'Ученик {user_id}'

        coach_settings = await get_user_settings(coach_id)
        coach_distance_unit = coach_settings.get('distance_unit', 'км') if coach_settings else 'км'
        formatted_dist_coach = safe_convert_distance_name(distance_name, coach_distance_unit)

        if coach_distance_unit == 'мили' and 'миль' not in formatted_dist_coach and 'миля' not in formatted_dist_coach and 'ярд' not in formatted_dist_coach:
            formatted_dist_coach = f"{formatted_dist_coach} (мили)"
        elif coach_distance_unit == 'км' and 'км' not in formatted_dist_coach and 'м' not in formatted_dist_coach:
            formatted_dist_coach = f"{formatted_dist_coach} км"

        notification_text = (
            f"✅ <b>Ученик принял предложение!</b>\n\n"
            f"<b>{student_name}</b> принял участие в соревновании:\n"
            f"🏆 {competition['name']}\n"
            f"📏 Дистанция: {formatted_dist_coach}"
        )

        if target_time:
            notification_text += f"\n⏱ Целевое время: <b>{target_time}</b>"

        await message.bot.send_message(
            coach_id,
            notification_text,
            parse_mode="HTML"
        )

        from bot.keyboards import get_main_menu_keyboard
        from coach.coach_queries import is_user_coach

        coach_is_coach = await is_user_coach(coach_id)
        await message.bot.send_message(
            coach_id,
            "Вы в главном меню",
            reply_markup=get_main_menu_keyboard(is_coach=coach_is_coach)
        )

        from competitions.competitions_handlers import show_my_competitions

        new_msg = await message.answer("📋 Мои соревнования")

        class RedirectCallback:
            def __init__(self, msg, user, bot):
                self.message = msg
                self.from_user = user
                self.data = "comp:my"
                self.bot = bot

            async def answer(self, text="", show_alert=False):
                pass

        redirect_callback = RedirectCallback(new_msg, message.from_user, message.bot)
        await show_my_competitions(redirect_callback, state, page=1)

    except Exception as e:
        logger.error(f"Error processing target time after accept: {e}")
        await message.answer(
            "❌ Ошибка при сохранении времени",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()


@router.callback_query(F.data.startswith("reject_coach_dist:"))
async def reject_coach_distance_proposal(callback: CallbackQuery):
    """Ученик отклоняет предложение ОДНОЙ дистанции от тренера"""
    try:
        parts = callback.data.split(":")
        comp_id = int(parts[1])
        coach_id = int(parts[2])
        distance_km_from_callback = float(parts[3])
        student_id = callback.from_user.id

        import aiosqlite
        import os
        DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

        from competitions.competitions_queries import get_competition
        competition = await get_competition(comp_id)

        if not competition:
            await callback.answer("❌ Соревнование не найдено", show_alert=True)
            return

        distances_json = competition.get('distances', '[]')
        try:
            distances = json.loads(distances_json) if isinstance(distances_json, str) else distances_json
        except:
            distances = []

        distance_km = None
        distance_name = None
        for dist in distances:
            if isinstance(dist, dict):
                dist_km = dist.get('distance', 0)
                if abs(dist_km - distance_km_from_callback) < 0.01:
                    distance_km = dist_km
                    distance_name = dist.get('name', 'Дистанция')
                    break
            else:
                try:
                    dist_km = float(dist)
                except (ValueError, TypeError):
                    import re
                    match = re.search(r'[\d.]+', str(dist))
                    dist_km = float(match.group()) if match else 0

                if abs(dist_km - distance_km_from_callback) < 0.01:
                    distance_km = dist_km
                    distance_name = str(dist)
                    break

        if distance_km is None:
            logger.error(f"Distance {distance_km_from_callback} not found in competition {comp_id}")
            logger.error(f"Available distances: {distances}")
            await callback.answer("❌ Дистанция не найдена в соревновании", show_alert=True)
            return

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """
                DELETE FROM competition_participants
                WHERE user_id = ? AND competition_id = ? AND distance = ? AND distance_name = ?
                """,
                (student_id, comp_id, distance_km, distance_name)
            )
            await db.commit()

        from utils.unit_converter import safe_convert_distance_name
        from database.queries import get_user_settings

        student_settings = await get_user_settings(student_id)
        student_distance_unit = student_settings.get('distance_unit', 'км') if student_settings else 'км'
        formatted_dist = safe_convert_distance_name(distance_name, student_distance_unit)

        if student_distance_unit == 'мили' and 'миль' not in formatted_dist and 'миля' not in formatted_dist and 'ярд' not in formatted_dist:
            formatted_dist = f"{formatted_dist} (мили)"
        elif student_distance_unit == 'км' and 'км' not in formatted_dist and 'м' not in formatted_dist:
            formatted_dist = f"{formatted_dist} км"

        await callback.message.edit_text(
            f"❌ <b>Вы отклонили предложение</b>\n\n"
            f"Дистанция: <b>{formatted_dist}</b>",
            parse_mode="HTML"
        )

        try:
            from database.queries import get_user
            student = await get_user(student_id)
            student_name = student.get('name') or student.get('username') or f'Ученик {student_id}'

            coach_settings = await get_user_settings(coach_id)
            coach_distance_unit = coach_settings.get('distance_unit', 'км') if coach_settings else 'км'
            formatted_dist_coach = safe_convert_distance_name(distance_name, coach_distance_unit)

            if coach_distance_unit == 'мили' and 'миль' not in formatted_dist_coach and 'миля' not in formatted_dist_coach and 'ярд' not in formatted_dist_coach:
                formatted_dist_coach = f"{formatted_dist_coach} (мили)"
            elif coach_distance_unit == 'км' and 'км' not in formatted_dist_coach and 'м' not in formatted_dist_coach:
                formatted_dist_coach = f"{formatted_dist_coach} км"

            await callback.bot.send_message(
                coach_id,
                f"❌ <b>Ученик отклонил предложение</b>\n\n"
                f"<b>{student_name}</b> отклонил участие в соревновании:\n"
                f"🏆 {competition['name']}\n"
                f"📏 Дистанция: {formatted_dist_coach}",
                parse_mode="HTML"
            )

            from bot.keyboards import get_main_menu_keyboard
            from coach.coach_queries import is_user_coach

            coach_is_coach = await is_user_coach(coach_id)
            await callback.bot.send_message(
                coach_id,
                "Вы в главном меню",
                reply_markup=get_main_menu_keyboard(is_coach=coach_is_coach)
            )
        except Exception as e:
            logger.error(f"Error sending notification to coach: {e}")

        await callback.answer("Предложение отклонено", show_alert=True)

    except Exception as e:
        logger.error(f"Error rejecting distance proposal: {e}")
        await callback.answer("❌ Ошибка при отклонении предложения", show_alert=True)


@router.callback_query(F.data.startswith("coach:edit_student_target:"))
async def edit_student_target_time(callback: CallbackQuery, state: FSMContext):
    """Тренер изменяет целевое время ученика"""
    parts = callback.data.split(":")
    student_id = int(parts[2])
    competition_id = int(parts[3])
    distance = float(parts[4])
    coach_id = callback.from_user.id

    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    display_name = await get_student_display_name(coach_id, student_id)

    from competitions.competitions_queries import get_competition
    competition = await get_competition(competition_id)

    if not competition:
        await callback.answer("❌ Соревнование не найдено", show_alert=True)
        return

    from competitions.competitions_queries import get_user_competitions
    user_comps = await get_user_competitions(student_id)

    registration = None
    for comp in user_comps:
        comp_distance = comp.get('distance')
        if comp['id'] == competition_id:
            if (comp_distance == distance) or \
               (comp_distance in (None, 0) and distance in (None, 0)):
                registration = comp
                break

    if not registration:
        registrations_for_comp = [c for c in user_comps if c['id'] == competition_id]
        if len(registrations_for_comp) == 1:
            registration = registrations_for_comp[0]
        else:
            await callback.answer("❌ Регистрация не найдена", show_alert=True)
            return

    await state.update_data(
        edit_student_target_comp_id=competition_id,
        edit_student_target_distance=distance,
        edit_student_target_student_id=student_id
    )

    from competitions.competitions_utils import format_competition_distance as format_dist_with_units
    from database.queries import get_user_settings
    from utils.unit_converter import safe_convert_distance_name

    distance_name = registration.get('distance_name') if registration else None
    if distance_name and isinstance(distance_name, str):
        distance_name = distance_name.strip()
        if distance_name.lower() in ('none', 'null', '0', '0.0', ''):
            distance_name = None

    if distance_name and distance_name.strip():
        settings = await get_user_settings(coach_id)
        distance_unit = settings.get('distance_unit', 'км') if settings else 'км'

        import re
        if re.match(r'^\d+(\.\d+)?$', distance_name):
            dist_str = f"{distance_name} {distance_unit}"
        else:
            dist_str = safe_convert_distance_name(distance_name, distance_unit)
    else:
        dist_str = await format_dist_with_units(distance, coach_id)

    text = (
        f"👤 Ученик: <b>{display_name}</b>\n\n"
        f"🏃 <b>{competition['name']}</b>\n"
        f"📏 Дистанция: {dist_str}\n\n"
        f"Введите новое целевое время в формате ЧЧ:ММ:СС или ММ:СС:\n\n"
        f"<i>Например:\n"
        f"• 03:30:00 (3 часа 30 минут)\n"
        f"• 45:00 (45 минут)\n"
        f"• 1:30:15 (1 час 30 минут 15 секунд)</i>"
    )

    await callback.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(CoachStates.waiting_for_student_target_time)
    await callback.answer()


@router.message(CoachStates.waiting_for_student_target_time)
async def process_student_target_time_edit(message: Message, state: FSMContext):
    """Обработать новое целевое время ученика"""
    from utils.time_formatter import validate_time_format

    if message.text == "❌ Отменить":
        data = await state.get_data()
        student_id = data.get('edit_student_target_student_id')

        await message.answer("❌ Изменение отменено", reply_markup=ReplyKeyboardRemove())
        await state.clear()

        if student_id:
            import asyncio
            from types import SimpleNamespace

            cancel_msg = await message.answer("Возвращаю в раздел соревнований ученика...")

            fake_callback = SimpleNamespace(
                data=f"coach:student_competitions:{student_id}",
                from_user=message.from_user,
                message=cancel_msg,
                answer=lambda *args, **kwargs: asyncio.sleep(0),
                bot=message.bot
            )
            await show_student_competitions(fake_callback, state)
        return

    time_text = message.text.strip()

    if not validate_time_format(time_text):
        await message.answer(
            "❌ Неверный формат времени. Используйте ЧЧ:ММ:СС или ММ:СС\n"
            "Например: 03:30:00 или 45:00"
        )
        return

    from utils.time_formatter import normalize_time
    time_str = normalize_time(time_text)

    data = await state.get_data()
    competition_id = data.get('edit_student_target_comp_id')
    distance = data.get('edit_student_target_distance')
    student_id = data.get('edit_student_target_student_id')
    coach_id = message.from_user.id

    if not await can_coach_access_student(coach_id, student_id):
        await message.answer("❌ Нет доступа", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    from competitions.competitions_queries import update_target_time
    success = await update_target_time(student_id, competition_id, distance, time_str)

    if success:
        from competitions.competitions_queries import get_competition
        comp = await get_competition(competition_id)
        display_name = await get_student_display_name(coach_id, student_id)

        try:
            from bot.keyboards import get_main_menu_keyboard
            from coach.coach_queries import is_user_coach
            from aiogram.types import ReplyKeyboardRemove
            student_is_coach = await is_user_coach(student_id)

            await message.bot.send_message(
                student_id,
                f"👨‍🏫 <b>Изменение целевого времени</b>\n\n"
                f"Ваш тренер изменил целевое время для соревнования:\n\n"
                f"🏆 <b>{comp['name']}</b>\n"
                f"🎯 Новое целевое время: <b>{time_str}</b>",
                parse_mode="HTML"
            )

            await message.bot.send_message(
                student_id,
                "⏳ Возвращаю вас в главное меню...",
                reply_markup=ReplyKeyboardRemove()
            )

            await message.bot.send_message(
                student_id,
                "Вы в главном меню",
                reply_markup=get_main_menu_keyboard(is_coach=student_is_coach)
            )
        except Exception as e:
            logger.error(f"Error sending notification to student: {e}")

        await message.answer(
            f"✅ Целевое время для ученика <b>{display_name}</b> обновлено на {time_str}",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )

        await state.clear()

        import asyncio
        from types import SimpleNamespace

        redirect_msg = await message.answer("Возвращаю в раздел соревнований ученика...")

        fake_callback = SimpleNamespace(
            data=f"coach:student_competitions:{student_id}",
            from_user=message.from_user,
            message=redirect_msg,
            answer=lambda *args, **kwargs: asyncio.sleep(0),
            bot=message.bot
        )
        await show_student_competitions(fake_callback, state)
    else:
        await message.answer(
            "❌ Не удалось обновить целевое время",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()


@router.callback_query(F.data.startswith("coach:cancel_student_reg:"))
async def cancel_student_registration(callback: CallbackQuery):
    """Тренер отменяет участие ученика в соревновании - показать подтверждение"""
    parts = callback.data.split(":")
    student_id = int(parts[2])
    competition_id = int(parts[3])
    distance = float(parts[4])
    coach_id = callback.from_user.id

    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    display_name = await get_student_display_name(coach_id, student_id)

    from competitions.competitions_queries import get_competition
    competition = await get_competition(competition_id)

    if not competition:
        await callback.answer("❌ Соревнование не найдено", show_alert=True)
        return

    from competitions.competitions_queries import get_user_competitions
    user_comps = await get_user_competitions(student_id)

    registration = None
    for comp in user_comps:
        comp_distance = comp.get('distance')
        if comp['id'] == competition_id:
            if (comp_distance == distance) or \
               (comp_distance in (None, 0) and distance in (None, 0)):
                registration = comp
                break

    if not registration:
        registrations_for_comp = [c for c in user_comps if c['id'] == competition_id]
        if len(registrations_for_comp) == 1:
            registration = registrations_for_comp[0]
        else:
            await callback.answer("❌ Регистрация не найдена", show_alert=True)
            return

    from competitions.competitions_utils import format_competition_distance as format_dist_with_units
    from database.queries import get_user_settings
    from utils.unit_converter import safe_convert_distance_name

    distance_name = registration.get('distance_name') if registration else None
    if distance_name and isinstance(distance_name, str):
        distance_name = distance_name.strip()
        if distance_name.lower() in ('none', 'null', '0', '0.0', ''):
            distance_name = None

    if distance_name and distance_name.strip():
        settings = await get_user_settings(coach_id)
        distance_unit = settings.get('distance_unit', 'км') if settings else 'км'

        import re
        if re.match(r'^\d+(\.\d+)?$', distance_name):
            dist_str = f"{distance_name} {distance_unit}"
        else:
            dist_str = safe_convert_distance_name(distance_name, distance_unit)
    else:
        dist_str = await format_dist_with_units(distance, coach_id)

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Да, отменить",
            callback_data=f"coach:cancel_student_reg_confirm:{student_id}:{competition_id}:{distance}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Нет, вернуться",
            callback_data=f"coach:view_student_comp:{student_id}:{competition_id}:{distance}"
        )
    )

    text = (
        f"⚠️ <b>ПОДТВЕРЖДЕНИЕ</b>\n\n"
        f"Отменить участие ученика <b>{display_name}</b> в соревновании?\n\n"
        f"🏆 <b>{competition['name']}</b>\n"
        f"📏 Дистанция: {dist_str}\n\n"
        f"<i>Ученик получит уведомление об отмене.</i>"
    )

    await callback.answer()
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("coach:cancel_student_reg_confirm:"))
async def confirm_cancel_student_registration(callback: CallbackQuery):
    """Подтвердить отмену участия ученика"""
    parts = callback.data.split(":")
    student_id = int(parts[2])
    competition_id = int(parts[3])
    distance = float(parts[4])
    coach_id = callback.from_user.id

    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    display_name = await get_student_display_name(coach_id, student_id)

    await callback.answer()

    from competitions.competitions_queries import unregister_from_competition_with_distance, get_competition
    success = await unregister_from_competition_with_distance(student_id, competition_id, distance)

    if success:
        comp = await get_competition(competition_id)

        try:
            from bot.keyboards import get_main_menu_keyboard
            from coach.coach_queries import is_user_coach
            student_is_coach = await is_user_coach(student_id)

            await callback.bot.send_message(
                student_id,
                f"👨‍🏫 <b>Отмена регистрации</b>\n\n"
                f"Ваш тренер отменил вашу регистрацию на соревнование:\n\n"
                f"🏆 <b>{comp['name']}</b>\n\n"
                f"<i>Вы можете зарегистрироваться снова самостоятельно.</i>",
                parse_mode="HTML",
                reply_markup=get_main_menu_keyboard(is_coach=student_is_coach)
            )
        except Exception as e:
            logger.error(f"Error sending notification to student: {e}")

        await callback.message.edit_text(
            f"✅ Участие ученика <b>{display_name}</b> отменено",
            parse_mode="HTML"
        )

        from types import SimpleNamespace
        fake_callback = SimpleNamespace(
            data=f"coach:student_competitions:{student_id}",
            from_user=callback.from_user,
            message=callback.message,
            answer=callback.answer,
            bot=callback.bot
        )
        from aiogram.fsm.context import FSMContext as FSMContextType
        fake_state = FSMContextType(
            storage=callback.bot.get("state").storage if hasattr(callback.bot, "get") else None,
            key=callback.message.chat.id
        )
        await show_student_competitions(fake_callback, fake_state)
    else:
        await callback.message.edit_text("❌ Не удалось отменить регистрацию")


@router.callback_query(F.data.startswith("coach:view_student_result:"))
async def view_student_result(callback: CallbackQuery):
    """Просмотр результата соревнования ученика"""
    parts = callback.data.split(":")
    student_id = int(parts[2])
    competition_id = int(parts[3])
    distance = float(parts[4])
    coach_id = callback.from_user.id

    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    display_name = await get_student_display_name(coach_id, student_id)

    from competitions.competitions_queries import get_user_competitions, get_competition
    user_comps = await get_user_competitions(student_id, competition_id=competition_id)

    if not user_comps:
        await callback.answer("❌ Результат не найден", show_alert=True)
        return

    comp_result = user_comps[0]
    competition = await get_competition(competition_id)

    if not competition:
        await callback.answer("❌ Соревнование не найдено", show_alert=True)
        return

    from competitions.competitions_utils import format_competition_distance as format_dist_with_units, format_competition_date
    from utils.date_formatter import get_user_date_format
    from database.queries import get_user_settings
    from utils.unit_converter import safe_convert_distance_name
    from utils.time_formatter import normalize_time, calculate_pace_with_unit
    from competitions.competitions_keyboards import format_qualification

    coach_date_format = await get_user_date_format(coach_id)

    distance_name = comp_result.get('distance_name')

    if distance_name:
        settings = await get_user_settings(coach_id)
        distance_unit = settings.get('distance_unit', 'км') if settings else 'км'
        dist_str = safe_convert_distance_name(distance_name, distance_unit)
    else:
        dist_str = await format_dist_with_units(comp_result['distance'], coach_id)

    date_str = await format_competition_date(comp_result['date'], coach_id)

    pace = await calculate_pace_with_unit(comp_result['finish_time'], comp_result['distance'], coach_id)

    text = (
        f"👤 Ученик: <b>{display_name}</b>\n\n"
        f"🏆 <b>{competition['name']}</b>\n\n"
        f"📅 Дата: {date_str}\n"
        f"📏 Дистанция: {dist_str}\n"
        f"⏱️ Время: {normalize_time(comp_result['finish_time'])}\n"
    )

    if pace:
        text += f"⚡ Темп: {pace}\n"

    if comp_result.get('place_overall'):
        text += f"🏆 Место общее: {comp_result['place_overall']}\n"
    if comp_result.get('place_age_category'):
        text += f"🏅 Место в категории: {comp_result['place_age_category']}\n"
    qual = comp_result.get('qualification')
    if qual and qual not in [None, '', 'Нет разряда', 'Б/р']:
        text += f"🎖️ Разряд: {format_qualification(qual)}\n"
    if comp_result.get('heart_rate'):
        text += f"❤️ Средний пульс: {comp_result['heart_rate']} уд/мин\n"

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад к соревнованию",
            callback_data=f"coach:view_student_comp:{student_id}:{competition_id}:{distance}"
        )
    )

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

