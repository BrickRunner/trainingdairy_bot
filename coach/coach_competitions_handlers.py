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
from coach.coach_training_queries import can_coach_access_student, get_student_display_name
from competitions.competitions_queries import add_competition, get_competition
from database.queries import get_user

logger = logging.getLogger(__name__)
router = Router()


# ========== ПРЕДЛОЖЕНИЕ СОРЕВНОВАНИЯ УЧЕНИКУ ==========

@router.callback_query(F.data.startswith("coach:propose_comp:"))
async def start_propose_competition(callback: CallbackQuery, state: FSMContext):
    """Начать процесс предложения соревнования ученику"""

    student_id = int(callback.data.split(":")[2])
    coach_id = callback.from_user.id

    # Проверяем доступ
    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    display_name = await get_student_display_name(coach_id, student_id)

    # Сохраняем student_id в состоянии
    await state.update_data(propose_student_id=student_id)

    text = (
        f"🏆 <b>ПРЕДЛОЖИТЬ СОРЕВНОВАНИЕ</b>\n\n"
        f"Ученик: <b>{display_name}</b>\n\n"
        f"📝 <b>Шаг 1 из 5</b>\n\n"
        f"Введите <b>название</b> соревнования:\n"
        f"<i>Например: Московский марафон 2026</i>"
    )

    await callback.message.edit_text(text, parse_mode="HTML")
    await state.set_state(CompetitionStates.waiting_for_comp_name)
    await callback.answer()


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

    text = (
        f"✅ Название: <b>{comp_name}</b>\n\n"
        f"📝 <b>Шаг 2 из 5</b>\n\n"
        f"Введите <b>дату</b> соревнования:\n"
        f"<i>Формат: ДД.ММ.ГГГГ\nНапример: 25.09.2026</i>"
    )

    await message.answer(text, parse_mode="HTML")
    await state.set_state(CompetitionStates.waiting_for_comp_date)


@router.message(CompetitionStates.waiting_for_comp_date)
async def process_proposed_comp_date(message: Message, state: FSMContext):
    """Обработать дату предложенного соревнования"""

    # Проверяем что это flow от тренера
    data = await state.get_data()
    if 'propose_student_id' not in data:
        return

    from datetime import date
    date_text = message.text.strip()

    try:
        comp_date = datetime.strptime(date_text, '%d.%m.%Y').date()

        if comp_date < date.today():
            await message.answer(
                "❌ Дата соревнования должна быть в будущем.\n"
                "Введите корректную дату:"
            )
            return

    except ValueError:
        await message.answer(
            "❌ Неверный формат даты.\n"
            "Используйте формат: ДД.ММ.ГГГГ\n"
            "Например: 25.09.2026"
        )
        return

    await state.update_data(comp_date=comp_date.strftime('%Y-%m-%d'))

    # Создаём клавиатуру с типами
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏃 Бег", callback_data="comptype:running"))
    builder.row(InlineKeyboardButton(text="🏊 Плавание", callback_data="comptype:swimming"))
    builder.row(InlineKeyboardButton(text="🚴 Велоспорт", callback_data="comptype:cycling"))
    builder.row(InlineKeyboardButton(text="🏊‍♂️🚴‍♂️🏃 Триатлон", callback_data="comptype:triathlon"))
    builder.row(InlineKeyboardButton(text="⛰️ Трейл", callback_data="comptype:trail"))

    from utils.date_formatter import get_user_date_format, DateFormatter
    coach_id = message.from_user.id
    user_date_format = await get_user_date_format(coach_id)
    formatted_date = DateFormatter.format_date(comp_date.strftime('%Y-%m-%d'), user_date_format)

    text = (
        f"✅ Дата: <b>{formatted_date}</b>\n\n"
        f"📝 <b>Шаг 3 из 5</b>\n\n"
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
        "cycling": "велоспорт",
        "triathlon": "триатлон",
        "trail": "трейл"
    }

    comp_type_key = callback.data.split(":")[1]
    comp_type = comp_type_map.get(comp_type_key, "бег")

    await state.update_data(comp_type=comp_type)

    text = (
        f"✅ Вид спорта: <b>{comp_type}</b>\n\n"
        f"📝 <b>Шаг 4 из 5</b>\n\n"
        f"Введите <b>дистанцию</b>:\n"
        f"<i>Например: 42.195 (для марафона)\n"
        f"Или: 21.1 (для полумарафона)\n"
        f"Или: 10 (для 10 км)</i>"
    )

    await callback.message.edit_text(text, parse_mode="HTML")
    await state.set_state(CompetitionStates.waiting_for_comp_distance)
    await callback.answer()


@router.message(CompetitionStates.waiting_for_comp_distance)
async def process_proposed_comp_distance(message: Message, state: FSMContext):
    """Обработать дистанцию предложенного соревнования"""

    # Проверяем что это flow от тренера
    data = await state.get_data()
    if 'propose_student_id' not in data:
        return

    distance_text = message.text.strip().replace(',', '.')

    try:
        distance = float(distance_text)

        if distance <= 0 or distance > 500:
            await message.answer(
                "❌ Дистанция должна быть от 0.1 до 500 км.\n"
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

    # Определяем название дистанции с учетом единиц измерения студента
    student_id = data.get('propose_student_id')
    from competitions.competitions_utils import format_competition_distance
    distance_name = await format_competition_distance(distance, student_id) if student_id else f"{distance} км"

    text = (
        f"✅ Дистанция: <b>{distance_name}</b>\n\n"
        f"📝 <b>Шаг 5 из 5</b>\n\n"
        f"Введите <b>рекомендуемое целевое время</b> для ученика:\n"
        f"<i>Формат: ЧЧ:ММ:СС\n"
        f"Например: 03:30:00 (3 часа 30 минут)\n"
        f"Или: 00:45:00 (45 минут)</i>\n\n"
        f"Или отправьте <b>0</b>, если не хотите указывать цель."
    )

    await message.answer(text, parse_mode="HTML")
    await state.set_state(CompetitionStates.waiting_for_comp_target)


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
                "Используйте формат: ЧЧ:ММ:СС (например: 03:30:00)\n"
                "Или отправьте 0, чтобы пропустить."
            )
            return

    # Получаем сохранённые данные
    student_id = data.get('propose_student_id')
    comp_name = data.get('comp_name')
    comp_date = data.get('comp_date')
    comp_type = data.get('comp_type')
    comp_distance = data.get('comp_distance')

    coach_id = message.from_user.id

    try:
        # Создаём соревнование в БД
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
            await db.execute(
                """
                INSERT INTO competition_participants
                (participant_id, competition_id, distance, target_time,
                 proposed_by_coach, proposed_by_coach_id, proposal_status, reminders_enabled)
                VALUES (?, ?, ?, ?, 1, ?, 'pending', 0)
                """,
                (student_id, comp_id, comp_distance, target_time, coach_id)
            )
            await db.commit()

        logger.info(f"Coach {coach_id} proposed competition {comp_id} to student {student_id}")

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
                callback_data=f"student:accept_comp:{comp_id}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=f"student:reject_comp:{comp_id}"
            )
        )

        await message.bot.send_message(
            student_id,
            notification_text,
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )

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


# ========== ОТВЕТ УЧЕНИКА НА ПРЕДЛОЖЕНИЕ ==========

@router.callback_query(F.data.startswith("student:accept_comp:"))
async def student_accept_competition(callback: CallbackQuery):
    """Ученик принимает предложение соревнования"""

    comp_id = int(callback.data.split(":")[2])
    student_id = callback.from_user.id

    import aiosqlite
    import os
    DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row

            # Получаем информацию о предложении
            async with db.execute(
                """
                SELECT cp.*, c.name, c.date, c.type, coach_id
                FROM competition_participants cp
                JOIN competitions c ON cp.competition_id = c.id
                WHERE cp.competition_id = ? AND cp.participant_id = ? AND cp.proposal_status = 'pending'
                """,
                (comp_id, student_id)
            ) as cursor:
                row = await cursor.fetchone()

            if not row:
                await callback.answer("Предложение не найдено", show_alert=True)
                return

            proposal = dict(row)
            coach_id = proposal.get('proposed_by_coach_id')

            # Обновляем статус и включаем напоминания
            await db.execute(
                """
                UPDATE competition_participants
                SET proposal_status = 'accepted', reminders_enabled = 1
                WHERE competition_id = ? AND participant_id = ?
                """,
                (comp_id, student_id)
            )
            await db.commit()

        # Создаём напоминания
        from competitions.reminder_scheduler import create_reminders_for_competition
        await create_reminders_for_competition(student_id, comp_id, proposal['date'])

        # Уведомляем тренера
        coach = await get_user(coach_id)
        student = await get_user(student_id)
        student_name = student.get('name') or student.get('username') or 'Ученик'

        await callback.bot.send_message(
            coach_id,
            f"✅ <b>Предложение принято!</b>\n\n"
            f"Ученик <b>{student_name}</b> принял участие в соревновании:\n"
            f"🏆 {proposal['name']}",
            parse_mode="HTML"
        )

        # Отвечаем ученику
        from utils.date_formatter import get_user_date_format, DateFormatter
        student_date_format = await get_user_date_format(student_id)
        formatted_date = DateFormatter.format_date(proposal['date'], student_date_format)

        text = (
            f"✅ <b>Вы приняли участие!</b>\n\n"
            f"🏆 <b>{proposal['name']}</b>\n"
            f"📅 Дата: {formatted_date}\n\n"
            f"🔔 Напоминания настроены. Вы будете получать уведомления перед соревнованием.\n\n"
            f"Соревнование добавлено в раздел 'Мои соревнования'."
        )

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="✅ Мои соревнования", callback_data="comp:my")
        )

        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
        await callback.answer("✅ Принято!")

    except Exception as e:
        logger.error(f"Error accepting competition proposal: {e}")
        await callback.answer("❌ Ошибка при принятии предложения", show_alert=True)


@router.callback_query(F.data.startswith("student:reject_comp:"))
async def student_reject_competition(callback: CallbackQuery):
    """Ученик отклоняет предложение соревнования"""

    comp_id = int(callback.data.split(":")[2])
    student_id = callback.from_user.id

    import aiosqlite
    import os
    DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row

            # Получаем информацию о предложении
            async with db.execute(
                """
                SELECT cp.*, c.name, coach_id
                FROM competition_participants cp
                JOIN competitions c ON cp.competition_id = c.id
                WHERE cp.competition_id = ? AND cp.participant_id = ? AND cp.proposal_status = 'pending'
                """,
                (comp_id, student_id)
            ) as cursor:
                row = await cursor.fetchone()

            if not row:
                await callback.answer("Предложение не найдено", show_alert=True)
                return

            proposal = dict(row)
            coach_id = proposal.get('proposed_by_coach_id')

            # Обновляем статус
            await db.execute(
                """
                UPDATE competition_participants
                SET proposal_status = 'rejected'
                WHERE competition_id = ? AND participant_id = ?
                """,
                (comp_id, student_id)
            )
            await db.commit()

        # Уведомляем тренера
        student = await get_user(student_id)
        student_name = student.get('name') or student.get('username') or 'Ученик'

        await callback.bot.send_message(
            coach_id,
            f"❌ <b>Предложение отклонено</b>\n\n"
            f"Ученик <b>{student_name}</b> отклонил участие в соревновании:\n"
            f"🏆 {proposal['name']}",
            parse_mode="HTML"
        )

        # Отвечаем ученику
        await callback.message.edit_text(
            f"❌ Вы отклонили предложение участия в соревновании:\n"
            f"🏆 <b>{proposal['name']}</b>",
            parse_mode="HTML"
        )
        await callback.answer("Отклонено")

    except Exception as e:
        logger.error(f"Error rejecting competition proposal: {e}")
        await callback.answer("❌ Ошибка при отклонении предложения", show_alert=True)
