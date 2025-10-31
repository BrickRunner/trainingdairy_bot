"""
Обработчики для добавления тренировок ученику тренером
"""

import logging
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from bot.fsm import CoachStates
from bot.keyboards import get_training_types_keyboard, get_date_keyboard, get_skip_keyboard, get_fatigue_keyboard
from coach.coach_training_queries import add_training_for_student, can_coach_access_student, get_student_display_name
from database.queries import get_main_training_types

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data.startswith("coach:add_training:"))
async def start_add_training_for_student(callback: CallbackQuery, state: FSMContext):
    """Начать процесс добавления тренировки для ученика"""
    student_id = int(callback.data.split(":")[2])
    coach_id = callback.from_user.id

    # Проверяем доступ
    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа к этому ученику", show_alert=True)
        return

    # Сохраняем student_id в состоянии
    await state.update_data(student_id=student_id, coach_id=coach_id)

    # Получаем основные типы тренировок ученика
    main_types = await get_main_training_types(student_id)
    display_name = await get_student_display_name(coach_id, student_id)

    await callback.message.edit_text(
        f"➕ <b>Добавление тренировки для {display_name}</b>\n\n"
        "Выберите тип тренировки:",
        reply_markup=get_training_types_keyboard(main_types if main_types else None),
        parse_mode="HTML"
    )
    await state.set_state(CoachStates.waiting_for_student_training_type)
    await callback.answer()


@router.callback_query(CoachStates.waiting_for_student_training_type, F.data.startswith("training_type:"))
async def process_training_type(callback: CallbackQuery, state: FSMContext):
    """Обработать выбор типа тренировки"""
    training_type = callback.data.split(":")[1]
    await state.update_data(type=training_type)

    await callback.message.answer(
        f"Выбран тип: {training_type.capitalize()}\n\n"
        "Выберите дату тренировки:",
        reply_markup=get_date_keyboard()
    )
    await state.set_state(CoachStates.waiting_for_student_training_date)
    await callback.answer()


@router.message(CoachStates.waiting_for_student_training_date)
async def process_training_date(message: Message, state: FSMContext):
    """Обработать дату тренировки"""
    text = message.text.strip()
    today = datetime.now().date()

    if text == "📅 Сегодня":
        date = today
    elif text == "📅 Вчера":
        date = today - timedelta(days=1)
    elif text == "📝 Ввести дату":
        await message.answer(
            "Введите дату в формате ДД.ММ.ГГГГ (например, 15.01.2025):",
            reply_markup=get_skip_keyboard()
        )
        return
    else:
        # Парсим введённую дату
        try:
            date = datetime.strptime(text, "%d.%m.%Y").date()
        except ValueError:
            await message.answer(
                "❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ",
                reply_markup=get_date_keyboard()
            )
            return

    await state.update_data(date=date.strftime("%Y-%m-%d"))

    await message.answer(
        f"Дата: {date.strftime('%d.%m.%Y')}\n\n"
        "Введите время начала (ЧЧ:ММ) или пропустите:",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(CoachStates.waiting_for_student_training_time)


@router.message(CoachStates.waiting_for_student_training_time)
async def process_training_time(message: Message, state: FSMContext):
    """Обработать время тренировки"""
    text = message.text.strip()

    if text == "⏭️ Пропустить":
        await state.update_data(time=None)
    else:
        # Проверяем формат времени
        import re
        if not re.match(r'^\d{1,2}:\d{2}$', text):
            await message.answer(
                "❌ Неверный формат. Используйте ЧЧ:ММ (например, 09:30)",
                reply_markup=get_skip_keyboard()
            )
            return
        await state.update_data(time=text)

    await message.answer(
        "Введите продолжительность тренировки в минутах:",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(CoachStates.waiting_for_student_training_duration)


@router.message(CoachStates.waiting_for_student_training_duration)
async def process_training_duration(message: Message, state: FSMContext):
    """Обработать продолжительность тренировки"""
    text = message.text.strip()

    if text == "❌ Отменить":
        await state.clear()
        await message.answer("❌ Добавление тренировки отменено")
        return

    try:
        duration = int(text)
        if duration <= 0:
            raise ValueError
    except ValueError:
        await message.answer(
            "❌ Введите корректное число минут",
            reply_markup=get_skip_keyboard()
        )
        return

    await state.update_data(duration=duration)

    # Проверяем тип тренировки
    data = await state.get_data()
    training_type = data.get('type')

    # Для кросса, плавания, велотренировки нужна дистанция
    if training_type in ['кросс', 'плавание', 'велотренировка']:
        await message.answer(
            f"Введите дистанцию в км:",
            reply_markup=get_skip_keyboard()
        )
        await state.set_state(CoachStates.waiting_for_student_training_distance)
    # Для силовой - упражнения
    elif training_type == 'силовая':
        await message.answer(
            "Введите описание упражнений или пропустите:",
            reply_markup=get_skip_keyboard()
        )
        await state.set_state(CoachStates.waiting_for_student_training_exercises)
    # Для интервальной - интервалы
    elif training_type == 'интервальная':
        await message.answer(
            "Введите описание интервалов (например, '10x400м') или пропустите:",
            reply_markup=get_skip_keyboard()
        )
        await state.set_state(CoachStates.waiting_for_student_training_intervals)
    else:
        # Сразу к пульсу
        await message.answer(
            "Введите средний пульс или пропустите:",
            reply_markup=get_skip_keyboard()
        )
        await state.set_state(CoachStates.waiting_for_student_training_avg_pulse)


@router.message(CoachStates.waiting_for_student_training_distance)
async def process_training_distance(message: Message, state: FSMContext):
    """Обработать дистанцию тренировки"""
    text = message.text.strip()

    if text == "⏭️ Пропустить":
        await state.update_data(distance=None, avg_pace=None)
    else:
        try:
            distance = float(text.replace(',', '.'))
            if distance <= 0:
                raise ValueError

            # Вычисляем темп
            data = await state.get_data()
            duration = data.get('duration')
            if duration and distance:
                avg_pace_minutes = duration / distance
                pace_min = int(avg_pace_minutes)
                pace_sec = int((avg_pace_minutes - pace_min) * 60)
                avg_pace = f"{pace_min:02d}:{pace_sec:02d}"
                await state.update_data(distance=distance, avg_pace=avg_pace, pace_unit='мин/км')
            else:
                await state.update_data(distance=distance, avg_pace=None)
        except ValueError:
            await message.answer(
                "❌ Введите корректное число (например, 10 или 10.5)",
                reply_markup=get_skip_keyboard()
            )
            return

    await message.answer(
        "Введите средний пульс или пропустите:",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(CoachStates.waiting_for_student_training_avg_pulse)


@router.message(CoachStates.waiting_for_student_training_exercises)
async def process_training_exercises(message: Message, state: FSMContext):
    """Обработать упражнения (силовая)"""
    text = message.text.strip()

    if text == "⏭️ Пропустить":
        await state.update_data(exercises=None)
    else:
        await state.update_data(exercises=text)

    await message.answer(
        "Введите средний пульс или пропустите:",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(CoachStates.waiting_for_student_training_avg_pulse)


@router.message(CoachStates.waiting_for_student_training_intervals)
async def process_training_intervals(message: Message, state: FSMContext):
    """Обработать интервалы"""
    text = message.text.strip()

    if text == "⏭️ Пропустить":
        await state.update_data(intervals=None)
    else:
        await state.update_data(intervals=text)

    await message.answer(
        "Введите средний пульс или пропустите:",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(CoachStates.waiting_for_student_training_avg_pulse)


@router.message(CoachStates.waiting_for_student_training_avg_pulse)
async def process_avg_pulse(message: Message, state: FSMContext):
    """Обработать средний пульс"""
    text = message.text.strip()

    if text == "⏭️ Пропустить":
        await state.update_data(avg_pulse=None)
    else:
        try:
            avg_pulse = int(text)
            if avg_pulse <= 0 or avg_pulse > 250:
                raise ValueError
            await state.update_data(avg_pulse=avg_pulse)
        except ValueError:
            await message.answer(
                "❌ Введите корректное значение пульса (40-250)",
                reply_markup=get_skip_keyboard()
            )
            return

    await message.answer(
        "Введите максимальный пульс или пропустите:",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(CoachStates.waiting_for_student_training_max_pulse)


@router.message(CoachStates.waiting_for_student_training_max_pulse)
async def process_max_pulse(message: Message, state: FSMContext):
    """Обработать максимальный пульс"""
    text = message.text.strip()

    if text == "⏭️ Пропустить":
        await state.update_data(max_pulse=None)
    else:
        try:
            max_pulse = int(text)
            if max_pulse <= 0 or max_pulse > 250:
                raise ValueError
            await state.update_data(max_pulse=max_pulse)
        except ValueError:
            await message.answer(
                "❌ Введите корректное значение пульса (40-250)",
                reply_markup=get_skip_keyboard()
            )
            return

    await message.answer(
        "Введите комментарий к тренировке или пропустите:",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(CoachStates.waiting_for_student_training_comment)


@router.message(CoachStates.waiting_for_student_training_comment)
async def process_training_comment(message: Message, state: FSMContext):
    """Обработать комментарий"""
    text = message.text.strip()

    if text == "⏭️ Пропустить":
        await state.update_data(comment=None)
    else:
        await state.update_data(comment=text)

    await message.answer(
        "Оцените предполагаемый уровень усилий (1-10):",
        reply_markup=get_fatigue_keyboard()
    )
    await state.set_state(CoachStates.waiting_for_student_training_fatigue)


@router.callback_query(CoachStates.waiting_for_student_training_fatigue, F.data.startswith("fatigue:"))
async def process_training_fatigue(callback: CallbackQuery, state: FSMContext):
    """Обработать уровень усилий и сохранить тренировку"""
    fatigue = int(callback.data.split(":")[1])
    await state.update_data(fatigue_level=fatigue)

    # Получаем все данные
    data = await state.get_data()
    student_id = data.get('student_id')
    coach_id = data.get('coach_id')

    # Подготавливаем данные тренировки
    training_data = {
        'type': data.get('type'),
        'date': data.get('date'),
        'time': data.get('time'),
        'duration': data.get('duration'),
        'distance': data.get('distance'),
        'avg_pace': data.get('avg_pace'),
        'pace_unit': data.get('pace_unit'),
        'avg_pulse': data.get('avg_pulse'),
        'max_pulse': data.get('max_pulse'),
        'exercises': data.get('exercises'),
        'intervals': data.get('intervals'),
        'calculated_volume': None,  # Вычислится автоматически
        'description': None,
        'results': None,
        'comment': data.get('comment'),
        'fatigue_level': fatigue,
        'is_planned': 1 if datetime.strptime(data.get('date'), "%Y-%m-%d").date() > datetime.now().date() else 0
    }

    # Сохраняем тренировку
    training_id = await add_training_for_student(coach_id, student_id, training_data)

    # Уведомляем ученика
    display_name = await get_student_display_name(coach_id, student_id)
    try:
        training_date = datetime.strptime(data.get('date'), "%Y-%m-%d").strftime("%d.%m.%Y")
        await callback.bot.send_message(
            student_id,
            f"👨‍🏫 <b>Новая тренировка от тренера</b>\n\n"
            f"Тип: {data.get('type').capitalize()}\n"
            f"Дата: {training_date}\n"
            f"Продолжительность: {data.get('duration')} мин\n"
            + (f"Дистанция: {data.get('distance')} км\n" if data.get('distance') else "")
            + (f"\n💬 Комментарий тренера:\n{data.get('comment')}" if data.get('comment') else ""),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Failed to notify student: {e}")

    await callback.message.edit_text(
        f"✅ <b>Тренировка добавлена!</b>\n\n"
        f"Ученик {display_name} получил уведомление.",
        parse_mode="HTML"
    )
    await state.clear()
    await callback.answer()
