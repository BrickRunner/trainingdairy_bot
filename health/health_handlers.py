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

from health.health_fsm import HealthMetricsStates
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

router = Router()
logger = logging.getLogger(__name__)


# ============== Вспомогательные функции ==============

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


# ============== Главное меню здоровья ==============

@router.message(F.text == "❤️ Здоровье")
async def health_menu(message: Message, state: FSMContext):
    """Главное меню раздела здоровья"""
    await state.clear()
    user_id = message.from_user.id

    logger.info(f"health_menu called for user_id = {user_id}")

    # Проверяем, какие метрики уже заполнены сегодня
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


@router.callback_query(F.data == "health:menu")
async def health_menu_callback(callback: CallbackQuery, state: FSMContext):
    """Возврат в меню здоровья"""
    # НЕ очищаем state - пусть пользователь продолжит добавлять метрики
    # await state.clear()

    # Очищаем только состояние FSM, но оставляем данные
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


# ============== Ввод метрик ==============

@router.callback_query(F.data == "health:add_metrics")
async def choose_input_type(callback: CallbackQuery):
    """Выбор типа ввода метрик"""
    user_id = callback.from_user.id

    # Получаем метрики на сегодня
    from datetime import date
    today = date.today()
    today_metrics = await get_health_metrics_by_date(user_id, today)

    # Формируем текст сообщения
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
    await callback.message.delete()
    await state.set_state(HealthMetricsStates.waiting_for_pulse)
    await callback.answer()


@router.callback_query(F.data == "health:input_pulse")
async def start_pulse_input(callback: CallbackQuery, state: FSMContext):
    """Ввод только пульса"""
    # НЕ очищаем state - чтобы сохранить другие метрики!
    await callback.message.answer(
        "💗 Введите ваш <b>утренний пульс</b> (уд/мин):\n\n"
        "Например: 60",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.message.delete()
    await state.set_state(HealthMetricsStates.waiting_for_pulse)
    await state.update_data(quick_input='pulse')
    await callback.answer()


@router.callback_query(F.data == "health:input_weight")
async def start_weight_input(callback: CallbackQuery, state: FSMContext):
    """Ввод только веса"""
    # НЕ очищаем state - чтобы сохранить другие метрики!
    await callback.message.answer(
        "⚖️ Введите ваш <b>вес</b> (кг):\n\n"
        "Например: 75.5",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(HealthMetricsStates.waiting_for_weight)
    await state.update_data(quick_input='weight')
    await callback.answer()


@router.callback_query(F.data == "health:input_sleep")
async def start_sleep_input(callback: CallbackQuery, state: FSMContext):
    """Ввод только сна"""
    # НЕ очищаем state - чтобы сохранить другие метрики!
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
    await callback.message.answer(
        "📅 <b>За какую дату вы хотите внести данные?</b>",
        reply_markup=get_date_choice_keyboard(),
        parse_mode="HTML"
    )
    await callback.message.delete()
    await state.set_state(HealthMetricsStates.waiting_for_date_choice)
    await callback.answer()


@router.message(HealthMetricsStates.waiting_for_date_choice)
async def process_date_choice(message: Message, state: FSMContext):
    """Обработка выбора даты"""
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
    elif message.text == "📝 Ввести дату":
        await message.answer(
            "📅 Введите дату в формате ДД.ММ.ГГГГ\n\n"
            "Например: 20.10.2025",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(HealthMetricsStates.waiting_for_custom_date)
        return
    else:
        await message.answer(
            "❌ Неверный выбор. Используйте кнопки."
        )
        return

    # Сохраняем выбранную дату и показываем меню ввода
    await state.update_data(selected_date=selected_date)

    user_id = message.from_user.id
    metrics = await get_health_metrics_by_date(user_id, selected_date)

    date_str = selected_date.strftime("%d.%m.%Y")

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

    # Парсим дату
    match = re.match(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', message.text)
    if not match:
        await message.answer(
            "❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ\n\n"
            "Например: 20.10.2025"
        )
        return

    day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))

    try:
        selected_date = date(year, month, day)
    except ValueError:
        await message.answer(
            "❌ Некорректная дата. Проверьте правильность ввода."
        )
        return

    # Проверяем что дата не в будущем
    if selected_date > date.today():
        await message.answer(
            "❌ Нельзя вносить данные за будущую дату."
        )
        return

    # Сохраняем выбранную дату и показываем меню ввода
    await state.update_data(selected_date=selected_date)

    user_id = message.from_user.id
    metrics = await get_health_metrics_by_date(user_id, selected_date)

    date_str = selected_date.strftime("%d.%m.%Y")

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


# ============== Обработка ввода метрик ==============

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

    # Валидация
    try:
        pulse = int(message.text)
        if not (30 <= pulse <= 200):
            await message.answer("❌ Пульс должен быть в диапазоне 30-200 уд/мин")
            return
    except ValueError:
        await message.answer("❌ Введите число")
        return

    await state.update_data(pulse=pulse)

    # Проверяем режим ввода
    data = await state.get_data()
    if data.get('quick_input') == 'pulse':
        # Быстрый ввод - сохраняем только пульс
        await save_and_finish(message, state, morning_pulse=pulse)
    else:
        # Полный ввод - переходим к весу
        await ask_weight(message, state)


async def ask_weight(message: Message, state: FSMContext):
    """Запрос веса"""
    await message.answer(
        "⚖️ Введите ваш <b>вес</b> (кг):\n\n"
        "Например: 75.5",
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

    # Валидация
    try:
        weight = float(message.text.replace(',', '.'))
        if not (30 <= weight <= 300):
            await message.answer("❌ Вес должен быть в диапазоне 30-300 кг")
            return
    except ValueError:
        await message.answer("❌ Введите число")
        return

    await state.update_data(weight=weight)

    # Проверяем режим ввода
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

    # Валидация и парсинг
    try:
        text = message.text.strip()

        # Проверяем формат ЧЧ:ММ
        if ':' in text:
            parts = text.split(':')
            if len(parts) != 2:
                await message.answer("❌ Неверный формат. Используйте ЧЧ:ММ (например: 7:30)")
                return

            hours = int(parts[0])
            minutes = int(parts[1])

            if not (0 <= hours <= 20):
                await message.answer("❌ Часы должны быть в диапазоне 0-20")
                return

            if not (0 <= minutes < 60):
                await message.answer("❌ Минуты должны быть в диапазоне 0-59")
                return

            # Конвертируем в десятичное число часов
            sleep_duration = hours + (minutes / 60.0)
        else:
            # Обычный формат - просто число
            sleep_duration = float(text.replace(',', '.'))

        if not (1 <= sleep_duration <= 20):
            await message.answer("❌ Длительность сна должна быть в диапазоне 1-20 часов")
            return

    except ValueError:
        await message.answer("❌ Неверный формат. Примеры: 7:30 или 7.5 или 8")
        return

    await state.update_data(sleep_duration=sleep_duration)

    # Проверяем режим ввода
    data = await state.get_data()
    if data.get('quick_input') == 'sleep':
        # После сна в быстром режиме спрашиваем качество
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

    # Сохраняем данные
    await save_and_finish(callback.message, state)
    await callback.answer()


async def save_and_finish(message: Message, state: FSMContext, **extra_data):
    """Сохранение данных и завершение"""
    data = await state.get_data()
    data.update(extra_data)

    user_id = message.from_user.id if hasattr(message, 'from_user') else message.chat.id

    # Используем выбранную дату из state, или сегодня по умолчанию
    metric_date = data.get('selected_date', date.today())

    # ОТЛАДКА: Логируем что в state
    logger.info(f"save_and_finish: data from state = {data}")
    logger.info(f"save_and_finish: extra_data = {extra_data}")
    logger.info(f"save_and_finish: metric_date = {metric_date}")

    # Подготавливаем параметры для сохранения - передаем только заполненные значения
    save_params = {
        'user_id': user_id,
        'metric_date': metric_date
    }

    # Добавляем только те параметры, которые были введены (не None)
    if 'pulse' in data and data['pulse'] is not None:
        save_params['morning_pulse'] = data['pulse']
    if 'weight' in data and data['weight'] is not None:
        save_params['weight'] = data['weight']
    if 'sleep_duration' in data and data['sleep_duration'] is not None:
        save_params['sleep_duration'] = data['sleep_duration']
    if 'sleep_quality' in data and data['sleep_quality'] is not None:
        save_params['sleep_quality'] = data['sleep_quality']

    # ОТЛАДКА: Логируем что передаем в БД
    logger.info(f"save_and_finish: save_params = {save_params}")

    # Сохраняем в БД
    success = await save_health_metrics(**save_params)

    if success:
        # Формируем сообщение о сохраненных данных
        saved_items = []
        if data.get('pulse'):
            saved_items.append(f"💗 Пульс: {data['pulse']} уд/мин")
        if data.get('weight'):
            saved_items.append(f"⚖️ Вес: {data['weight']} кг")
        if data.get('sleep_duration'):
            # Форматируем длительность сна
            duration = data['sleep_duration']
            hours = int(duration)
            minutes = int((duration - hours) * 60)
            if minutes > 0:
                saved_items.append(f"😴 Сон: {hours} ч {minutes} мин")
            else:
                saved_items.append(f"😴 Сон: {hours} ч")
        if data.get('sleep_quality'):
            saved_items.append(f"⭐ Качество: {data['sleep_quality']}/5")

        # Показываем статус на сегодня
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

        # Получаем обновленные метрики и возвращаем в меню ввода данных
        updated_metrics = await get_health_metrics_by_date(user_id, metric_date)

        # Форматируем дату для отображения
        date_str = metric_date.strftime("%d.%m.%Y")
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

    # НЕ очищаем state - чтобы пользователь мог добавлять другие метрики
    # State будет очищен только когда пользователь выйдет из раздела здоровья
    # await state.clear()


# ============== Статистика и графики ==============

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

    await callback.answer("⏳ Загрузка данных...", show_alert=True)

    # Определяем период и название
    if period_param == "week":
        metrics = await get_current_week_metrics(user_id)
        period_name = "эту неделю"
    elif period_param == "month":
        metrics = await get_current_month_metrics(user_id)
        period_name = "этот месяц"
    else:
        # Для числовых значений - последние N дней
        days = int(period_param)
        metrics = await get_latest_health_metrics(user_id, days)
        period_name = f"{days} дней"

    # Вычисляем статистику на основе полученных метрик
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
        # Возвращаемся в главное меню здоровья
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

    # Форматируем статистику
    msg = f"📊 <b>Статистика за {period_name}</b>\n\n"

    # Пульс
    if stats and stats['pulse']['avg']:
        msg += f"💗 <b>Утренний пульс:</b>\n"
        msg += f"   Среднее: {stats['pulse']['avg']:.1f} уд/мин\n"
        msg += f"   Диапазон: {stats['pulse']['min']} - {stats['pulse']['max']}\n"
        trend = stats['pulse']['trend']
        trend_emoji = "📈" if trend == "increasing" else "📉" if trend == "decreasing" else "➡️"
        msg += f"   Тренд: {trend_emoji}\n\n"

    # Вес
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

    # Сон
    if stats and stats['sleep']['avg']:
        # Форматируем среднюю длительность
        avg_hours = int(stats['sleep']['avg'])
        avg_minutes = int((stats['sleep']['avg'] - avg_hours) * 60)
        avg_text = f"{avg_hours} ч {avg_minutes} мин" if avg_minutes > 0 else f"{avg_hours} ч"

        # Форматируем минимум
        min_hours = int(stats['sleep']['min'])
        min_minutes = int((stats['sleep']['min'] - min_hours) * 60)
        min_text = f"{min_hours}:{min_minutes:02d}" if min_minutes > 0 else f"{min_hours}:00"

        # Форматируем максимум
        max_hours = int(stats['sleep']['max'])
        max_minutes = int((stats['sleep']['max'] - max_hours) * 60)
        max_text = f"{max_hours}:{max_minutes:02d}" if max_minutes > 0 else f"{max_hours}:00"

        msg += f"😴 <b>Сон:</b>\n"
        msg += f"   Среднее: {avg_text}\n"
        msg += f"   Диапазон: {min_text} - {max_text}\n"

        # Оценка качества сна
        avg_sleep = stats['sleep']['avg']
        if 7 <= avg_sleep <= 9:
            msg += f"   Оценка: ✅ В норме\n"
        elif avg_sleep < 7:
            msg += f"   Оценка: ⚠️ Недостаточно\n"
        else:
            msg += f"   Оценка: ⚠️ Избыточно\n"

    # Отправляем статистику
    await callback.message.answer(msg, parse_mode="HTML")

    # Генерируем и отправляем графики
    if metrics:
        try:
            # Для генерации графика передаём количество дней (используем len(metrics) как приблизительное значение)
            days_for_graph = len(metrics) if len(metrics) > 0 else 7
            graph_buffer = await generate_health_graphs(metrics, days_for_graph)
            photo = BufferedInputFile(graph_buffer.read(), filename=f"health_stats.png")
            await callback.message.answer_photo(
                photo=photo,
                caption=f"📈 Графики метрик здоровья за {period_name}"
            )
        except Exception as e:
            logger.error(f"Ошибка при генерации графиков: {e}")
            await callback.message.answer("❌ Ошибка при генерации графиков")

    # Возвращаем пользователя в главное меню здоровья
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


# Оставляем старые обработчики для обратной совместимости
@router.callback_query(F.data == "health:statistics")
async def show_statistics_periods(callback: CallbackQuery):
    """Выбор периода для статистики (перенаправление на новый обработчик)"""
    await show_stats_graphs_periods(callback)


@router.callback_query(F.data == "health:graphs")
async def show_graphs_periods(callback: CallbackQuery):
    """Выбор периода для графиков (перенаправление на новый обработчик)"""
    await show_stats_graphs_periods(callback)


# ============== Анализ сна ==============

@router.callback_query(F.data == "health:sleep_analysis")
async def show_sleep_analysis(callback: CallbackQuery):
    """Глубокий анализ сна"""
    user_id = callback.from_user.id

    await callback.answer("⏳ Анализирую данные...", show_alert=True)

    # Получаем данные за 30 дней
    metrics = await get_latest_health_metrics(user_id, 30)

    if not metrics or len(metrics) < 3:
        # Возвращаемся в главное меню здоровья
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
        # Выполняем анализ
        analyzer = SleepAnalyzer(metrics)
        analysis = analyzer.get_full_analysis()

        # Форматируем сообщение
        message_text = format_sleep_analysis_message(analysis)

        await callback.message.answer(
            message_text,
            parse_mode="HTML"
        )

        # Генерируем график сна
        graph_buffer = await generate_sleep_quality_graph(metrics, 30)
        photo = BufferedInputFile(graph_buffer.read(), filename="sleep_analysis.png")
        await callback.message.answer_photo(
            photo=photo,
            caption="📊 График анализа сна"
        )

        # Возвращаем пользователя в главное меню здоровья
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

        # Возвращаемся в главное меню здоровья даже при ошибке
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


# ============== Отмена ==============

@router.message(F.text == "❌ Отменить", StateFilter("*"))
async def cancel_handler(message: Message, state: FSMContext):
    """Отмена текущего действия"""
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer(
        "Действие отменено.",
        reply_markup=ReplyKeyboardRemove()
    )
    await return_to_health_menu(message)
