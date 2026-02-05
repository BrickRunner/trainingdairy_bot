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
from bot.keyboards import get_main_menu_keyboard
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
        "👨‍🏫 <b>Кабинет тренера</b>\n\n"
        "Здесь вы можете управлять своими учениками, "
        "просматривать их тренировки и прогресс.",
        reply_markup=get_coach_main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "coach:main_menu")
async def show_coach_main_menu_redirect(callback: CallbackQuery):
    """Редирект на главное меню тренера (алиас для coach:menu)"""
    await show_coach_menu(callback)


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
            "👉 Кабинет тренера → Ссылка для учеников",
            reply_markup=get_students_list_keyboard([]),
            parse_mode="HTML"
        )
    else:
        text = f"👥 <b>Мои ученики</b> ({len(students)})\n\n"
        text += "Выберите ученика для просмотра:\n"

        await callback.message.edit_text(
            text,
            reply_markup=get_students_list_keyboard(students),
            parse_mode="HTML"
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

    # Форматируем дату подключения согласно настройкам тренера
    from utils.date_formatter import get_user_date_format, DateFormatter
    coach_date_format = await get_user_date_format(coach_id)

    # Извлекаем только дату из timestamp (берём первые 10 символов: YYYY-MM-DD)
    connected_at_str = student.get('connected_at', '')
    if connected_at_str:
        # Если есть пробел (формат datetime), берём только дату
        connected_date_only = connected_at_str.split()[0] if ' ' in connected_at_str else connected_at_str[:10]
        connected_date = DateFormatter.format_date(connected_date_only, coach_date_format)
    else:
        connected_date = 'не указано'

    text = f"👤 <b>{display_name}</b>\n\n"
    text += f"📱 Telegram: @{student['username']}\n"
    text += f"📅 Подключён: {connected_date}\n"

    await callback.message.edit_text(
        text,
        reply_markup=get_student_detail_keyboard(student_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("coach:student_trainings:"))
async def show_student_trainings_menu(callback: CallbackQuery):
    """Показать меню выбора периода для тренировок ученика"""
    from coach.coach_training_queries import can_coach_access_student, get_student_display_name
    from coach.coach_keyboards import get_student_trainings_period_keyboard

    student_id = int(callback.data.split(":")[2])
    coach_id = callback.from_user.id

    # Проверяем доступ
    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа к этому ученику", show_alert=True)
        return

    display_name = await get_student_display_name(coach_id, student_id)

    await callback.message.edit_text(
        f"📊 <b>Статистика: {display_name}</b>\n\n"
        "Выберите период для просмотра:",
        reply_markup=get_student_trainings_period_keyboard(student_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("coach:trainings_period:"))
async def show_student_trainings_by_period(callback: CallbackQuery, state: FSMContext):
    """Показать тренировки и статистику ученика за выбранный период (детальный view как в глобальном разделе)"""
    from coach.coach_training_queries import get_student_trainings_by_period, can_coach_access_student, get_student_display_name
    from coach.coach_keyboards import get_student_trainings_keyboard, get_student_trainings_period_keyboard
    from utils.date_formatter import get_user_date_format, DateFormatter
    from database.queries import get_training_statistics, get_user_settings, get_trainings_by_period
    from utils.unit_converter import format_distance, format_swimming_distance
    from datetime import datetime, timedelta
    from aiogram.types import BufferedInputFile
    from bot.graphs import generate_graphs
    import logging

    logger = logging.getLogger(__name__)

    parts = callback.data.split(":")
    student_id = int(parts[2])
    period = parts[3]
    coach_id = callback.from_user.id

    # Проверяем доступ
    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа к этому ученику", show_alert=True)
        return

    # Удаляем старые сообщения с графиками, если они есть
    data = await state.get_data()
    old_message_ids = data.get('coach_trainings_message_ids', [])
    for msg_id in old_message_ids:
        try:
            await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=msg_id)
        except Exception:
            pass
    await state.update_data(coach_trainings_message_ids=[])

    # Получаем формат даты и единицы измерения ТРЕНЕРА (не ученика)
    coach_date_format = await get_user_date_format(coach_id)
    coach_settings = await get_user_settings(coach_id)
    distance_unit = coach_settings.get('distance_unit', 'км') if coach_settings else 'км'

    # Получаем тренировки и статистику за период
    trainings = await get_trainings_by_period(student_id, period)
    stats = await get_training_statistics(student_id, period)
    display_name = await get_student_display_name(coach_id, student_id)

    period_names = {"week": "неделю", "2weeks": "2 недели", "month": "месяц"}
    period_name = period_names.get(period, "период")

    # Определяем количество дней для графиков
    period_days = {
        "week": 7,
        "2weeks": 14,
        "month": 30
    }
    days = period_days.get(period, 7)

    # Определяем начальную дату периода для отображения
    today = datetime.now().date()
    if period == 'week':
        start_date = today - timedelta(days=today.weekday())
        formatted_start = DateFormatter.format_date(start_date, coach_date_format)
        if coach_date_format == 'ДД.ММ.ГГГГ':
            short_start = formatted_start[:5]
        elif coach_date_format == 'ММ/ДД/ГГГГ':
            short_start = formatted_start[:5]
        else:
            short_start = formatted_start[5:]
        period_display = f"неделю (с {short_start} по сегодня)"
    elif period == '2weeks':
        start_date = today - timedelta(days=today.weekday() + 7)
        formatted_start = DateFormatter.format_date(start_date, coach_date_format)
        if coach_date_format == 'ДД.ММ.ГГГГ':
            short_start = formatted_start[:5]
        elif coach_date_format == 'ММ/ДД/ГГГГ':
            short_start = formatted_start[:5]
        else:
            short_start = formatted_start[5:]
        period_display = f"2 недели (с {short_start} по сегодня)"
    elif period == 'month':
        start_date = today.replace(day=1)
        formatted_start = DateFormatter.format_date(start_date, coach_date_format)
        if coach_date_format == 'ДД.ММ.ГГГГ':
            short_start = formatted_start[:5]
        elif coach_date_format == 'ММ/ДД/ГГГГ':
            short_start = formatted_start[:5]
        else:
            short_start = formatted_start[5:]
        period_display = f"месяц (с {short_start} по сегодня)"
    else:
        period_display = period_name

    if not trainings:
        await callback.message.edit_text(
            f"📊 *Статистика: {display_name}*\n\n"
            f"За {period_name} нет тренировок.",
            reply_markup=get_student_trainings_period_keyboard(student_id),
            parse_mode="Markdown"
        )
        await callback.answer()
        return

    # Формируем заголовок с общей статистикой
    message_text = f"📊 *Статистика: {display_name}*\n"
    message_text += f"📅 За {period_display}\n\n"
    message_text += "━━━━━━━━━━━━━━━━━━\n"
    message_text += "📈 *ОБЩАЯ СТАТИСТИКА*\n"
    message_text += "━━━━━━━━━━━━━━━━━━\n\n"

    # 1. Общее количество тренировок
    message_text += f"🏃 Всего тренировок: *{stats['total_count']}*\n"

    # 2. Общий километраж (и средний за неделю для периодов > 1 недели)
    if stats['total_distance'] > 0:
        message_text += f"📏 Общий километраж: *{format_distance(stats['total_distance'], distance_unit)}*\n"

        # Для периодов больше недели показываем средний км за неделю
        if period in ['2weeks', 'month']:
            days_in_period = (today - start_date).days + 1
            weeks_count = days_in_period / 7

            if weeks_count > 0:
                avg_per_week = stats['total_distance'] / weeks_count
                message_text += f"   _(Средний за неделю: {format_distance(avg_per_week, distance_unit)})_\n"

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

    # 4. Средний уровень усилий
    if stats['avg_fatigue'] > 0:
        message_text += f"\n💪 Средний уровень усилий: *{stats['avg_fatigue']}/10*\n"

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
        # Парсим и форматируем дату согласно настройкам тренера
        date = DateFormatter.format_date(training['date'], coach_date_format)
        t_type = training['type']
        emoji = type_emoji.get(t_type, '📝')

        # 1. Дата и тип (с отметкой если добавлено тренером)
        coach_mark = " 👨‍🏫" if training.get('added_by_coach_id') else ""
        message_text += f"*{idx}.* {emoji} *{t_type.capitalize()}* • {date}{coach_mark}\n"

        # 2. Продолжительность в формате ЧЧ:ММ:СС
        if training.get('time'):
            message_text += f"   ⏰ Время: {training['time']}\n"

        # 3. Общий километраж с учетом единиц измерения
        if t_type == 'интервальная':
            if training.get('calculated_volume'):
                message_text += f"   📏 Дистанция: {format_distance(training['calculated_volume'], distance_unit)}\n"
        else:
            if training.get('distance'):
                if t_type == 'плавание':
                    message_text += f"   📏 Дистанция: {format_swimming_distance(training['distance'], distance_unit)}\n"
                else:
                    message_text += f"   📏 Дистанция: {format_distance(training['distance'], distance_unit)}\n"

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

        # Усилия
        if training.get('fatigue_level'):
            message_text += f"   💪 Усилия: {training['fatigue_level']}/10\n"

        message_text += "\n"

    if len(trainings) > 15:
        message_text += f"_... и ещё {len(trainings) - 15} тренировок_\n"

    try:
        await callback.message.edit_text(
            message_text,
            parse_mode="Markdown",
            reply_markup=get_student_trainings_period_keyboard(student_id)
        )
    except Exception as e:
        # Если сообщение не изменилось - просто отвечаем на callback
        if "message is not modified" in str(e):
            await callback.answer("Данные актуальны", show_alert=False)
        elif "message to edit not found" in str(e).lower():
            # Если сообщение было удалено - отправляем новое
            logger.warning(f"Сообщение для редактирования не найдено, отправляем новое")
            await callback.message.answer(
                message_text,
                parse_mode="Markdown",
                reply_markup=get_student_trainings_period_keyboard(student_id)
            )
        else:
            logger.error(f"Ошибка при редактировании сообщения: {str(e)}")
            raise

    # Генерируем и отправляем графики для всех периодов (только если тренировок >= 2)
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
            logger.info(f"Отправка графика для ученика {student_id}, период {period}...")

            if combined_graph:
                graph_msg = await callback.message.answer_photo(
                    photo=BufferedInputFile(combined_graph.read(), filename="statistics.png"),
                    caption=f"📊 Статистика тренировок {display_name} {caption_suffix}"
                )
                new_message_ids.append(graph_msg.message_id)
                logger.info("График отправлен")
            else:
                logger.warning("Не удалось создать графики")
                warning_msg = await callback.message.answer("⚠️ Недостаточно данных для создания графиков")
                new_message_ids.append(warning_msg.message_id)

        except Exception as e:
            logger.error(f"Ошибка при отправке графика: {str(e)}", exc_info=True)
            error_msg = await callback.message.answer(f"❌ Ошибка при создании графиков: {str(e)}")
            new_message_ids.append(error_msg.message_id)
    else:
        logger.info(f"Недостаточно тренировок для графиков: {len(trainings)} (минимум 2)")

    # Отправляем сообщение с кнопками для выбора тренировки
    from coach.coach_keyboards import get_student_trainings_keyboard
    menu_msg = await callback.message.answer(
        "📋 *Выберите тренировку для просмотра деталей:*\n\n"
        "Нажмите на номер тренировки или выберите другой период",
        parse_mode="Markdown",
        reply_markup=get_student_trainings_keyboard(student_id, trainings, period, coach_date_format)
    )
    new_message_ids.append(menu_msg.message_id)

    # Сохраняем ID новых сообщений в state
    await state.update_data(coach_trainings_message_ids=new_message_ids)

    await callback.answer()


@router.callback_query(F.data.startswith("coach:student_health:"))
async def show_student_health_menu(callback: CallbackQuery):
    """Показать меню выбора периода для здоровья ученика"""
    from coach.coach_training_queries import can_coach_access_student, get_student_display_name
    from coach.coach_keyboards import get_student_health_period_keyboard

    student_id = int(callback.data.split(":")[2])
    coach_id = callback.from_user.id

    # Проверяем доступ
    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    display_name = await get_student_display_name(coach_id, student_id)

    await callback.message.edit_text(
        f"💊 <b>Здоровье: {display_name}</b>\n\n"
        "Выберите период:",
        reply_markup=get_student_health_period_keyboard(student_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("coach:health_period:"))
async def show_student_health_data(callback: CallbackQuery):
    """Показать данные о здоровье ученика за выбранный период"""
    from coach.coach_training_queries import can_coach_access_student, get_student_display_name
    from health.health_queries import get_latest_health_metrics
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    from utils.date_formatter import get_user_date_format, DateFormatter
    from database.queries import get_user_settings
    from utils.unit_converter import kg_to_lbs

    parts = callback.data.split(":")
    student_id = int(parts[2])
    period = parts[3]  # week, 2weeks, month
    coach_id = callback.from_user.id

    # Проверяем доступ
    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    display_name = await get_student_display_name(coach_id, student_id)

    # Получаем формат даты и единицы измерения тренера
    coach_date_format = await get_user_date_format(coach_id)
    coach_settings = await get_user_settings(coach_id)
    weight_unit = coach_settings.get('weight_unit', 'кг') if coach_settings else 'кг'

    # Определяем начальную и конечную даты в зависимости от периода
    from datetime import datetime, timedelta
    import calendar

    today = datetime.now().date()

    if period == 'week':
        # Текущая календарная неделя: от понедельника до воскресенья
        start_date = today - timedelta(days=today.weekday())  # Понедельник
        end_date = start_date + timedelta(days=6)  # Воскресенье
        period_name = 'неделя'
    elif period == '2weeks':
        # Последние 14 дней до сегодня
        start_date = today - timedelta(days=13)
        end_date = today
        period_name = 'две недели'
    elif period == 'month':
        # Текущий календарный месяц: с 1 до последнего числа
        start_date = today.replace(day=1)
        # Последний день месяца
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_date = today.replace(day=last_day)
        period_name = 'месяц'
    else:
        # По умолчанию - неделя
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
        period_name = 'неделя'

    # Получаем данные о здоровье за период
    from health.health_queries import get_health_metrics_range
    health_data = await get_health_metrics_range(student_id, start_date, end_date)

    if not health_data:
        text = (
            f"💊 <b>Здоровье: {display_name}</b>\n"
            f"📅 За {period_name}\n\n"
            "Нет данных о здоровье за этот период."
        )
    else:
        text = f"💊 <b>Здоровье: {display_name}</b>\n"
        text += f"📅 За {period_name}\n\n"

        for record in reversed(health_data):  # Новые сверху
            date_str = record['date']
            if isinstance(date_str, str):
                # Форматируем дату согласно настройкам тренера (короткий формат)
                formatted_date = DateFormatter.format_date(date_str, coach_date_format)
                if coach_date_format == 'ДД.ММ.ГГГГ':
                    date_str = formatted_date[:5]  # ДД.ММ
                elif coach_date_format == 'ММ/ДД/ГГГГ':
                    date_str = formatted_date[:5]  # ММ/ДД
                else:  # ГГГГ-ММ-ДД
                    date_str = formatted_date[5:]  # ММ-ДД

            line = f"📅 {date_str}: "
            parts_list = []

            if record.get('morning_pulse'):
                parts_list.append(f"💗 {record['morning_pulse']} уд/мин")

            if record.get('weight'):
                # Вес в БД всегда хранится в кг, конвертируем если нужно
                weight_value = record['weight']
                if weight_unit == 'фунты':
                    weight_value = kg_to_lbs(weight_value)
                parts_list.append(f"⚖️ {weight_value:.1f} {weight_unit}")

            if record.get('sleep_duration'):
                parts_list.append(f"😴 {record['sleep_duration']}ч")

            if parts_list:
                line += ", ".join(parts_list)
            else:
                line += "нет данных"

            text += line + "\n"

    # Кнопка назад к выбору периода
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="« К выбору периода",
            callback_data=f"coach:student_health:{student_id}"
        )
    )

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


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
        reply_markup=get_confirm_remove_student_keyboard(student_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("coach:confirm_remove:"))
async def remove_student(callback: CallbackQuery):
    """Удалить ученика"""
    from coach.coach_training_queries import get_student_display_name
    from database.queries import get_user_settings

    student_id = int(callback.data.split(":")[2])
    coach_id = callback.from_user.id

    # Получаем имя ученика для уведомления
    student_display_name = await get_student_display_name(coach_id, student_id)

    # Получаем информацию о тренере для уведомления
    coach_settings = await get_user_settings(coach_id)
    coach_name = coach_settings.get('name', 'Тренер') if coach_settings else 'Тренер'

    # Удаляем ученика
    await remove_student_from_coach(coach_id, student_id)

    # Уведомляем ученика об удалении
    try:
        await callback.bot.send_message(
            student_id,
            f"❌ <b>Тренер отключил вас</b>\n\n"
            f"Тренер {coach_name} отключил вас из списка своих учеников.",
            parse_mode="HTML"
        )
        logger.info(f"Notified student {student_id} about removal by coach {coach_id}")

        # Редирект ученика в главное меню
        student_settings = await get_user_settings(student_id)
        student_is_coach = await is_user_coach(student_id)

        await callback.bot.send_message(
            student_id,
            "Вы в главном меню",
            reply_markup=get_main_menu_keyboard(student_is_coach),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Failed to notify student {student_id} about removal: {e}")

    # Перенаправляем тренера в главное меню кабинета тренера
    await callback.message.edit_text(
        "👨‍🏫 <b>Кабинет тренера</b>\n\n"
        "Здесь вы можете управлять своими учениками, "
        "просматривать их тренировки и прогресс.",
        reply_markup=get_coach_main_menu(),
        parse_mode="HTML"
    )
    await callback.answer(f"✅ Ученик {student_display_name} удалён", show_alert=True)


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
        reply_markup=get_coach_main_menu(),
        parse_mode="HTML"
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
            reply_markup=get_add_coach_keyboard(),
            parse_mode="HTML"
        )
    else:
        text = f"👨‍🏫 <b>Мой тренер</b>\n\n"
        text += f"👤 Имя: {coach['name']}\n"
        text += f"📱 Telegram: @{coach['username']}\n\n"
        text += "Ваш тренер может просматривать ваши тренировки и статистику."

        await callback.message.edit_text(
            text,
            reply_markup=get_student_coach_info_keyboard(),
            parse_mode="HTML"
        )

    await callback.answer()


@router.callback_query(F.data == "student:add_coach")
async def add_coach_prompt(callback: CallbackQuery, state: FSMContext):
    """Запросить код тренера"""
    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="❌ Отменить",
            callback_data="student:cancel_add_coach"
        )
    )

    await callback.message.edit_text(
        "✏️ <b>Добавление тренера</b>\n\n"
        "Введите код тренера, который он вам отправил:",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await state.set_state(CoachStates.waiting_for_coach_code)
    await callback.answer()


@router.callback_query(F.data == "student:cancel_add_coach")
async def cancel_add_coach(callback: CallbackQuery, state: FSMContext):
    """Отменить добавление тренера и вернуться в настройки"""
    await state.clear()

    # Редирект в настройки
    from settings.settings_keyboards import get_settings_menu_keyboard

    # Проверяем, является ли пользователь тренером
    user_id = callback.from_user.id
    user_is_coach = await is_user_coach(user_id)

    await callback.message.edit_text(
        "⚙️ <b>Настройки</b>\n\n"
        "Выберите раздел:",
        reply_markup=get_settings_menu_keyboard(is_coach=user_is_coach),
        parse_mode="HTML"
    )
    await callback.answer("❌ Отменено")


@router.message(CoachStates.waiting_for_coach_code)
async def process_coach_code(message: Message, state: FSMContext):
    """Обработать введённый код тренера"""
    code = message.text.strip().upper()

    # Ищем тренера по коду
    coach_id = await find_coach_by_code(code)

    if not coach_id:
        await message.answer(
            "❌ Код тренера не найден.\n\n"
            "Проверьте правильность кода и попробуйте снова.",
            parse_mode="HTML"
        )
        return

    # Добавляем связь
    student_id = message.from_user.id

    # Проверяем, что пользователь не пытается добавить себя
    if coach_id == student_id:
        await message.answer(
            "❌ <b>Ошибка подключения</b>\n\n"
            "Вы не можете быть тренером для самого себя.",
            parse_mode="HTML"
        )
        await state.clear()
        return

    success = await add_student_to_coach(coach_id, student_id)

    if success:
        coach = await get_user(coach_id)
        from aiogram.types import ReplyKeyboardRemove
        await message.answer(
            f"✅ <b>Вы успешно подключились к тренеру!</b>\n\n"
            f"Ваш тренер: @{coach.get('username', 'Неизвестно')}\n\n"
            f"Теперь тренер может просматривать ваши тренировки и статистику.",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="HTML"
        )

        # Уведомляем тренера
        try:
            student_name = message.from_user.full_name
            await message.bot.send_message(
                coach_id,
                f"🎉 Новый ученик!\n\n"
                f"К вам подключился: {student_name}"
            )

            # Редирект тренера в главное меню
            from database.queries import get_user_settings
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

        # Редирект в главное меню
        from database.queries import get_user_settings
        user_id = message.from_user.id
        is_coach_status = await is_user_coach(user_id)
        settings = await get_user_settings(user_id)

        await message.answer(
            "Вы в главном меню",
            reply_markup=get_main_menu_keyboard(is_coach_status),
            parse_mode="HTML"
        )
    else:
        from aiogram.types import ReplyKeyboardRemove
        await message.answer(
            "⚠️ Вы уже подключены к этому тренеру.",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="HTML"
        )

        # Редирект в главное меню
        from database.queries import get_user_settings
        user_id = message.from_user.id
        settings = await get_user_settings(user_id)
        is_coach_status = await is_user_coach(user_id)
        name = settings.get('name', message.from_user.username) if settings else message.from_user.username

        await message.answer(
            "Вы в главном меню",
            reply_markup=get_main_menu_keyboard(is_coach_status),
            parse_mode="HTML"
        )

    await state.clear()


@router.callback_query(F.data == "student:remove_coach")
async def confirm_remove_coach(callback: CallbackQuery):
    """Подтверждение отключения от тренера"""
    await callback.message.edit_text(
        "Вы уверены, что хотите отключиться от тренера?\n\n"
        "После этого тренер больше не сможет видеть ваши данные.",
        reply_markup=get_confirm_remove_coach_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "student:confirm_remove_coach")
async def remove_coach(callback: CallbackQuery):
    """Отключиться от тренера"""
    user_id = callback.from_user.id
    student_name = callback.from_user.full_name

    coach_id = await remove_coach_from_student(user_id)

    await callback.message.edit_text(
        "✅ Вы отключились от тренера",
        reply_markup=get_add_coach_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

    # Уведомляем тренера об отключении
    if coach_id:
        try:
            await callback.bot.send_message(
                coach_id,
                f"❌ <b>Ученик отключился</b>\n\n"
                f"{student_name} отключился от вас.",
                parse_mode="HTML"
            )
            logger.info(f"Notified coach {coach_id} about student {user_id} disconnect")

            # Редирект тренера в главное меню
            from database.queries import get_user_settings
            coach_settings = await get_user_settings(coach_id)
            coach_is_coach = await is_user_coach(coach_id)

            await callback.bot.send_message(
                coach_id,
                "Вы в главном меню",
                reply_markup=get_main_menu_keyboard(coach_is_coach),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to notify coach {coach_id} about disconnect: {e}")


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
    from coach.coach_training_queries import set_student_nickname, get_student_display_name
    from coach.coach_keyboards import get_student_detail_keyboard
    from utils.date_formatter import get_user_date_format, DateFormatter

    data = await state.get_data()
    student_id = data.get('student_id')
    coach_id = message.from_user.id
    nickname = message.text.strip()

    await set_student_nickname(coach_id, student_id, nickname)

    # Получаем обновленное имя
    display_name = await get_student_display_name(coach_id, student_id)

    # Получаем информацию об ученике
    students = await get_coach_students(coach_id)
    student = next((s for s in students if s['id'] == student_id), None)

    if student:
        # Форматируем дату подключения
        coach_date_format = await get_user_date_format(coach_id)

        # Извлекаем только дату из timestamp
        connected_at_str = student.get('connected_at', '')
        if connected_at_str:
            connected_date_only = connected_at_str.split()[0] if ' ' in connected_at_str else connected_at_str[:10]
            connected_date = DateFormatter.format_date(connected_date_only, coach_date_format)
        else:
            connected_date = 'не указано'

        text = f"👤 <b>{display_name}</b>\n\n"
        text += f"📱 Telegram: @{student['username']}\n"
        text += f"📅 Подключён: {connected_date}\n\n"
        text += f"✅ Псевдоним изменён на: <b>{nickname}</b>"

        await message.answer(
            text,
            reply_markup=get_student_detail_keyboard(student_id),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"✅ Псевдоним изменён на: <b>{nickname}</b>",
            parse_mode="HTML"
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
    period = parts[4] if len(parts) > 4 else None
    coach_id = callback.from_user.id

    # Проверяем доступ
    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    training = await get_training_with_comments(training_id)
    if not training:
        await callback.answer("Тренировка не найдена", show_alert=True)
        return

    # Логирование для отладки комментариев
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Training {training_id}: comment field = {training.get('comment')}, has {len(training.get('comments', []))} trainer comments")

    # Форматируем информацию о тренировке
    from database.queries import get_user_settings
    from utils.date_formatter import get_user_date_format, DateFormatter
    from competitions.competitions_utils import km_to_miles

    # Используем формат даты и единицы измерения ТРЕНЕРА для единообразия в кабинете тренера
    coach_date_format = await get_user_date_format(coach_id)
    formatted_date = DateFormatter.format_date(training['date'], coach_date_format)

    coach_settings = await get_user_settings(coach_id)
    distance_unit = coach_settings.get('distance_unit', 'км') if coach_settings else 'км'

    t_type = training['type']

    type_emoji = {
        'кросс': '🏃',
        'плавание': '🏊',
        'велотренировка': '🚴',
        'силовая': '💪',
        'интервальная': '⚡'
    }
    emoji = type_emoji.get(t_type, '📝')

    text = f"{emoji} <b>Детальная информация о тренировке</b>\n\n"
    text += f"━━━━━━━━━━━━━━━━━\n"
    text += f"📅 <b>Дата:</b> {formatted_date}\n"
    text += f"🏋️ <b>Тип:</b> {t_type.capitalize()}\n"

    # Время тренировки
    if training.get('time'):
        text += f"⏱ <b>Время:</b> {training['time']}\n"

    # Специфичная информация в зависимости от типа
    if t_type == 'интервальная':
        # Для интервальной - описание и объем
        if training.get('calculated_volume'):
            from utils.unit_converter import format_distance
            text += f"📏 <b>Объем:</b> {format_distance(training['calculated_volume'], distance_unit)}\n"

        if training.get('intervals'):
            # Показываем средний темп отрезков если есть результаты
            from utils.interval_calculator import calculate_average_interval_pace
            avg_pace_intervals = calculate_average_interval_pace(training['intervals'])
            if avg_pace_intervals:
                text += f"⚡ <b>Средний темп отрезков:</b> {avg_pace_intervals}\n"

            text += f"\n📋 <b>Описание тренировки:</b>\n{training['intervals']}\n"

    elif t_type == 'силовая':
        # Для силовой - упражнения
        if training.get('exercises'):
            text += f"\n💪 <b>Упражнения:</b>\n{training['exercises']}\n"

    else:
        # Для кросса, плавания, велотренировки - дистанция и темп
        if training.get('distance'):
            if t_type == 'плавание':
                from utils.unit_converter import format_swimming_distance
                text += f"📏 <b>Дистанция:</b> {format_swimming_distance(training['distance'], distance_unit)}\n"
            else:
                from utils.unit_converter import format_distance
                text += f"📏 <b>Дистанция:</b> {format_distance(training['distance'], distance_unit)}\n"

        # Для плавания - дополнительная информация
        if t_type == 'плавание':
            # Место тренировки
            if training.get('swimming_location'):
                from utils.swimming_pace import format_swimming_location
                location_text = format_swimming_location(
                    training['swimming_location'],
                    training.get('pool_length')
                )
                text += f"📍 <b>Место:</b> {location_text}\n"

            # Стили плавания
            if training.get('swimming_styles'):
                import json
                try:
                    styles = json.loads(training['swimming_styles'])
                    from utils.swimming_pace import format_swimming_styles
                    styles_text = format_swimming_styles(styles)
                    text += f"🏊 <b>Стили:</b> {styles_text}\n"
                except:
                    pass

            # Описание отрезков
            if training.get('swimming_sets'):
                text += f"\n📝 <b>Отрезки:</b>\n{training['swimming_sets']}\n"

        if training.get('avg_pace'):
            pace_unit = training.get('pace_unit', '')
            if t_type == 'велотренировка':
                text += f"🚴 <b>Средняя скорость:</b> {training['avg_pace']} {pace_unit}\n"
            else:
                text += f"⚡ <b>Средний темп:</b> {training['avg_pace']} {pace_unit}\n"

    # Пульс (для всех типов)
    if training.get('avg_pulse'):
        text += f"❤️ <b>Средний пульс:</b> {training['avg_pulse']} уд/мин\n"

    if training.get('max_pulse'):
        text += f"💗 <b>Максимальный пульс:</b> {training['max_pulse']} уд/мин\n"

    # Уровень усилий
    if training.get('fatigue_level'):
        text += f"\n💪 <b>Уровень усилий:</b> {training['fatigue_level']}/10\n"

    text += "\n━━━━━━━━━━━━━━━━━\n"

    # Комментарий ученика (его личный комментарий к тренировке)
    if training.get('comment'):
        text += f"\n💬 <b>Комментарий ученика:</b>\n<i>{training['comment']}</i>\n"

    # Комментарии тренера
    comments = training.get('comments', [])
    coach_has_comment = False
    if comments:
        text += f"\n💬 <b>Комментарий тренера:</b>\n"
        for comment in comments:
            author_name = comment.get('author_name') or comment.get('author_username')
            text += f"\n<i>{author_name}:</i> {comment['comment']}\n"
            # Проверяем, есть ли комментарий от текущего тренера
            if comment.get('author_id') == coach_id:
                coach_has_comment = True

    await callback.message.edit_text(
        text,
        reply_markup=get_training_detail_keyboard(training_id, student_id, period, len(comments), coach_has_comment),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("coach:add_comment:"))
async def add_comment_prompt(callback: CallbackQuery, state: FSMContext):
    """Запросить комментарий к тренировке"""
    parts = callback.data.split(":")
    training_id = int(parts[2])
    student_id = int(parts[3])
    period = parts[4] if len(parts) > 4 else None

    # Сохраняем в состоянии
    await state.update_data(training_id=training_id, student_id=student_id, period=period)

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
    from coach.coach_training_queries import add_comment_to_training, get_training_with_comments, get_student_display_name
    from coach.coach_keyboards import get_training_detail_keyboard
    from database.queries import get_user_settings
    from utils.date_formatter import get_user_date_format, DateFormatter
    from competitions.competitions_utils import km_to_miles

    data = await state.get_data()
    training_id = data.get('training_id')
    student_id = data.get('student_id')
    period = data.get('period')
    coach_id = message.from_user.id
    comment_text = message.text.strip()

    # Получаем информацию о тренировке до добавления комментария (для уведомления)
    training = await get_training_with_comments(training_id)
    if not training:
        await message.answer("❌ Тренировка не найдена", parse_mode="HTML")
        await state.clear()
        return

    # Форматируем дату согласно настройкам ученика
    user_date_format = await get_user_date_format(student_id)
    formatted_date = DateFormatter.format_date(training['date'], user_date_format)

    # Определяем тип тренировки для эмодзи
    type_emoji = {
        'кросс': '🏃',
        'плавание': '🏊',
        'велотренировка': '🚴',
        'силовая': '💪',
        'интервальная': '⚡'
    }
    emoji = type_emoji.get(training['type'], '📝')

    # Добавляем комментарий
    await add_comment_to_training(training_id, coach_id, comment_text)

    # Уведомляем ученика с датой тренировки и кнопкой для просмотра
    try:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        from aiogram.utils.keyboard import InlineKeyboardBuilder

        # Создаем клавиатуру с кнопкой просмотра деталей
        builder = InlineKeyboardBuilder()
        # Используем period или "week" как дефолт
        view_period = period if period else "week"
        builder.row(
            InlineKeyboardButton(
                text="📋 Посмотреть тренировку",
                callback_data=f"training_detail:{training_id}:{view_period}"
            )
        )

        await message.bot.send_message(
            student_id,
            f"💬 <b>Новый комментарий от тренера</b>\n\n"
            f"{emoji} <b>Тренировка:</b> {training['type'].capitalize()}\n"
            f"📅 <b>Дата:</b> {formatted_date}\n\n"
            f"<b>Комментарий:</b>\n<i>{comment_text}</i>",
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
    except Exception as e:
        logger.error(f"Failed to notify student: {e}")

    # Получаем обновленную тренировку с комментариями (для отображения тренеру)
    training = await get_training_with_comments(training_id)

    # Используем настройки ТРЕНЕРА (а не ученика) для отображения деталей
    coach_settings = await get_user_settings(coach_id)
    distance_unit = coach_settings.get('distance_unit', 'км') if coach_settings else 'км'

    # Форматируем дату согласно настройкам ТРЕНЕРА
    coach_date_format = await get_user_date_format(coach_id)
    coach_formatted_date = DateFormatter.format_date(training['date'], coach_date_format)

    t_type = training['type']
    emoji = type_emoji.get(t_type, '📝')

    text = f"{emoji} <b>Детальная информация о тренировке</b>\n\n"
    text += f"━━━━━━━━━━━━━━━━━\n"
    text += f"📅 <b>Дата:</b> {coach_formatted_date}\n"
    text += f"🏋️ <b>Тип:</b> {t_type.capitalize()}\n"

    # Время тренировки
    if training.get('time'):
        text += f"⏱ <b>Время:</b> {training['time']}\n"

    # Специфичная информация в зависимости от типа
    if t_type == 'интервальная':
        # Для интервальной - описание и объем
        if training.get('calculated_volume'):
            from utils.unit_converter import format_distance
            text += f"📏 <b>Объем:</b> {format_distance(training['calculated_volume'], distance_unit)}\n"

        if training.get('intervals'):
            # Показываем средний темп отрезков если есть результаты
            from utils.interval_calculator import calculate_average_interval_pace
            avg_pace_intervals = calculate_average_interval_pace(training['intervals'])
            if avg_pace_intervals:
                text += f"⚡ <b>Средний темп отрезков:</b> {avg_pace_intervals}\n"

            text += f"\n📋 <b>Описание тренировки:</b>\n{training['intervals']}\n"

    elif t_type == 'силовая':
        # Для силовой - упражнения
        if training.get('exercises'):
            text += f"\n💪 <b>Упражнения:</b>\n{training['exercises']}\n"

    else:
        # Для кросса, плавания, велотренировки - дистанция и темп
        if training.get('distance'):
            if t_type == 'плавание':
                from utils.unit_converter import format_swimming_distance
                text += f"📏 <b>Дистанция:</b> {format_swimming_distance(training['distance'], distance_unit)}\n"
            else:
                from utils.unit_converter import format_distance
                text += f"📏 <b>Дистанция:</b> {format_distance(training['distance'], distance_unit)}\n"

        # Для плавания - дополнительная информация
        if t_type == 'плавание':
            # Место тренировки
            if training.get('swimming_location'):
                from utils.swimming_pace import format_swimming_location
                location_text = format_swimming_location(
                    training['swimming_location'],
                    training.get('pool_length')
                )
                text += f"📍 <b>Место:</b> {location_text}\n"

            # Стили плавания
            if training.get('swimming_styles'):
                import json
                try:
                    styles = json.loads(training['swimming_styles'])
                    from utils.swimming_pace import format_swimming_styles
                    styles_text = format_swimming_styles(styles)
                    text += f"🏊 <b>Стили:</b> {styles_text}\n"
                except:
                    pass

            # Описание отрезков
            if training.get('swimming_sets'):
                text += f"\n📝 <b>Отрезки:</b>\n{training['swimming_sets']}\n"

        if training.get('avg_pace'):
            pace_unit = training.get('pace_unit', '')
            if t_type == 'велотренировка':
                text += f"🚴 <b>Средняя скорость:</b> {training['avg_pace']} {pace_unit}\n"
            else:
                text += f"⚡ <b>Средний темп:</b> {training['avg_pace']} {pace_unit}\n"

    # Пульс (для всех типов)
    if training.get('avg_pulse'):
        text += f"❤️ <b>Средний пульс:</b> {training['avg_pulse']} уд/мин\n"

    if training.get('max_pulse'):
        text += f"💗 <b>Максимальный пульс:</b> {training['max_pulse']} уд/мин\n"

    # Уровень усилий
    if training.get('fatigue_level'):
        text += f"\n💪 <b>Уровень усилий:</b> {training['fatigue_level']}/10\n"

    text += "\n━━━━━━━━━━━━━━━━━\n"

    # Комментарий ученика (его личный комментарий к тренировке)
    if training.get('comment'):
        text += f"\n💬 <b>Комментарий ученика:</b>\n<i>{training['comment']}</i>\n"

    # Комментарии тренера
    comments = training.get('comments', [])
    coach_has_comment = False
    if comments:
        text += f"\n💬 <b>Комментарий тренера:</b>\n"
        for comment in comments:
            author_name = comment.get('author_name') or comment.get('author_username')
            text += f"\n<i>{author_name}:</i> {comment['comment']}\n"
            if comment.get('author_id') == coach_id:
                coach_has_comment = True

    text += "\n✅ <b>Комментарий успешно добавлен!</b>"

    await message.answer(
        text,
        reply_markup=get_training_detail_keyboard(training_id, student_id, period, len(comments), coach_has_comment),
        parse_mode="HTML"
    )

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
    from coach.coach_keyboards import get_student_stats_period_keyboard
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
    from utils.date_formatter import get_user_date_format, DateFormatter
    coach_date_format = await get_user_date_format(coach_id)

    today = datetime.now().date()

    if period == 'week':
        start_date = today - timedelta(days=today.weekday())
        formatted_start = DateFormatter.format_date(start_date, coach_date_format)
        # Берем только день и месяц
        if coach_date_format == 'ДД.ММ.ГГГГ':
            short_start = formatted_start[:5]  # ДД.ММ
        elif coach_date_format == 'ММ/ДД/ГГГГ':
            short_start = formatted_start[:5]  # ММ/ДД
        else:  # ГГГГ-ММ-ДД
            short_start = formatted_start[5:]  # ММ-ДД
        period_display = f"неделю (с {short_start} по сегодня)"
    elif period == '2weeks':
        start_date = today - timedelta(days=today.weekday() + 7)
        formatted_start = DateFormatter.format_date(start_date, coach_date_format)
        # Берем только день и месяц
        if coach_date_format == 'ДД.ММ.ГГГГ':
            short_start = formatted_start[:5]  # ДД.ММ
        elif coach_date_format == 'ММ/ДД/ГГГГ':
            short_start = formatted_start[:5]  # ММ/ДД
        else:  # ГГГГ-ММ-ДД
            short_start = formatted_start[5:]  # ММ-ДД
        period_display = f"2 недели (с {short_start} по сегодня)"
    elif period == 'month':
        start_date = today.replace(day=1)
        formatted_start = DateFormatter.format_date(start_date, coach_date_format)
        # Берем только день и месяц
        if coach_date_format == 'ДД.ММ.ГГГГ':
            short_start = formatted_start[:5]  # ДД.ММ
        elif coach_date_format == 'ММ/ДД/ГГГГ':
            short_start = formatted_start[:5]  # ММ/ДД
        else:  # ГГГГ-ММ-ДД
            short_start = formatted_start[5:]  # ММ-ДД
        period_display = f"месяц (с {short_start} по сегодня)"
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


@router.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: CallbackQuery):
    """Вернуться в главное меню из раздела тренера"""
    from bot.keyboards import get_main_menu_keyboard
    from coach.coach_queries import is_user_coach

    user_id = callback.from_user.id
    is_coach = await is_user_coach(user_id)

    await callback.message.delete()
    await callback.message.answer(
        "Главное меню:",
        reply_markup=get_main_menu_keyboard(is_coach)
    )
    await callback.answer()
