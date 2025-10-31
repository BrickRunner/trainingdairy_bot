"""
Обработчики для работы с тренерским разделом
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from coach.coach_keyboards import (
    get_coach_main_menu,
    get_students_list_keyboard,
    get_student_detail_keyboard,
    get_confirm_remove_student_keyboard,
    get_add_coach_keyboard,
    get_student_coach_info_keyboard,
    get_confirm_remove_coach_keyboard
)
from coach.coach_queries import (
    is_user_coach,
    get_coach_link_code,
    get_coach_students,
    remove_student_from_coach,
    find_coach_by_code,
    add_student_to_coach,
    get_student_coach,
    remove_coach_from_student
)
from bot.fsm import CoachStates
from database.queries import get_user

logger = logging.getLogger(__name__)
router = Router()


# ========== ТРЕНЕРСКАЯ СТОРОНА ==========

@router.callback_query(F.data == "coach:menu")
async def show_coach_menu(callback: CallbackQuery):
    """Показать главное меню тренера"""
    user_id = callback.from_user.id

    # Проверяем что пользователь тренер
    if not await is_user_coach(user_id):
        await callback.answer("У вас нет доступа к этому разделу", show_alert=True)
        return

    await callback.message.edit_text(
        "👨‍🏫 <b>Раздел тренера</b>\n\n"
        "Здесь вы можете управлять своими учениками, "
        "просматривать их тренировки и прогресс.",
        reply_markup=get_coach_main_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "coach:students")
async def show_students_list(callback: CallbackQuery):
    """Показать список учеников"""
    user_id = callback.from_user.id

    students = await get_coach_students(user_id)

    if not students:
        await callback.message.edit_text(
            "👥 <b>Мои ученики</b>\n\n"
            "У вас пока нет учеников.\n\n"
            "Чтобы добавить ученика, отправьте ему свою ссылку:\n"
            "👉 Тренер → Ссылка для учеников",
            reply_markup=get_students_list_keyboard([])
        )
    else:
        text = f"👥 <b>Мои ученики</b> ({len(students)})\n\n"
        text += "Выберите ученика для просмотра:\n"

        await callback.message.edit_text(
            text,
            reply_markup=get_students_list_keyboard(students)
        )

    await callback.answer()


@router.callback_query(F.data.startswith("coach:student:"))
async def show_student_detail(callback: CallbackQuery):
    """Показать детали ученика"""
    from coach.coach_training_queries import get_student_display_name

    student_id = int(callback.data.split(":")[2])
    coach_id = callback.from_user.id

    # Проверяем что это ученик данного тренера
    students = await get_coach_students(coach_id)
    student = next((s for s in students if s['id'] == student_id), None)

    if not student:
        await callback.answer("Ученик не найден", show_alert=True)
        return

    # Получаем отображаемое имя (с учётом псевдонима)
    display_name = await get_student_display_name(coach_id, student_id)

    user_info = await get_user(student_id)

    text = f"👤 <b>{display_name}</b>\n\n"
    text += f"📱 Telegram: @{student['username']}\n"
    text += f"📅 Подключён: {student['connected_at'][:10]}\n"

    await callback.message.edit_text(
        text,
        reply_markup=get_student_detail_keyboard(student_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("coach:student_trainings:"))
async def show_student_trainings(callback: CallbackQuery):
    """Показать тренировки ученика"""
    from coach.coach_training_queries import get_student_trainings, can_coach_access_student, get_student_display_name
    from coach.coach_keyboards import get_student_trainings_keyboard

    student_id = int(callback.data.split(":")[2])
    coach_id = callback.from_user.id

    # Проверяем доступ
    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа к этому ученику", show_alert=True)
        return

    # Получаем тренировки
    trainings = await get_student_trainings(student_id, limit=30)
    display_name = await get_student_display_name(coach_id, student_id)

    if not trainings:
        await callback.message.edit_text(
            f"📊 <b>Тренировки: {display_name}</b>\n\n"
            "У ученика пока нет тренировок.",
            reply_markup=get_student_trainings_keyboard(student_id, []),
            parse_mode="HTML"
        )
    else:
        text = f"📊 <b>Тренировки: {display_name}</b>\n\n"
        text += f"Последние {len(trainings)} тренировок:\n\n"

        await callback.message.edit_text(
            text,
            reply_markup=get_student_trainings_keyboard(student_id, trainings),
            parse_mode="HTML"
        )

    await callback.answer()


@router.callback_query(F.data.startswith("coach:student_stats:"))
async def show_student_stats(callback: CallbackQuery):
    """Показать статистику ученика"""
    student_id = int(callback.data.split(":")[2])

    # TODO: Реализовать просмотр статистики ученика
    await callback.answer("Статистика в разработке", show_alert=True)


@router.callback_query(F.data.startswith("coach:student_health:"))
async def show_student_health(callback: CallbackQuery):
    """Показать данные о здоровье ученика"""
    student_id = int(callback.data.split(":")[2])

    # TODO: Реализовать просмотр здоровья ученика
    await callback.answer("Просмотр здоровья в разработке", show_alert=True)


@router.callback_query(F.data.startswith("coach:remove_student:"))
async def confirm_remove_student(callback: CallbackQuery):
    """Подтверждение удаления ученика"""
    student_id = int(callback.data.split(":")[2])
    coach_id = callback.from_user.id

    students = await get_coach_students(coach_id)
    student = next((s for s in students if s['id'] == student_id), None)

    if not student:
        await callback.answer("Ученик не найден", show_alert=True)
        return

    await callback.message.edit_text(
        f"Вы уверены, что хотите удалить ученика <b>{student['name']}</b>?\n\n"
        f"После удаления ученик больше не сможет видеть ваши рекомендации.",
        reply_markup=get_confirm_remove_student_keyboard(student_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("coach:confirm_remove:"))
async def remove_student(callback: CallbackQuery):
    """Удалить ученика"""
    student_id = int(callback.data.split(":")[2])
    coach_id = callback.from_user.id

    await remove_student_from_coach(coach_id, student_id)

    await callback.message.edit_text(
        "✅ Ученик удалён",
        reply_markup=get_students_list_keyboard([])
    )
    await callback.answer()


@router.callback_query(F.data == "coach:link")
async def show_coach_link(callback: CallbackQuery):
    """Показать ссылку для подключения учеников"""
    user_id = callback.from_user.id

    link_code = await get_coach_link_code(user_id)

    if not link_code:
        await callback.answer("Ошибка: код не найден", show_alert=True)
        return

    bot_username = (await callback.bot.me()).username

    text = "🔗 <b>Ваша ссылка для учеников</b>\n\n"
    text += f"Отправьте эту ссылку своим ученикам:\n\n"
    text += f"<code>https://t.me/{bot_username}?start=coach_{link_code}</code>\n\n"
    text += f"Или код для ввода вручную:\n"
    text += f"<code>{link_code}</code>\n\n"
    text += "После перехода по ссылке ученик автоматически подключится к вам."

    await callback.message.edit_text(
        text,
        reply_markup=get_coach_main_menu()
    )
    await callback.answer()


# ========== УЧЕНИЧЕСКАЯ СТОРОНА ==========

@router.callback_query(F.data == "student:my_coach")
async def show_my_coach(callback: CallbackQuery):
    """Показать информацию о тренере"""
    user_id = callback.from_user.id

    coach = await get_student_coach(user_id)

    if not coach:
        text = "👨‍🏫 <b>Мой тренер</b>\n\n"
        text += "У вас пока нет тренера.\n\n"
        text += "Чтобы добавить тренера, попросите у него код "
        text += "или ссылку для подключения."

        await callback.message.edit_text(
            text,
            reply_markup=get_add_coach_keyboard()
        )
    else:
        text = f"👨‍🏫 <b>Мой тренер</b>\n\n"
        text += f"👤 Имя: {coach['name']}\n"
        text += f"📱 Telegram: @{coach['username']}\n\n"
        text += "Ваш тренер может просматривать ваши тренировки и статистику."

        await callback.message.edit_text(
            text,
            reply_markup=get_student_coach_info_keyboard()
        )

    await callback.answer()


@router.callback_query(F.data == "student:add_coach")
async def add_coach_prompt(callback: CallbackQuery, state: FSMContext):
    """Запросить код тренера"""
    await callback.message.edit_text(
        "✏️ <b>Добавление тренера</b>\n\n"
        "Введите код тренера, который он вам отправил:",
    )
    await state.set_state(CoachStates.waiting_for_coach_code)
    await callback.answer()


@router.message(CoachStates.waiting_for_coach_code)
async def process_coach_code(message: Message, state: FSMContext):
    """Обработать введённый код тренера"""
    code = message.text.strip().upper()

    # Ищем тренера по коду
    coach_id = await find_coach_by_code(code)

    if not coach_id:
        await message.answer(
            "❌ Код тренера не найден.\n\n"
            "Проверьте правильность кода и попробуйте снова."
        )
        return

    # Добавляем связь
    student_id = message.from_user.id
    success = await add_student_to_coach(coach_id, student_id)

    if success:
        coach = await get_user(coach_id)
        await message.answer(
            f"✅ Вы успешно подключились к тренеру!\n\n"
            f"Ваш тренер: {coach.get('username', 'Неизвестно')}\n\n"
            f"Теперь тренер может просматривать ваши тренировки и статистику."
        )

        # Уведомляем тренера
        try:
            student_name = message.from_user.full_name
            await message.bot.send_message(
                coach_id,
                f"🎉 Новый ученик!\n\n"
                f"К вам подключился: {student_name}"
            )
        except Exception as e:
            logger.error(f"Failed to notify coach: {e}")
    else:
        await message.answer(
            "⚠️ Вы уже подключены к этому тренеру."
        )

    await state.clear()


@router.callback_query(F.data == "student:remove_coach")
async def confirm_remove_coach(callback: CallbackQuery):
    """Подтверждение отключения от тренера"""
    await callback.message.edit_text(
        "Вы уверены, что хотите отключиться от тренера?\n\n"
        "После этого тренер больше не сможет видеть ваши данные.",
        reply_markup=get_confirm_remove_coach_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "student:confirm_remove_coach")
async def remove_coach(callback: CallbackQuery):
    """Отключиться от тренера"""
    user_id = callback.from_user.id

    await remove_coach_from_student(user_id)

    await callback.message.edit_text(
        "✅ Вы отключились от тренера",
        reply_markup=get_add_coach_keyboard()
    )
    await callback.answer()


# ========== НОВЫЕ ФУНКЦИИ: ПСЕВДОНИМ, КОММЕНТАРИИ, ДОБАВЛЕНИЕ ТРЕНИРОВОК ==========

@router.callback_query(F.data.startswith("coach:edit_nickname:"))
async def edit_nickname_prompt(callback: CallbackQuery, state: FSMContext):
    """Запросить новый псевдоним для ученика"""
    from coach.coach_training_queries import get_student_display_name

    student_id = int(callback.data.split(":")[2])
    coach_id = callback.from_user.id

    # Сохраняем student_id в состоянии
    await state.update_data(student_id=student_id)

    display_name = await get_student_display_name(coach_id, student_id)

    await callback.message.edit_text(
        f"✏️ <b>Изменение псевдонима</b>\n\n"
        f"Текущее отображаемое имя: {display_name}\n\n"
        f"Введите новый псевдоним для ученика:\n"
        f"(Псевдоним будет виден только вам)",
        parse_mode="HTML"
    )
    await state.set_state(CoachStates.waiting_for_nickname)
    await callback.answer()


@router.message(CoachStates.waiting_for_nickname)
async def process_nickname(message: Message, state: FSMContext):
    """Обработать введённый псевдоним"""
    from coach.coach_training_queries import set_student_nickname

    data = await state.get_data()
    student_id = data.get('student_id')
    coach_id = message.from_user.id
    nickname = message.text.strip()

    await set_student_nickname(coach_id, student_id, nickname)

    await message.answer(
        f"✅ Псевдоним изменён на: {nickname}\n\n"
        f"Теперь ученик будет отображаться под этим именем."
    )

    await state.clear()


@router.callback_query(F.data.startswith("coach:training_detail:"))
async def show_training_detail(callback: CallbackQuery):
    """Показать детали тренировки ученика"""
    from coach.coach_training_queries import get_training_with_comments, can_coach_access_student
    from coach.coach_keyboards import get_training_detail_keyboard

    parts = callback.data.split(":")
    training_id = int(parts[2])
    student_id = int(parts[3])
    coach_id = callback.from_user.id

    # Проверяем доступ
    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    training = await get_training_with_comments(training_id)
    if not training:
        await callback.answer("Тренировка не найдена", show_alert=True)
        return

    # Форматируем информацию о тренировке
    text = f"📊 <b>Тренировка: {training['type'].capitalize()}</b>\n\n"
    text += f"📅 Дата: {training['date']}\n"
    text += f"⏱ Продолжительность: {training['duration']} мин\n"

    if training.get('distance'):
        text += f"📏 Дистанция: {training['distance']} км\n"

    if training.get('avg_pace'):
        text += f"⚡ Средний темп: {training['avg_pace']} мин/км\n"

    if training.get('avg_pulse'):
        text += f"💓 Средний пульс: {training['avg_pulse']} bpm\n"

    if training.get('max_pulse'):
        text += f"💗 Максимальный пульс: {training['max_pulse']} bpm\n"

    if training.get('added_by_coach_id'):
        text += f"\n👨‍🏫 Добавлено тренером: {training.get('coach_username', 'вами')}\n"

    if training.get('comment'):
        text += f"\n💬 Комментарий ученика:\n{training['comment']}\n"

    # Комментарии тренера
    comments = training.get('comments', [])
    if comments:
        text += f"\n💬 <b>Комментарии ({len(comments)}):</b>\n"
        for comment in comments:
            author_name = comment.get('author_name') or comment.get('author_username')
            text += f"\n<i>{author_name}:</i> {comment['comment']}\n"

    await callback.message.edit_text(
        text,
        reply_markup=get_training_detail_keyboard(training_id, student_id, len(comments)),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("coach:add_comment:"))
async def add_comment_prompt(callback: CallbackQuery, state: FSMContext):
    """Запросить комментарий к тренировке"""
    parts = callback.data.split(":")
    training_id = int(parts[2])
    student_id = int(parts[3])

    # Сохраняем в состоянии
    await state.update_data(training_id=training_id, student_id=student_id)

    await callback.message.edit_text(
        "💬 <b>Добавление комментария</b>\n\n"
        "Введите ваш комментарий к тренировке:",
        parse_mode="HTML"
    )
    await state.set_state(CoachStates.waiting_for_comment)
    await callback.answer()


@router.message(CoachStates.waiting_for_comment)
async def process_comment(message: Message, state: FSMContext):
    """Обработать введённый комментарий"""
    from coach.coach_training_queries import add_comment_to_training

    data = await state.get_data()
    training_id = data.get('training_id')
    student_id = data.get('student_id')
    coach_id = message.from_user.id
    comment_text = message.text.strip()

    # Добавляем комментарий
    await add_comment_to_training(training_id, coach_id, comment_text)

    # Уведомляем ученика
    try:
        await message.bot.send_message(
            student_id,
            f"💬 <b>Новый комментарий от тренера</b>\n\n"
            f"К вашей тренировке добавлен комментарий:\n\n"
            f"<i>{comment_text}</i>",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Failed to notify student: {e}")

    await message.answer("✅ Комментарий добавлен! Ученик получил уведомление.")

    await state.clear()


@router.callback_query(F.data.startswith("coach:student_stats:"))
async def show_student_stats_menu(callback: CallbackQuery):
    """Показать меню выбора периода для статистики ученика"""
    from coach.coach_training_queries import can_coach_access_student, get_student_display_name
    from coach.coach_keyboards import get_student_stats_period_keyboard

    student_id = int(callback.data.split(":")[2])
    coach_id = callback.from_user.id

    # Проверяем доступ
    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    display_name = await get_student_display_name(coach_id, student_id)

    await callback.message.edit_text(
        f"📈 <b>Статистика ученика {display_name}</b>\n\n"
        f"Выберите период для просмотра:",
        parse_mode="HTML",
        reply_markup=get_student_stats_period_keyboard(student_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("coach:stats_period:"))
async def show_student_statistics(callback: CallbackQuery):
    """Показать статистику ученика за выбранный период"""
    from coach.coach_training_queries import can_coach_access_student, get_student_display_name
    from database.queries import get_training_statistics, get_user_settings
    from utils.unit_converter import format_distance
    from datetime import datetime, timedelta

    parts = callback.data.split(":")
    student_id = int(parts[2])
    period = parts[3]
    coach_id = callback.from_user.id

    # Проверяем доступ
    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    display_name = await get_student_display_name(coach_id, student_id)

    # Получаем настройки ученика для единиц измерения
    settings = await get_user_settings(student_id)
    distance_unit = settings.get('distance_unit', 'км') if settings else 'км'

    # Получаем статистику
    stats = await get_training_statistics(student_id, period)

    period_names = {"week": "неделю", "2weeks": "2 недели", "month": "месяц"}
    period_name = period_names.get(period, "период")

    if stats['total_count'] == 0:
        await callback.message.edit_text(
            f"📈 <b>Статистика {display_name}</b>\n\n"
            f"За {period_name} нет тренировок.",
            parse_mode="HTML",
            reply_markup=get_student_stats_period_keyboard(student_id)
        )
        await callback.answer()
        return

    # Определяем начальную дату периода для отображения
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

    # Формируем сообщение с статистикой
    message_text = f"📈 <b>Статистика {display_name}</b>\n"
    message_text += f"📅 Период: {period_display}\n\n"
    message_text += "━━━━━━━━━━━━━━━━━━\n"
    message_text += "📊 <b>ОБЩАЯ СТАТИСТИКА</b>\n"
    message_text += "━━━━━━━━━━━━━━━━━━\n\n"

    # 1. Общее количество тренировок
    message_text += f"🏃 Всего тренировок: <b>{stats['total_count']}</b>\n"

    # 2. Общий километраж
    if stats['total_distance'] > 0:
        message_text += f"📏 Общий километраж: <b>{format_distance(stats['total_distance'], distance_unit)}</b>\n"

        # Для периодов больше недели показываем средний км за неделю
        if period in ['2weeks', 'month']:
            days_in_period = (today - start_date).days + 1
            weeks_count = days_in_period / 7

            if weeks_count > 0:
                avg_per_week = stats['total_distance'] / weeks_count
                message_text += f"   <i>(Средний за неделю: {format_distance(avg_per_week, distance_unit)})</i>\n"

    # 3. Типы тренировок с процентами
    if stats['types_count']:
        message_text += f"\n📋 <b>Типы тренировок:</b>\n"

        type_emoji = {
            'кросс': '🏃',
            'плавание': '🏊',
            'велотренировка': '🚴',
            'силовая': '💪',
            'интервальная': '⚡'
        }

        # Сортируем по количеству
        sorted_types = sorted(stats['types_count'].items(), key=lambda x: x[1], reverse=True)

        for t_type, count in sorted_types:
            emoji = type_emoji.get(t_type, '📝')
            percentage = (count / stats['total_count']) * 100
            message_text += f"  {emoji} {t_type.capitalize()}: {count} ({percentage:.1f}%)\n"

    # 4. Средний уровень усилий
    if stats['avg_fatigue'] > 0:
        message_text += f"\n💪 Средний уровень усилий: <b>{stats['avg_fatigue']}/10</b>\n"

    from coach.coach_keyboards import get_student_stats_period_keyboard
    await callback.message.edit_text(
        message_text,
        parse_mode="HTML",
        reply_markup=get_student_stats_period_keyboard(student_id)
    )
    await callback.answer()
