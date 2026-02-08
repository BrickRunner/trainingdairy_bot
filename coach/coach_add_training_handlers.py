"""
Обработчики для добавления тренировок ученику тренером
"""

import logging
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from bot.fsm import CoachStates
from bot.keyboards import get_training_types_keyboard, get_date_keyboard, get_skip_keyboard, get_fatigue_keyboard
from bot.calendar_keyboard import CalendarKeyboard
from coach.coach_training_queries import add_training_for_student, can_coach_access_student, get_student_display_name
from database.queries import get_main_training_types

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data.startswith("coach:add_training:"))
async def start_add_training_for_student(callback: CallbackQuery, state: FSMContext):
    """Начать процесс назначения тренировки для ученика"""
    student_id = int(callback.data.split(":")[2])
    coach_id = callback.from_user.id

    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа к этому ученику", show_alert=True)
        return

    await state.update_data(student_id=student_id, coach_id=coach_id)

    main_types = await get_main_training_types(student_id)
    display_name = await get_student_display_name(coach_id, student_id)

    await callback.message.edit_text(
        f"➕ <b>Назначение тренировки для {display_name}</b>\n\n"
        "Выберите тип тренировки:",
        reply_markup=get_training_types_keyboard(main_types if main_types else None),
        parse_mode="HTML"
    )
    await state.set_state(CoachStates.waiting_for_student_training_type)
    await callback.answer()


@router.callback_query(CoachStates.waiting_for_student_training_type, F.data == "cancel")
async def cancel_add_training(callback: CallbackQuery, state: FSMContext):
    """Отменить добавление тренировки"""
    from coach.coach_keyboards import get_student_detail_keyboard
    from coach.coach_queries import get_coach_students
    from utils.date_formatter import get_user_date_format, DateFormatter

    data = await state.get_data()
    student_id = data.get('student_id')
    coach_id = data.get('coach_id')

    await state.clear()

    if student_id:
        students = await get_coach_students(coach_id)
        student = next((s for s in students if s['id'] == student_id), None)

        if student:
            display_name = await get_student_display_name(coach_id, student_id)
            coach_date_format = await get_user_date_format(coach_id)
            connected_date = DateFormatter.format_date(student['connected_at'][:10], coach_date_format)

            text = f"👤 <b>{display_name}</b>\n\n"
            text += f"📱 Telegram: @{student['username']}\n"
            text += f"📅 Подключён: {connected_date}\n"

            await callback.message.edit_text(
                text,
                reply_markup=get_student_detail_keyboard(student_id),
                parse_mode="HTML"
            )
    await callback.answer("❌ Назначение тренировки отменено")


@router.message(
    F.text == "❌ Отменить",
    F.or_(
        CoachStates.waiting_for_student_training_distance,
        CoachStates.waiting_for_student_training_exercises,
        CoachStates.waiting_for_student_training_intervals,
        CoachStates.waiting_for_student_training_max_pulse,
        CoachStates.waiting_for_student_training_comment
    )
)
async def cancel_add_training_text(message: Message, state: FSMContext):
    """Отменить добавление тренировки (текстовая кнопка)"""
    from coach.coach_keyboards import get_student_detail_keyboard
    from coach.coach_queries import get_coach_students
    from utils.date_formatter import get_user_date_format, DateFormatter
    from bot.keyboards import get_main_menu_keyboard
    from coach.coach_queries import is_user_coach

    data = await state.get_data()
    student_id = data.get('student_id')
    coach_id = data.get('coach_id')

    await state.clear()

    if student_id:
        students = await get_coach_students(coach_id)
        student = next((s for s in students if s['id'] == student_id), None)

        if student:
            display_name = await get_student_display_name(coach_id, student_id)
            coach_date_format = await get_user_date_format(coach_id)
            connected_date = DateFormatter.format_date(student['connected_at'][:10], coach_date_format)

            text = f"👤 <b>{display_name}</b>\n\n"
            text += f"📱 Telegram: @{student['username']}\n"
            text += f"📅 Подключён: {connected_date}\n"

            await message.answer(
                text,
                reply_markup=get_student_detail_keyboard(student_id),
                parse_mode="HTML"
            )

            is_coach = await is_user_coach(coach_id)
            await message.answer(
                "Главное меню:",
                reply_markup=get_main_menu_keyboard(is_coach)
            )

    await message.answer("❌ Назначение тренировки отменено")


@router.callback_query(CoachStates.waiting_for_student_training_type, F.data.startswith("training_type:"))
async def process_training_type(callback: CallbackQuery, state: FSMContext):
    """Обработать выбор типа тренировки"""
    training_type = callback.data.split(":")[1]
    await state.update_data(type=training_type)

    calendar = CalendarKeyboard.create_calendar(
        1,
        datetime.now(),
        "coach_cal"
    )
    await callback.message.answer(
        f"📅 <b>На какую дату назначить тренировку?</b>\n\n"
        f"Тип: {training_type.capitalize()}\n\n"
        "Выберите дату из календаря (только сегодня или будущее):",
        reply_markup=calendar,
        parse_mode="HTML"
    )

    await callback.message.answer(
        "Или выберите быстрый вариант:",
        reply_markup=get_date_keyboard(for_coach=True)
    )

    await state.set_state(CoachStates.waiting_for_student_training_date)
    await callback.answer()


@router.callback_query(CoachStates.waiting_for_student_training_date, F.data.startswith("coach_cal_1_select_"))
async def process_calendar_date_selection(callback: CallbackQuery, state: FSMContext):
    """Обработать выбор даты из календаря"""
    parsed = CalendarKeyboard.parse_callback_data(callback.data.replace("coach_cal_", "cal_"))
    selected_date = parsed.get("date")

    if not selected_date:
        await callback.answer("❌ Ошибка при выборе даты", show_alert=True)
        return

    today = datetime.now().date()
    if selected_date.date() < today:
        await callback.answer("❌ Нельзя назначить тренировку на прошлую дату", show_alert=True)
        return

    await state.update_data(date=selected_date.date().isoformat())

    from utils.date_formatter import DateFormatter, get_user_date_format
    coach_id = callback.from_user.id
    date_format = await get_user_date_format(coach_id)
    date_str = DateFormatter.format_date(selected_date.date(), date_format)

    await callback.answer()

    data = await state.get_data()
    training_type = data.get('type')

    if training_type in ['кросс', 'плавание', 'велотренировка']:
        student_id = data.get('student_id')
        from database.queries import get_user_settings
        student_settings = await get_user_settings(student_id)
        distance_unit = student_settings.get('distance_unit', 'км') if student_settings else 'км'
        unit_prepositional = 'километрах' if distance_unit == 'км' else 'милях'

        await callback.message.answer(
            f"📅 Дата: {date_str}\n\n"
            f"Введите плановую дистанцию в {unit_prepositional} или пропустите:",
            reply_markup=get_skip_keyboard()
        )
        await state.set_state(CoachStates.waiting_for_student_training_distance)
    elif training_type == 'силовая':
        await callback.message.answer(
            f"📅 Дата: {date_str}\n\n"
            "Введите плановые упражнения или пропустите:",
            reply_markup=get_skip_keyboard()
        )
        await state.set_state(CoachStates.waiting_for_student_training_exercises)
    elif training_type == 'интервальная':
        await callback.message.answer(
            f"📅 Дата: {date_str}\n\n"
            "Введите плановые интервалы (например, '10x400м') или пропустите:",
            reply_markup=get_skip_keyboard()
        )
        await state.set_state(CoachStates.waiting_for_student_training_intervals)
    else:
        await callback.message.answer(
            f"📅 Дата: {date_str}\n\n"
            "Введите комментарий или пропустите:",
            reply_markup=get_skip_keyboard()
        )
        await state.set_state(CoachStates.waiting_for_student_training_comment)


@router.callback_query(CoachStates.waiting_for_student_training_date, F.data.startswith("coach_cal"))
async def process_calendar_navigation(callback: CallbackQuery, state: FSMContext):
    """Обработать навигацию по календарю"""
    if callback.data == "coach_cal_empty" or callback.data.endswith("_empty"):
        await callback.answer()
        return

    callback_data_normalized = callback.data.replace("coach_cal_", "cal_")
    new_keyboard = CalendarKeyboard.handle_navigation(
        callback_data_normalized,
        prefix="cal"
    )

    if new_keyboard:
        final_keyboard = CalendarKeyboard.replace_prefix_in_keyboard(new_keyboard, "cal", "coach_cal")

        try:
            await callback.message.edit_reply_markup(reply_markup=final_keyboard)
        except Exception as e:
            if "message is not modified" not in str(e).lower():
                logger.error(f"Ошибка при обновлении календаря: {str(e)}")

    await callback.answer()


@router.message(CoachStates.waiting_for_student_training_date)
async def process_date_text(message: Message, state: FSMContext):
    """Обработать выбор даты через текстовые кнопки"""
    if message.text == "❌ Отменить":
        from coach.coach_keyboards import get_student_detail_keyboard
        from bot.keyboards import get_main_menu_keyboard
        from coach.coach_queries import is_user_coach

        data = await state.get_data()
        student_id = data.get('student_id')
        coach_id = data.get('coach_id')

        await state.clear()

        if student_id:
            display_name = await get_student_display_name(coach_id, student_id)
            text = f"👤 <b>{display_name}</b>\n\nВыберите действие:"

            await message.answer(
                text,
                reply_markup=get_student_detail_keyboard(student_id),
                parse_mode="HTML"
            )
            is_coach = await is_user_coach(coach_id)
            await message.answer(
                "Главное меню:",
                reply_markup=get_main_menu_keyboard(is_coach)
            )
        return

    from utils.date_formatter import get_user_date_format, DateFormatter
    coach_id = message.from_user.id
    date_format = await get_user_date_format(coach_id)

    utc_now = datetime.utcnow()
    moscow_now = utc_now + timedelta(hours=3)
    today = moscow_now.date()
    tomorrow = today + timedelta(days=1)

    if message.text == "📅 Сегодня":
        date = today
    elif message.text == "📅 Завтра":
        date = tomorrow
    elif message.text == "📅 Вчера":
        await message.answer(
            "❌ Нельзя назначить тренировку на прошлую дату.\n"
            "Выберите сегодня или будущую дату.",
            reply_markup=get_date_keyboard(for_coach=True)
        )
        return
    elif message.text == "📝 Ввести дату":
        format_desc = DateFormatter.get_format_description(date_format)
        await message.answer(
            f"Введите дату в формате {format_desc}:",
            reply_markup=get_skip_keyboard()
        )
        return
    else:
        date = DateFormatter.parse_date(message.text, date_format)
        if not date:
            format_desc = DateFormatter.get_format_description(date_format)
            await message.answer(
                f"❌ Неверный формат даты. Используйте {format_desc}",
                reply_markup=get_date_keyboard(for_coach=True)
            )
            return

        if date < today:
            await message.answer(
                "❌ Нельзя назначить тренировку на прошлую дату.\n"
                "Выберите сегодня или будущую дату.",
                reply_markup=get_date_keyboard(for_coach=True)
            )
            return

    await state.update_data(date=date.isoformat())
    date_str = DateFormatter.format_date(date, date_format)

    data = await state.get_data()
    training_type = data.get('type')
    student_id = data.get('student_id')

    if training_type in ['кросс', 'плавание', 'велотренировка']:
        from database.queries import get_user_settings
        student_settings = await get_user_settings(student_id)
        distance_unit = student_settings.get('distance_unit', 'км') if student_settings else 'км'
        unit_prepositional = 'километрах' if distance_unit == 'км' else 'милях'

        await message.answer(
            f"📅 Дата: {date_str}\n\n"
            f"Введите плановую дистанцию в {unit_prepositional} или пропустите:",
            reply_markup=get_skip_keyboard()
        )
        await state.set_state(CoachStates.waiting_for_student_training_distance)
    elif training_type == 'силовая':
        await message.answer(
            f"📅 Дата: {date_str}\n\n"
            "Введите плановые упражнения или пропустите:",
            reply_markup=get_skip_keyboard()
        )
        await state.set_state(CoachStates.waiting_for_student_training_exercises)
    elif training_type == 'интервальная':
        await message.answer(
            f"📅 Дата: {date_str}\n\n"
            "Введите плановые интервалы (например, '10x400м') или пропустите:",
            reply_markup=get_skip_keyboard()
        )
        await state.set_state(CoachStates.waiting_for_student_training_intervals)
    else:
        await message.answer(
            f"📅 Дата: {date_str}\n\n"
            "Введите комментарий или пропустите:",
            reply_markup=get_skip_keyboard()
        )
        await state.set_state(CoachStates.waiting_for_student_training_comment)


@router.message(CoachStates.waiting_for_student_training_distance)
async def process_training_distance(message: Message, state: FSMContext):
    """Обработать плановую дистанцию"""
    text = message.text.strip()

    if text == "⏭️ Пропустить":
        await state.update_data(distance=None)
    else:
        try:
            distance = float(text.replace(',', '.'))
            if distance <= 0:
                raise ValueError
            await state.update_data(distance=distance)
        except ValueError:
            await message.answer(
                "❌ Введите корректное число (например, 10 или 10.5)",
                reply_markup=get_skip_keyboard()
            )
            return

    data = await state.get_data()
    student_id = data.get('student_id')
    from database.queries import get_user_settings
    student_settings = await get_user_settings(student_id)
    distance_unit = student_settings.get('distance_unit', 'км') if student_settings else 'км'
    pace_unit = 'мин/миля' if distance_unit == 'мили' else 'мин/км'

    await message.answer(
        f"Введите желаемый темп ({pace_unit}) в формате ММ:СС или пропустите:\n\n"
        f"Например: 05:30",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(CoachStates.waiting_for_student_training_max_pulse)  


@router.message(CoachStates.waiting_for_student_training_exercises)
async def process_training_exercises(message: Message, state: FSMContext):
    """Обработать упражнения (силовая)"""
    text = message.text.strip()

    if text == "⏭️ Пропустить":
        await state.update_data(exercises=None)
    else:
        await state.update_data(exercises=text)

    await message.answer(
        "Введите комментарий к тренировке или пропустите:",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(CoachStates.waiting_for_student_training_comment)


@router.message(CoachStates.waiting_for_student_training_intervals)
async def process_training_intervals(message: Message, state: FSMContext):
    """Обработать интервалы"""
    text = message.text.strip()

    if text == "⏭️ Пропустить":
        await state.update_data(intervals=None)
    else:
        await state.update_data(intervals=text)

    await message.answer(
        "Введите комментарий (можно указать желаемые результаты) или пропустите:",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(CoachStates.waiting_for_student_training_comment)


@router.message(CoachStates.waiting_for_student_training_max_pulse)
async def process_desired_pace(message: Message, state: FSMContext):
    """Обработать желаемый темп"""
    text = message.text.strip()

    if text == "⏭️ Пропустить":
        await state.update_data(avg_pace=None, pace_unit=None)
    else:
        import re
        pace_pattern = r'^(\d{1,2}):([0-5]\d)$'
        match = re.match(pace_pattern, text)

        if not match:
            await message.answer(
                "❌ Введите темп в формате ММ:СС (например, 05:30)",
                reply_markup=get_skip_keyboard()
            )
            return

        data = await state.get_data()
        student_id = data.get('student_id')
        from database.queries import get_user_settings
        student_settings = await get_user_settings(student_id)
        distance_unit = student_settings.get('distance_unit', 'км') if student_settings else 'км'
        pace_unit = 'мин/миля' if distance_unit == 'мили' else 'мин/км'

        await state.update_data(avg_pace=text, pace_unit=pace_unit)

    await message.answer(
        "Введите комментарий к тренировке или пропустите:",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(CoachStates.waiting_for_student_training_comment)


@router.message(CoachStates.waiting_for_student_training_comment)
async def process_training_comment(message: Message, state: FSMContext):
    """Обработать комментарий и сохранить тренировку"""
    text = message.text.strip()

    if text == "⏭️ Пропустить":
        await state.update_data(comment=None)
    else:
        await state.update_data(comment=text)

    data = await state.get_data()
    student_id = data.get('student_id')
    coach_id = data.get('coach_id')

    training_data = {
        'type': data.get('type'),
        'date': data.get('date'),
        'time': None,  
        'duration': None,  
        'distance': data.get('distance'),  
        'avg_pace': data.get('avg_pace'),  
        'pace_unit': data.get('pace_unit'),
        'avg_pulse': None,  
        'max_pulse': None,
        'exercises': data.get('exercises'),  
        'intervals': data.get('intervals'),  
        'calculated_volume': None,
        'description': None,
        'results': None,
        'comment': data.get('comment'),  
        'fatigue_level': None,  
        'is_planned': 1  
    }

    training_id = await add_training_for_student(coach_id, student_id, training_data)

    display_name = await get_student_display_name(coach_id, student_id)
    try:
        from utils.date_formatter import get_user_date_format, DateFormatter
        from database.queries import get_user_settings

        user_date_format = await get_user_date_format(student_id)
        date_str = DateFormatter.format_date(data.get('date'), user_date_format)

        student_settings = await get_user_settings(student_id)
        coach_settings = await get_user_settings(coach_id)

        distance_unit = student_settings.get('distance_unit', 'км') if student_settings else 'км'
        coach_name = coach_settings.get('name') if coach_settings else 'Ваш тренер'

        training_desc = f"📝 <b>Тип:</b> {data.get('type').capitalize()}\n"
        training_desc += f"📅 <b>Дата:</b> {date_str}\n"

        if data.get('distance'):
            training_desc += f"📏 <b>Плановая дистанция:</b> {data.get('distance')} {distance_unit}\n"

        if data.get('avg_pace'):
            training_desc += f"⏱ <b>Желаемый темп:</b> {data.get('avg_pace')} {data.get('pace_unit', 'мин/км')}\n"

        if data.get('exercises'):
            training_desc += f"💪 <b>Плановые упражнения:</b> {data.get('exercises')}\n"

        if data.get('intervals'):
            training_desc += f"🔄 <b>Плановые интервалы:</b> {data.get('intervals')}\n"

        if data.get('comment'):
            training_desc += f"💬 <b>Комментарий тренера:</b> {data.get('comment')}\n"

        notification_text = (
            f"📋 <b>Запланирована тренировка</b>\n\n"
            f"<b>{coach_name}</b> запланировал для вас тренировку:\n\n"
            f"{training_desc}\n"
            f"⚡️ В день тренировки заполните фактические данные в разделе «Добавить тренировку»"
        )

        await message.bot.send_message(
            student_id,
            notification_text,
            parse_mode="HTML"
        )

        from coach.coach_queries import is_user_coach
        from bot.keyboards import get_main_menu_keyboard

        student_is_coach = await is_user_coach(student_id)
        await message.bot.send_message(
            student_id,
            "Главное меню:",
            reply_markup=get_main_menu_keyboard(student_is_coach)
        )
    except Exception as e:
        logger.error(f"Failed to send notification to student {student_id}: {e}")

    from coach.coach_keyboards import get_student_detail_keyboard

    await message.answer(
        f"✅ <b>Тренировка запланирована!</b>\n\n"
        f"Ученик <b>{display_name}</b> получил уведомление.\n\n"
        f"📅 Дата: {DateFormatter.format_date(data.get('date'), await get_user_date_format(coach_id))}\n"
        f"📝 В день тренировки ученик заполнит фактические данные.",
        parse_mode="HTML",
        reply_markup=get_student_detail_keyboard(student_id)
    )

    await state.clear()
