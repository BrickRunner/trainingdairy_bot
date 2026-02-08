"""
Обработчики для модуля здоровья
"""

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, BufferedInputFile
from aiogram.fsm.context import FSMContext
from datetime import date, timedelta
import re
import logging

from health.health_fsm import HealthMetricsStates, HealthExportStates
from health.health_keyboards import (
    get_health_menu_keyboard,
    get_quick_input_keyboard,
    get_sleep_quality_keyboard,
    get_stats_period_keyboard,
    get_graphs_period_keyboard,
    get_cancel_keyboard,
    get_skip_cancel_keyboard,
    get_date_choice_keyboard
)
from health.health_queries import (
    save_health_metrics,
    get_health_metrics_by_date,
    get_latest_health_metrics,
    get_health_statistics,
    check_today_metrics_filled,
    get_current_week_metrics,
    get_current_month_metrics
)
from health.health_graphs import generate_health_graphs, generate_sleep_quality_graph
from health.sleep_analysis import SleepAnalyzer, format_sleep_analysis_message
from utils.date_formatter import DateFormatter, get_user_date_format
from database.queries import get_user_settings
from ai.ai_analyzer import analyze_health_statistics, is_ai_available

router = Router()
logger = logging.getLogger(__name__)



async def format_date_for_user(date_obj: date, user_id: int) -> str:
    """Форматировать дату согласно настройкам пользователя"""
    user_format = await get_user_date_format(user_id)
    return DateFormatter.format_date(date_obj, user_format)


async def get_date_format_description(user_id: int) -> str:
    """Получить описание формата даты для пользователя"""
    user_format = await get_user_date_format(user_id)
    return DateFormatter.get_format_description(user_format)


async def get_date_validation_pattern(user_id: int) -> str:
    """Получить паттерн валидации для формата даты пользователя"""
    user_format = await get_user_date_format(user_id)
    return DateFormatter.get_validation_pattern(user_format)


async def parse_user_date(date_str: str, user_id: int) -> date:
    """Распарсить дату из строки согласно настройкам пользователя"""
    user_format = await get_user_date_format(user_id)
    return DateFormatter.parse_date(date_str, user_format)


async def return_to_health_menu(message: Message):
    """Возврат в главное меню здоровья"""
    user_id = message.from_user.id
    filled = await check_today_metrics_filled(user_id)

    status_text = "📋 <b>Статус на сегодня:</b>\n"
    status_text += f"{'✅' if filled['morning_pulse'] else '❌'} Утренний пульс\n"
    status_text += f"{'✅' if filled['weight'] else '❌'} Вес\n"
    status_text += f"{'✅' if filled['sleep_duration'] else '❌'} Сон\n"

    await message.answer(
        f"❤️ <b>Здоровье и метрики</b>\n\n"
        f"{status_text}\n"
        f"Выберите действие:",
        reply_markup=get_health_menu_keyboard(),
        parse_mode="HTML"
    )



@router.message(F.text == "❤️ Здоровье")
async def health_menu(message: Message, state: FSMContext):
    """Главное меню раздела здоровья"""
    await state.clear()
    user_id = message.from_user.id

    logger.info(f"health_menu called for user_id = {user_id}")

    filled = await check_today_metrics_filled(user_id)

    status_text = "📋 <b>Статус на сегодня:</b>\n"
    status_text += f"{'✅' if filled['morning_pulse'] else '❌'} Утренний пульс\n"
    status_text += f"{'✅' if filled['weight'] else '❌'} Вес\n"
    status_text += f"{'✅' if filled['sleep_duration'] else '❌'} Сон\n"

    await message.answer(
        f"❤️ <b>Здоровье и метрики</b>\n\n"
        f"{status_text}\n"
        f"Выберите действие:",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )
    await message.answer(
        "Выберите действие:",
        reply_markup=get_health_menu_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "health:menu")
async def health_menu_callback(callback: CallbackQuery, state: FSMContext):
    """Возврат в меню здоровья"""

    await state.set_state(None)

    user_id = callback.from_user.id

    filled = await check_today_metrics_filled(user_id)

    status_text = "📋 <b>Статус на сегодня:</b>\n"
    status_text += f"{'✅' if filled['morning_pulse'] else '❌'} Утренний пульс\n"
    status_text += f"{'✅' if filled['weight'] else '❌'} Вес\n"
    status_text += f"{'✅' if filled['sleep_duration'] else '❌'} Сон\n"

    await callback.message.edit_text(
        f"❤️ <b>Здоровье и метрики</b>\n\n"
        f"{status_text}\n"
        f"Выберите действие:",
        reply_markup=get_health_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()



@router.callback_query(F.data == "health:add_metrics")
async def choose_input_type(callback: CallbackQuery):
    """Выбор типа ввода метрик"""
    user_id = callback.from_user.id

    from datetime import date
    today = date.today()
    today_metrics = await get_health_metrics_by_date(user_id, today)

    if today_metrics and (today_metrics.get('morning_pulse') or today_metrics.get('weight') or today_metrics.get('sleep_duration')):
        message_text = "📝 <b>Ваши данные на сегодня</b>"
    else:
        message_text = "📝 <b>Внесение данных</b>"

    await callback.message.edit_text(
        message_text,
        reply_markup=get_quick_input_keyboard(today_metrics),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "health:input_all")
async def start_full_input(callback: CallbackQuery, state: FSMContext):
    """Начало полного ввода всех метрик"""
    await callback.message.answer(
        "💗 Введите ваш <b>утренний пульс</b> (уд/мин):\n\n"
        "Например: 60",
        reply_markup=get_skip_cancel_keyboard(),
        parse_mode="HTML"
    )
    try:
        await callback.message.delete()
    except:
        pass
    await state.set_state(HealthMetricsStates.waiting_for_pulse)
    await callback.answer()


@router.callback_query(F.data == "health:input_pulse")
async def start_pulse_input(callback: CallbackQuery, state: FSMContext):
    """Ввод только пульса"""
    await callback.message.answer(
        "💗 Введите ваш <b>утренний пульс</b> (уд/мин):\n\n"
        "Например: 60",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    try:
        await callback.message.delete()
    except:
        pass
    await state.set_state(HealthMetricsStates.waiting_for_pulse)
    await state.update_data(quick_input='pulse')
    await callback.answer()


@router.callback_query(F.data == "health:input_weight")
async def start_weight_input(callback: CallbackQuery, state: FSMContext):
    """Ввод только веса"""
    user_id = callback.from_user.id
    settings = await get_user_settings(user_id)
    weight_unit = settings.get('weight_unit', 'кг') if settings else 'кг'
    weight_goal = settings.get('weight_goal') if settings else None

    message_text = f"⚖️ Введите ваш <b>вес</b> ({weight_unit}):\n\n"
    if weight_goal:
        message_text += f"Ваша цель: {weight_goal:.1f} {weight_unit}\n\n"
    message_text += "Например: 75.5"

    await callback.message.answer(
        message_text,
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(HealthMetricsStates.waiting_for_weight)
    await state.update_data(quick_input='weight')
    await callback.answer()


@router.callback_query(F.data == "health:input_sleep")
async def start_sleep_input(callback: CallbackQuery, state: FSMContext):
    """Ввод только сна"""
    await callback.message.answer(
        "😴 Введите <b>длительность сна</b> (часы):\n\n"
        "Например: 7.5 или 8",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(HealthMetricsStates.waiting_for_sleep_duration)
    await state.update_data(quick_input='sleep')
    await callback.answer()


@router.callback_query(F.data == "health:choose_date")
async def choose_date_for_metrics(callback: CallbackQuery, state: FSMContext):
    """Выбор даты для внесения данных"""
    from bot.calendar_keyboard import CalendarKeyboard
    from datetime import datetime

    calendar_keyboard = CalendarKeyboard.create_calendar(
        calendar_format=1,
        current_date=datetime.now(),
        callback_prefix="healthcal",
        max_date=datetime.now()
    )

    await callback.message.answer(
        "📅 <b>За какую дату вы хотите внести данные?</b>",
        reply_markup=get_date_choice_keyboard(),
        parse_mode="HTML"
    )

    await callback.message.answer(
        "Выберите дату:",
        reply_markup=calendar_keyboard
    )

    try:
        await callback.message.delete()
    except:
        pass
    await state.set_state(HealthMetricsStates.waiting_for_calendar_date)
    await callback.answer()



@router.callback_query(F.data.startswith("healthcal_"))
async def process_health_calendar(callback: CallbackQuery, state: FSMContext):
    """Обработка навигации и выбора даты в календаре здоровья"""
    from bot.calendar_keyboard import CalendarKeyboard

    callback_data = callback.data
    logger.info(f"=== CALENDAR CALLBACK RECEIVED: {callback_data} ===")
    logger.info(f"Current state: {await state.get_state()}")

    from datetime import datetime
    new_keyboard = CalendarKeyboard.handle_navigation(callback_data, prefix="healthcal", max_date=datetime.now())
    logger.info(f"Navigation result: {new_keyboard is not None}")

    if new_keyboard:
        await callback.message.edit_reply_markup(reply_markup=new_keyboard)
        await callback.answer()
        return

    parsed = CalendarKeyboard.parse_callback_data(callback_data)
    logger.info(f"Parsed callback data: {parsed}")
    logger.info(f"Action: {parsed.get('action')}, Format: {parsed.get('format')}, Date: {parsed.get('date')}")

    if parsed.get("action") == "select" and parsed.get("format") == 1:
        logger.info(">>> DATE SELECTION BLOCK ENTERED <<<")
        selected_date = parsed["date"].date()

        if selected_date > date.today():
            await callback.answer("❌ Нельзя вносить данные за будущую дату.", show_alert=True)
            return

        await state.update_data(selected_date=selected_date)

        user_id = callback.from_user.id
        metrics = await get_health_metrics_by_date(user_id, selected_date)

        date_str = await format_date_for_user(selected_date, user_id)

        if metrics and (metrics.get('morning_pulse') or metrics.get('weight') or metrics.get('sleep_duration')):
            message_text = f"📝 <b>Ваши данные на {date_str}</b>"
        else:
            message_text = f"📝 <b>Внесение данных за {date_str}</b>"

        await callback.message.answer(
            message_text,
            reply_markup=get_quick_input_keyboard(metrics),
            parse_mode="HTML"
        )

        await callback.message.delete()

        await state.set_state(None)
        await callback.answer()
    else:
        logger.warning(f"❌ Date selection condition NOT met. Action='{parsed.get('action')}', Format={parsed.get('format')}")
        logger.warning(f"Full parsed data: {parsed}")
        await callback.answer("⚠️ Ошибка обработки календаря. Попробуйте еще раз.")


@router.message(HealthMetricsStates.waiting_for_calendar_date)
async def process_date_choice(message: Message, state: FSMContext):
    """Обработка выбора даты через быстрые кнопки"""
    if message.text == "❌ Отменить":
        await state.set_state(None)
        await message.answer(
            "Действие отменено.",
            reply_markup=ReplyKeyboardRemove()
        )
        await return_to_health_menu(message)
        return

    today = date.today()

    if message.text == "📅 Сегодня":
        selected_date = today
    elif message.text == "📅 Вчера":
        selected_date = today - timedelta(days=1)
    elif message.text == "📅 Позавчера":
        selected_date = today - timedelta(days=2)
    else:
        await message.answer(
            "❌ Неверный выбор. Используйте кнопки."
        )
        return

    await state.update_data(selected_date=selected_date)

    user_id = message.from_user.id
    metrics = await get_health_metrics_by_date(user_id, selected_date)

    date_str = await format_date_for_user(selected_date, user_id)

    if metrics and (metrics.get('morning_pulse') or metrics.get('weight') or metrics.get('sleep_duration')):
        message_text = f"📝 <b>Ваши данные на {date_str}</b>"
    else:
        message_text = f"📝 <b>Внесение данных за {date_str}</b>"

    await message.answer(
        message_text,
        reply_markup=get_quick_input_keyboard(metrics),
        parse_mode="HTML"
    )
    await state.set_state(None)


@router.message(HealthMetricsStates.waiting_for_custom_date)
async def process_custom_date(message: Message, state: FSMContext):
    """Обработка ввода произвольной даты"""
    if message.text == "❌ Отменить":
        await state.set_state(None)
        await message.answer(
            "Действие отменено.",
            reply_markup=ReplyKeyboardRemove()
        )
        await return_to_health_menu(message)
        return

    user_id = message.from_user.id

    try:
        selected_date = await parse_user_date(message.text, user_id)
    except ValueError:
        date_format_desc = await get_date_format_description(user_id)
        await message.answer(
            f"❌ Неверный формат даты. Используйте формат {date_format_desc}"
        )
        return

    if selected_date > date.today():
        await message.answer(
            "❌ Нельзя вносить данные за будущую дату."
        )
        return

    await state.update_data(selected_date=selected_date)

    metrics = await get_health_metrics_by_date(user_id, selected_date)

    date_str = await format_date_for_user(selected_date, user_id)

    if metrics and (metrics.get('morning_pulse') or metrics.get('weight') or metrics.get('sleep_duration')):
        message_text = f"📝 <b>Ваши данные на {date_str}</b>"
    else:
        message_text = f"📝 <b>Внесение данных за {date_str}</b>"

    await message.answer(
        message_text,
        reply_markup=get_quick_input_keyboard(metrics),
        parse_mode="HTML"
    )
    await state.set_state(None)



@router.message(HealthMetricsStates.waiting_for_pulse)
async def process_pulse(message: Message, state: FSMContext):
    """Обработка ввода пульса"""
    if message.text == "❌ Отменить":
        await state.clear()
        await message.answer(
            "Ввод данных отменен.",
            reply_markup=ReplyKeyboardRemove()
        )
        await return_to_health_menu(message)
        return

    if message.text == "⏭️ Пропустить":
        await state.update_data(pulse=None)
        await ask_weight(message, state)
        return

    try:
        pulse = int(message.text)
        if not (30 <= pulse <= 200):
            await message.answer("❌ Пульс должен быть в диапазоне 30-200 уд/мин")
            return
    except ValueError:
        await message.answer("❌ Введите число")
        return

    await state.update_data(pulse=pulse)

    user_id = message.from_user.id
    data = await state.get_data()
    selected_date = data.get('selected_date', date.today())

    yesterday = selected_date - timedelta(days=1)
    yesterday_metrics = await get_health_metrics_by_date(user_id, yesterday)

    if yesterday_metrics and yesterday_metrics.get('morning_pulse'):
        yesterday_pulse = yesterday_metrics['morning_pulse']
        pulse_diff = pulse - yesterday_pulse

        if pulse_diff >= 20:
            await message.answer(
                f"⚠️ <b>Внимание!</b>\n\n"
                f"Ваш пульс сегодня <b>{pulse} уд/мин</b>, что на <b>+{pulse_diff} уд/мин</b> "
                f"выше, чем вчера ({yesterday_pulse} уд/мин).\n\n"
                f"💡 <b>Рекомендация:</b>\n"
                f"Повышенный пульс может указывать на:\n"
                f"• Недостаточное восстановление\n"
                f"• Начало болезни\n"
                f"• Переутомление\n"
                f"• Стресс\n\n"
                f"Рекомендуем сегодня <b>отдохнуть</b> или снизить интенсивность тренировок. "
                f"Прислушайтесь к своему организму! 🙏",
                parse_mode="HTML"
            )

    if data.get('quick_input') == 'pulse':
        await save_and_finish(message, state, morning_pulse=pulse)
    else:
        await ask_weight(message, state)


async def ask_weight(message: Message, state: FSMContext):
    """Запрос веса"""
    user_id = message.from_user.id
    settings = await get_user_settings(user_id)
    weight_unit = settings.get('weight_unit', 'кг') if settings else 'кг'
    weight_goal = settings.get('weight_goal') if settings else None

    message_text = f"⚖️ Введите ваш <b>вес</b> ({weight_unit}):\n\n"
    if weight_goal:
        message_text += f"Ваша цель: {weight_goal:.1f} {weight_unit}\n\n"
    message_text += "Например: 75.5"

    await message.answer(
        message_text,
        reply_markup=get_skip_cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(HealthMetricsStates.waiting_for_weight)


@router.message(HealthMetricsStates.waiting_for_weight)
async def process_weight(message: Message, state: FSMContext):
    """Обработка ввода веса"""
    if message.text == "❌ Отменить":
        await state.clear()
        await message.answer(
            "Ввод данных отменен.",
            reply_markup=ReplyKeyboardRemove()
        )
        await return_to_health_menu(message)
        return

    if message.text == "⏭️ Пропустить":
        await state.update_data(weight=None)
        data = await state.get_data()
        if data.get('quick_input'):
            await save_and_finish(message, state)
        else:
            await ask_sleep_duration(message, state)
        return

    try:
        weight = float(message.text.replace(',', '.'))
        if not (30 <= weight <= 300):
            await message.answer("❌ Вес должен быть в диапазоне 30-300 кг")
            return
    except ValueError:
        await message.answer("❌ Введите число")
        return

    await state.update_data(weight=weight)

    data = await state.get_data()
    if data.get('quick_input') == 'weight':
        await save_and_finish(message, state, weight=weight)
    else:
        await ask_sleep_duration(message, state)


async def ask_sleep_duration(message: Message, state: FSMContext):
    """Запрос длительности сна"""
    await message.answer(
        "😴 Введите <b>длительность сна</b>:\n\n"
        "Примеры:\n"
        "• 7:30 (7 часов 30 минут)\n"
        "• 8:00 (8 часов)\n"
        "• 7.5 (7.5 часов)\n"
        "• 8 (8 часов)",
        reply_markup=get_skip_cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(HealthMetricsStates.waiting_for_sleep_duration)


@router.message(HealthMetricsStates.waiting_for_sleep_duration)
async def process_sleep_duration(message: Message, state: FSMContext):
    """Обработка ввода длительности сна"""
    if message.text == "❌ Отменить":
        await state.clear()
        await message.answer(
            "Ввод данных отменен.",
            reply_markup=ReplyKeyboardRemove()
        )
        await return_to_health_menu(message)
        return

    if message.text == "⏭️ Пропустить":
        await state.update_data(sleep_duration=None)
        data = await state.get_data()
        if data.get('quick_input'):
            await save_and_finish(message, state)
        else:
            await ask_sleep_quality(message, state)
        return

    try:
        text = message.text.strip()

        if ':' in text:
            parts = text.split(':')
            if len(parts) != 2:
                await message.answer("❌ Неверный формат. Используйте ЧЧ:ММ или Ч:М (например: 7:30 или 7:0)")
                return

            hours = int(parts[0])
            minutes = int(parts[1])

            if not (0 <= hours <= 20):
                await message.answer("❌ Часы должны быть в диапазоне 0-20")
                return

            if not (0 <= minutes < 60):
                await message.answer("❌ Минуты должны быть в диапазоне 0-59")
                return

            sleep_duration = hours + (minutes / 60.0)
        else:
            sleep_duration = float(text.replace(',', '.'))

        if not (1 <= sleep_duration <= 20):
            await message.answer("❌ Длительность сна должна быть в диапазоне 1-20 часов")
            return

    except ValueError:
        await message.answer("❌ Неверный формат. Примеры: 7:30 или 7.5 или 8")
        return

    await state.update_data(sleep_duration=sleep_duration)

    data = await state.get_data()
    if data.get('quick_input') == 'sleep':
        await ask_sleep_quality(message, state)
    else:
        await ask_sleep_quality(message, state)


async def ask_sleep_quality(message: Message, state: FSMContext):
    """Запрос качества сна"""
    await message.answer(
        "😴 Оцените <b>качество вашего сна</b>:\n\n"
        "1 - Очень плохо\n"
        "5 - Отлично",
        reply_markup=get_sleep_quality_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(HealthMetricsStates.waiting_for_sleep_quality)


@router.callback_query(F.data.startswith("sleep_quality:"))
async def process_sleep_quality(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора качества сна"""
    quality_str = callback.data.split(":")[1]

    if quality_str == "skip":
        await state.update_data(sleep_quality=None)
    else:
        quality = int(quality_str)
        await state.update_data(sleep_quality=quality)

    await save_and_finish(callback.message, state, user_id=callback.from_user.id)
    await callback.answer()


async def save_and_finish(message: Message, state: FSMContext, **extra_data):
    """Сохранение данных и завершение"""
    data = await state.get_data()

    user_id = extra_data.pop('user_id', None)

    if user_id is None:
        user_id = message.from_user.id if hasattr(message, 'from_user') else message.chat.id

    data.update(extra_data)

    metric_date = data.get('selected_date', date.today())

    logger.info(f"save_and_finish: user_id = {user_id}")
    logger.info(f"save_and_finish: data from state = {data}")
    logger.info(f"save_and_finish: extra_data = {extra_data}")
    logger.info(f"save_and_finish: metric_date = {metric_date}")

    save_params = {
        'user_id': user_id,
        'metric_date': metric_date
    }

    if 'pulse' in data and data['pulse'] is not None:
        save_params['morning_pulse'] = data['pulse']
    if 'weight' in data and data['weight'] is not None:
        save_params['weight'] = data['weight']
    if 'sleep_duration' in data and data['sleep_duration'] is not None:
        save_params['sleep_duration'] = data['sleep_duration']
    if 'sleep_quality' in data and data['sleep_quality'] is not None:
        save_params['sleep_quality'] = data['sleep_quality']

    logger.info(f"save_and_finish: save_params = {save_params}")

    success = await save_health_metrics(**save_params)

    if success:
        settings = await get_user_settings(user_id)
        weight_goal = settings.get('weight_goal') if settings else None
        weight_unit = settings.get('weight_unit', 'кг') if settings else 'кг'

        saved_items = []
        if data.get('pulse'):
            saved_items.append(f"💗 Пульс: {data['pulse']} уд/мин")
        if data.get('weight'):
            weight_text = f"⚖️ Вес: {data['weight']} {weight_unit}"

            if weight_goal:
                diff = data['weight'] - weight_goal
                if abs(diff) < 0.1:
                    weight_text += f" (🎯 цель достигнута!)"
                elif diff > 0:
                    weight_text += f" (до цели: -{diff:.1f} {weight_unit})"
                else:
                    weight_text += f" (превышение цели: +{abs(diff):.1f} {weight_unit})"

            saved_items.append(weight_text)
        if data.get('sleep_duration'):
            duration = data['sleep_duration']
            total_minutes = round(duration * 60)
            hours = total_minutes // 60
            minutes = total_minutes % 60
            if minutes > 0:
                saved_items.append(f"😴 Сон: {hours} ч {minutes} мин")
            else:
                saved_items.append(f"😴 Сон: {hours} ч")
        if data.get('sleep_quality'):
            saved_items.append(f"⭐ Качество: {data['sleep_quality']}/5")

        filled = await check_today_metrics_filled(user_id)
        status_text = "\n\n📋 <b>Статус на сегодня:</b>\n"
        status_text += f"{'✅' if filled['morning_pulse'] else '❌'} Утренний пульс\n"
        status_text += f"{'✅' if filled['weight'] else '❌'} Вес\n"
        status_text += f"{'✅' if filled['sleep_duration'] else '❌'} Сон"

        await message.answer(
            "✅ <b>Данные успешно сохранены!</b>\n\n" +
            "\n".join(saved_items) + status_text,
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="HTML"
        )

        updated_metrics = await get_health_metrics_by_date(user_id, metric_date)

        date_str = await format_date_for_user(metric_date, user_id)
        is_today = metric_date == date.today()

        if updated_metrics and (updated_metrics.get('morning_pulse') or updated_metrics.get('weight') or updated_metrics.get('sleep_duration')):
            if is_today:
                message_text = "📝 <b>Ваши данные на сегодня</b>"
            else:
                message_text = f"📝 <b>Ваши данные на {date_str}</b>"
        else:
            if is_today:
                message_text = "📝 <b>Внесение данных</b>"
            else:
                message_text = f"📝 <b>Внесение данных за {date_str}</b>"

        await message.answer(
            message_text,
            reply_markup=get_quick_input_keyboard(updated_metrics),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "❌ Ошибка при сохранении данных. Попробуйте позже.",
            reply_markup=ReplyKeyboardRemove()
        )




@router.callback_query(F.data == "health:stats_and_graphs")
async def show_stats_graphs_periods(callback: CallbackQuery):
    """Выбор периода для статистики и графиков"""
    await callback.message.edit_text(
        "📊 <b>Статистика и графики</b>\n\n"
        "Выберите период:",
        reply_markup=get_stats_period_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("health_stats_graphs:"))
async def show_stats_and_graphs(callback: CallbackQuery):
    """Показ статистики и графиков за период"""
    period_param = callback.data.split(":")[1]
    user_id = callback.from_user.id

    logger.info(f"=== SHOW_STATS_AND_GRAPHS CALLED ===")
    logger.info(f"User ID: {user_id}")
    logger.info(f"Period param: {period_param}")

    await callback.answer("⏳ Загрузка данных...", show_alert=True)

    if period_param == "week":
        metrics = await get_current_week_metrics(user_id)
        period_name = "эту неделю"
        logger.info(f"Period: CURRENT WEEK")
    elif period_param == "month":
        metrics = await get_current_month_metrics(user_id)
        period_name = "этот месяц"
        logger.info(f"Period: CURRENT MONTH")
    else:
        days = int(period_param)
        metrics = await get_latest_health_metrics(user_id, days)
        period_name = f"{days} дней"
        logger.info(f"Period: LAST {days} DAYS")

    logger.info(f"Metrics retrieved: {len(metrics)} records")
    if metrics:
        logger.info("Dates in metrics:")
        for m in metrics:
            logger.info(f"  {m['date']}: pulse={m.get('morning_pulse')}, weight={m.get('weight')}, sleep={m.get('sleep_duration')}")

    if not metrics:
        stats = {}
    else:
        pulse_values = [m['morning_pulse'] for m in metrics if m.get('morning_pulse')]
        weight_values = [m['weight'] for m in metrics if m.get('weight')]
        sleep_values = [m['sleep_duration'] for m in metrics if m.get('sleep_duration')]

        from health.health_queries import _calculate_trend

        stats = {
            'total_days': len(metrics),
            'pulse': {
                'avg': sum(pulse_values) / len(pulse_values) if pulse_values else None,
                'min': min(pulse_values) if pulse_values else None,
                'max': max(pulse_values) if pulse_values else None,
                'trend': _calculate_trend(pulse_values) if len(pulse_values) > 1 else None
            },
            'weight': {
                'current': weight_values[-1] if weight_values else None,
                'start': weight_values[0] if weight_values else None,
                'change': (weight_values[-1] - weight_values[0]) if len(weight_values) > 1 else None,
                'trend': _calculate_trend(weight_values) if len(weight_values) > 1 else None
            },
            'sleep': {
                'avg': sum(sleep_values) / len(sleep_values) if sleep_values else None,
                'min': min(sleep_values) if sleep_values else None,
                'max': max(sleep_values) if sleep_values else None
            }
        }

    if not stats and not metrics:
        filled = await check_today_metrics_filled(user_id)
        status_text = "📋 <b>Статус на сегодня:</b>\n"
        status_text += f"{'✅' if filled['morning_pulse'] else '❌'} Утренний пульс\n"
        status_text += f"{'✅' if filled['weight'] else '❌'} Вес\n"
        status_text += f"{'✅' if filled['sleep_duration'] else '❌'} Сон\n"

        await callback.message.edit_text(
            f"❌ Нет данных за {period_name}\n\n"
            f"❤️ <b>Здоровье и метрики</b>\n\n"
            f"{status_text}\n"
            f"Выберите действие:",
            reply_markup=get_health_menu_keyboard(),
            parse_mode="HTML"
        )
        return

    msg = f"📊 <b>Статистика за {period_name}</b>\n\n"

    if stats and stats['pulse']['avg']:
        msg += f"💗 <b>Утренний пульс:</b>\n"
        msg += f"   Среднее: {stats['pulse']['avg']:.1f} уд/мин\n"
        msg += f"   Диапазон: {stats['pulse']['min']} - {stats['pulse']['max']}\n"
        trend = stats['pulse']['trend']
        trend_emoji = "📈" if trend == "increasing" else "📉" if trend == "decreasing" else "➡️"
        msg += f"   Тренд: {trend_emoji}\n\n"

    if stats and stats['weight']['current']:
        msg += f"⚖️ <b>Вес:</b>\n"
        msg += f"   Текущий: {stats['weight']['current']:.1f} кг\n"
        if stats['weight']['change']:
            change = stats['weight']['change']
            change_emoji = "📈" if change > 0 else "📉"
            msg += f"   Изменение: {change_emoji} {change:+.1f} кг\n"
        trend = stats['weight']['trend']
        trend_emoji = "📈" if trend == "increasing" else "📉" if trend == "decreasing" else "➡️"
        msg += f"   Тренд: {trend_emoji}\n\n"

    if stats and stats['sleep']['avg']:
        avg_hours = int(stats['sleep']['avg'])
        avg_minutes = round((stats['sleep']['avg'] - avg_hours) * 60)
        if avg_minutes == 60:
            avg_hours += 1
            avg_minutes = 0
        avg_text = f"{avg_hours} ч {avg_minutes} мин" if avg_minutes > 0 else f"{avg_hours} ч"

        min_hours = int(stats['sleep']['min'])
        min_minutes = round((stats['sleep']['min'] - min_hours) * 60)
        if min_minutes == 60:
            min_hours += 1
            min_minutes = 0
        min_text = f"{min_hours}:{min_minutes:02d}" if min_minutes > 0 else f"{min_hours}:00"

        max_hours = int(stats['sleep']['max'])
        max_minutes = round((stats['sleep']['max'] - max_hours) * 60)
        if max_minutes == 60:
            max_hours += 1
            max_minutes = 0
        max_text = f"{max_hours}:{max_minutes:02d}" if max_minutes > 0 else f"{max_hours}:00"

        msg += f"😴 <b>Сон:</b>\n"
        msg += f"   Среднее: {avg_text}\n"
        msg += f"   Диапазон: {min_text} - {max_text}\n"

        avg_sleep = stats['sleep']['avg']
        if 7 <= avg_sleep <= 9:
            msg += f"   Оценка: ✅ В норме\n"
        elif avg_sleep < 7:
            msg += f"   Оценка: ⚠️ Недостаточно\n"
        else:
            msg += f"   Оценка: ⚠️ Избыточно\n"

    await callback.message.answer(msg, parse_mode="HTML")

    if metrics:
        try:
            logger.info(f"Generating graph with {len(metrics)} metrics, period_name={period_name}")
            logger.info(f"Metrics being passed to graph generation:")
            for m in metrics:
                logger.info(f"  {m['date']}: pulse={m.get('morning_pulse')}, weight={m.get('weight')}, sleep={m.get('sleep_duration')}")

            settings = await get_user_settings(user_id)
            weight_goal = settings.get('weight_goal') if settings else None

            graph_buffer = await generate_health_graphs(metrics, period_name, weight_goal)
            logger.info(f"Graph generated successfully, buffer size: {len(graph_buffer.getvalue())} bytes")

            photo = BufferedInputFile(graph_buffer.read(), filename=f"health_stats.png")
            await callback.message.answer_photo(
                photo=photo,
                caption=f"📈 Графики метрик здоровья за {period_name}"
            )
            logger.info("Graph sent to user successfully")
        except Exception as e:
            logger.error(f"Ошибка при генерации графиков: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await callback.message.answer("❌ Ошибка при генерации графиков")

    from health.health_keyboards import get_health_stats_actions_keyboard

    await callback.message.answer(
        "Что дальше?",
        reply_markup=get_health_stats_actions_keyboard(period_param),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("ai_analyze_health:"))
async def ai_analyze_health(callback: CallbackQuery):
    """AI-анализ статистики здоровья за период"""
    period_param = callback.data.split(":")[1]
    user_id = callback.from_user.id

    if not is_ai_available():
        await callback.answer(
            "❌ AI-анализ недоступен. Добавьте OPENROUTER_API_KEY в .env файл",
            show_alert=True
        )
        return

    await callback.answer("🤖 Анализирую данные...", show_alert=False)

    processing_msg = await callback.message.answer("🤖 AI анализирует показатели здоровья...")

    try:
        user_settings = await get_user_settings(user_id)
        weight_unit = user_settings.get('weight_unit', 'кг') if user_settings else 'кг'

        if period_param == "week":
            metrics = await get_current_week_metrics(user_id)
            period_name = "эту неделю"
            days = 7
        elif period_param == "month":
            metrics = await get_current_month_metrics(user_id)
            period_name = "этот месяц"
            days = 30
        else:
            days = int(period_param)
            metrics = await get_latest_health_metrics(user_id, days)
            period_name = f"{days} дней"

        statistics = await get_health_statistics(user_id, days)

        if not metrics:
            await processing_msg.edit_text(
                "❌ Нет данных за выбранный период для анализа"
            )
            return

        analysis = await analyze_health_statistics(
            statistics=statistics,
            metrics=metrics,
            period_name=period_name,
            weight_unit=weight_unit
        )

        if analysis:
            import html
            from bot.keyboards import get_main_menu_keyboard

            safe_analysis = html.escape(analysis)

            msg_text = (
                f"🤖 <b>AI-анализ здоровья за {period_name}</b>\n\n"
                f"{safe_analysis}\n\n"
                f"<i>Анализ создан с помощью Google Gemini</i>"
            )

            await processing_msg.edit_text(msg_text, parse_mode="HTML")

            from coach.coach_queries import is_user_coach
            is_coach_status = await is_user_coach(user_id)
            await processing_msg.answer(
                "Выбери действие из меню 👇",
                reply_markup=get_main_menu_keyboard(is_coach_status)
            )
        else:
            await processing_msg.edit_text(
                "❌ Не удалось создать AI-анализ. Попробуйте позже."
            )

    except Exception as e:
        logger.error(f"Ошибка при AI-анализе здоровья: {e}")
        await processing_msg.edit_text(
            "❌ Произошла ошибка при анализе. Попробуйте позже."
        )


@router.callback_query(F.data == "health:statistics")
async def show_statistics_periods(callback: CallbackQuery):
    """Выбор периода для статистики (перенаправление на новый обработчик)"""
    await show_stats_graphs_periods(callback)


@router.callback_query(F.data == "health:graphs")
async def show_graphs_periods(callback: CallbackQuery):
    """Выбор периода для графиков (перенаправление на новый обработчик)"""
    await show_stats_graphs_periods(callback)



@router.callback_query(F.data == "health:sleep_analysis")
async def show_sleep_analysis(callback: CallbackQuery):
    """Глубокий анализ сна"""
    user_id = callback.from_user.id

    await callback.answer("⏳ Анализирую данные...", show_alert=True)

    metrics = await get_latest_health_metrics(user_id, 30)

    if not metrics or len(metrics) < 3:
        filled = await check_today_metrics_filled(user_id)
        status_text = "📋 <b>Статус на сегодня:</b>\n"
        status_text += f"{'✅' if filled['morning_pulse'] else '❌'} Утренний пульс\n"
        status_text += f"{'✅' if filled['weight'] else '❌'} Вес\n"
        status_text += f"{'✅' if filled['sleep_duration'] else '❌'} Сон\n"

        await callback.message.answer(
            "❌ Недостаточно данных для анализа.\n\n"
            "Для полного анализа нужно минимум 3 дня с данными о сне.\n\n"
            f"❤️ <b>Здоровье и метрики</b>\n\n"
            f"{status_text}\n"
            f"Выберите действие:",
            reply_markup=get_health_menu_keyboard(),
            parse_mode="HTML"
        )
        return

    try:
        analyzer = SleepAnalyzer(metrics)
        analysis = analyzer.get_full_analysis()

        message_text = format_sleep_analysis_message(analysis)

        await callback.message.answer(
            message_text,
            parse_mode="HTML"
        )

        graph_buffer = await generate_sleep_quality_graph(metrics, "30 дней")
        photo = BufferedInputFile(graph_buffer.read(), filename="sleep_analysis.png")
        await callback.message.answer_photo(
            photo=photo,
            caption="📊 График анализа сна"
        )

        filled = await check_today_metrics_filled(user_id)
        status_text = "📋 <b>Статус на сегодня:</b>\n"
        status_text += f"{'✅' if filled['morning_pulse'] else '❌'} Утренний пульс\n"
        status_text += f"{'✅' if filled['weight'] else '❌'} Вес\n"
        status_text += f"{'✅' if filled['sleep_duration'] else '❌'} Сон\n"

        await callback.message.answer(
            f"❤️ <b>Здоровье и метрики</b>\n\n"
            f"{status_text}\n"
            f"Выберите действие:",
            reply_markup=get_health_menu_keyboard(),
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Ошибка при анализе сна: {e}")

        filled = await check_today_metrics_filled(user_id)
        status_text = "📋 <b>Статус на сегодня:</b>\n"
        status_text += f"{'✅' if filled['morning_pulse'] else '❌'} Утренний пульс\n"
        status_text += f"{'✅' if filled['weight'] else '❌'} Вес\n"
        status_text += f"{'✅' if filled['sleep_duration'] else '❌'} Сон\n"

        await callback.message.answer(
            "❌ Ошибка при анализе данных\n\n"
            f"❤️ <b>Здоровье и метрики</b>\n\n"
            f"{status_text}\n"
            f"Выберите действие:",
            reply_markup=get_health_menu_keyboard(),
            parse_mode="HTML"
        )








@router.callback_query(F.data.startswith("health_export:"))
async def export_health_pdf(callback: CallbackQuery, state: FSMContext):
    """Экспорт данных здоровья в PDF"""
    period_param = callback.data.split(":")[1]
    user_id = callback.from_user.id

    if period_param == "custom":
        user_id = callback.from_user.id
        date_format_desc = await get_date_format_description(user_id)

        from bot.calendar_keyboard import CalendarKeyboard
        from datetime import datetime
        calendar_keyboard = CalendarKeyboard.create_calendar(
            calendar_format=1,
            current_date=datetime.now(),
            callback_prefix="health_export_start",
            max_date=datetime.now(),
            show_cancel=True,
            cancel_callback="health:export:cancel"
        )

        await callback.message.edit_text(
            f"📅 <b>Произвольный период</b>\n\n"
            f"Выберите дату начала из календаря или введите вручную в формате {date_format_desc}",
            reply_markup=calendar_keyboard,
            parse_mode="HTML"
        )

        await state.set_state(HealthExportStates.waiting_for_start_date)
        await callback.answer()
        return

    await callback.answer("⏳ Генерирую PDF...", show_alert=True)

    try:
        from health.health_pdf_export import create_health_pdf

        pdf_buffer = await create_health_pdf(user_id, period_param)

        if period_param == "week":
            period_name = "неделю"
            filename_part = "week"
        elif period_param == "month":
            period_name = "месяц"
            filename_part = "month"
        elif period_param == "180":
            period_name = "полгода"
            filename_part = "6months"
        elif period_param == "365":
            period_name = "год"
            filename_part = "year"
        else:
            period_name = f"{period_param} дней"
            filename_part = f"{period_param}days"

        filename = f"health_{filename_part}_{date.today().strftime('%Y%m%d')}.pdf"

        document = BufferedInputFile(pdf_buffer.read(), filename=filename)
        await callback.message.answer_document(
            document=document,
            caption=f"📄 Экспорт данных здоровья за {period_name}"
        )

        logger.info(f"PDF экспорт здоровья успешно создан для пользователя {user_id}, период: {period_param}")

        from bot.keyboards import get_export_type_keyboard
        await callback.message.answer(
            "📥 <b>Экспорт в PDF</b>\n\n"
            "Выберите, что вы хотите экспортировать:",
            parse_mode="HTML",
            reply_markup=get_export_type_keyboard()
        )

    except ValueError as e:
        logger.error(f"Ошибка при экспорте PDF: {e}")
        await callback.message.answer(
            f"❌ {str(e)}\n\n"
            "Попробуйте выбрать другой период или внесите больше данных."
        )

        filled = await check_today_metrics_filled(user_id)
        status_text = "📋 <b>Статус на сегодня:</b>\n"
        status_text += f"{'✅' if filled['morning_pulse'] else '❌'} Утренний пульс\n"
        status_text += f"{'✅' if filled['weight'] else '❌'} Вес\n"
        status_text += f"{'✅' if filled['sleep_duration'] else '❌'} Сон\n"

        await callback.message.answer(
            f"❤️ <b>Здоровье и метрики</b>\n\n"
            f"{status_text}\n"
            f"Выберите действие:",
            reply_markup=get_health_menu_keyboard(),
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Неожиданная ошибка при экспорте PDF: {e}", exc_info=True)
        await callback.message.answer(
            "❌ Произошла ошибка при генерации PDF. Попробуйте позже."
        )

        filled = await check_today_metrics_filled(user_id)
        status_text = "📋 <b>Статус на сегодня:</b>\n"
        status_text += f"{'✅' if filled['morning_pulse'] else '❌'} Утренний пульс\n"
        status_text += f"{'✅' if filled['weight'] else '❌'} Вес\n"
        status_text += f"{'✅' if filled['sleep_duration'] else '❌'} Сон\n"

        await callback.message.answer(
            f"❤️ <b>Здоровье и метрики</b>\n\n"
            f"{status_text}\n"
            f"Выберите действие:",
            reply_markup=get_health_menu_keyboard(),
            parse_mode="HTML"
        )


@router.message(HealthExportStates.waiting_for_start_date)
async def process_export_start_date(message: Message, state: FSMContext):
    """Обработка даты начала периода экспорта"""
    user_id = message.from_user.id

    try:
        start_date = await parse_user_date(message.text, user_id)

        if start_date > date.today():
            await message.answer(
                "❌ Дата начала не может быть в будущем!\n\n"
                "Введите корректную дату:"
            )
            return

        await state.update_data(export_start_date=start_date)

        date_format_desc = await get_date_format_description(user_id)
        formatted_start = await format_date_for_user(start_date, user_id)

        from bot.calendar_keyboard import CalendarKeyboard
        from datetime import datetime
        calendar_keyboard = CalendarKeyboard.create_calendar(
            calendar_format=1,
            current_date=datetime.now(),
            callback_prefix="health_export_end",
            max_date=datetime.now(),
            show_cancel=True,
            cancel_callback="health:export:cancel"
        )

        await message.answer(
            f"✅ Дата начала: {formatted_start}\n\n"
            f"📅 Теперь выберите дату окончания из календаря или введите вручную в формате {date_format_desc}",
            parse_mode="HTML",
            reply_markup=calendar_keyboard
        )

        await state.set_state(HealthExportStates.waiting_for_end_date)

    except ValueError:
        date_format_desc = await get_date_format_description(user_id)
        await message.answer(
            f"❌ Неверный формат даты!\n\n"
            f"Введите дату в формате {date_format_desc}"
        )


@router.message(HealthExportStates.waiting_for_end_date)
async def process_export_end_date(message: Message, state: FSMContext):
    """Обработка даты окончания периода экспорта и генерация PDF"""
    user_id = message.from_user.id

    try:
        end_date = await parse_user_date(message.text, user_id)

        if end_date > date.today():
            await message.answer(
                "❌ Дата окончания не может быть в будущем!\n\n"
                "Введите корректную дату:"
            )
            return

        data = await state.get_data()
        start_date = data.get('export_start_date')

        if end_date < start_date:
            formatted_start = await format_date_for_user(start_date, user_id)
            await message.answer(
                f"❌ Дата окончания не может быть раньше даты начала!\n\n"
                f"Дата начала: {formatted_start}\n"
                f"Введите дату окончания (не раньше даты начала):"
            )
            return

        await state.clear()

        try:
            from health.health_pdf_export import create_health_pdf
            from health.health_queries import get_health_metrics_range

            metrics = await get_health_metrics_range(user_id, start_date, end_date)

            if not metrics:
                formatted_start = await format_date_for_user(start_date, user_id)
                formatted_end = await format_date_for_user(end_date, user_id)
                await message.answer(
                    f"❌ Нет данных за период с {formatted_start} по {formatted_end}\n\n"
                    "Попробуйте выбрать другой период."
                )
                await return_to_health_menu(message)
                return

            formatted_start = await format_date_for_user(start_date, user_id)
            formatted_end = await format_date_for_user(end_date, user_id)
            period_name = f"{formatted_start} - {formatted_end}"

            await state.update_data(custom_metrics=metrics, custom_period_name=period_name)

            period_param = f"custom_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
            pdf_buffer = await create_health_pdf(user_id, period_param)

            await state.clear()

            filename = f"health_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf"

            document = BufferedInputFile(pdf_buffer.read(), filename=filename)
            await message.answer_document(
                document=document,
                caption=f"📄 Экспорт данных здоровья за период:\n{period_name}"
            )

            logger.info(f"PDF экспорт здоровья (произвольный период) успешно создан для пользователя {user_id}")

            await return_to_health_menu(message)

        except Exception as e:
            logger.error(f"Ошибка при экспорте PDF (произвольный период): {e}", exc_info=True)
            await message.answer(
                "❌ Произошла ошибка при генерации PDF. Попробуйте позже."
            )
            await return_to_health_menu(message)

    except ValueError:
        date_format_desc = await get_date_format_description(user_id)
        await message.answer(
            f"❌ Неверный формат даты!\n\n"
            f"Введите дату в формате {date_format_desc}"
        )


@router.callback_query(F.data == "daily_reminder:yes")
async def handle_daily_reminder_yes(callback: CallbackQuery, state: FSMContext):
    """Обработка согласия на ввод данных из ежедневного напоминания"""
    await callback.answer()

    user_id = callback.from_user.id

    await state.clear()

    today = date.today()
    await state.update_data(selected_date=today)

    metrics = await get_health_metrics_by_date(user_id, today)

    try:
        await callback.message.delete()
    except:
        pass

    await callback.message.answer(
        "💗 Введите ваш <b>утренний пульс</b> (уд/мин):\n\n"
        "Например: 60",
        reply_markup=get_skip_cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(HealthMetricsStates.waiting_for_pulse)


@router.callback_query(F.data == "daily_reminder:no")
async def handle_daily_reminder_no(callback: CallbackQuery):
    """Обработка отказа от ввода данных из ежедневного напоминания"""
    await callback.answer("Хорошо, напомню позже! 👌", show_alert=False)

    try:
        await callback.message.delete()
    except:
        pass


@router.callback_query(F.data == "health:export:cancel")
async def cancel_health_export_inline(callback: CallbackQuery, state: FSMContext):
    """Отмена процесса экспорта здоровья (inline кнопка)"""
    await state.clear()
    from bot.keyboards import get_export_type_keyboard

    await callback.message.edit_text(
        "📥 <b>Экспорт в PDF</b>\n\n"
        "Выберите, что вы хотите экспортировать:",
        parse_mode="HTML",
        reply_markup=get_export_type_keyboard()
    )
    await callback.answer("Экспорт отменен")


 