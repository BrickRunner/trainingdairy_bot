"""
Обработчики для модуля здоровья
"""

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, BufferedInputFile
from aiogram.fsm.context import FSMContext
from datetime import date
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
    get_skip_cancel_keyboard
)
from health.health_queries import (
    save_health_metrics,
    get_health_metrics_by_date,
    get_latest_health_metrics,
    get_health_statistics,
    check_today_metrics_filled
)
from health.health_graphs import generate_health_graphs, generate_sleep_quality_graph
from health.sleep_analysis import SleepAnalyzer, format_sleep_analysis_message

router = Router()
logger = logging.getLogger(__name__)


# ============== Главное меню здоровья ==============

@router.message(F.text == "❤️ Здоровье")
async def health_menu(message: Message, state: FSMContext):
    """Главное меню раздела здоровья"""
    await state.clear()
    user_id = message.from_user.id

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
    await state.clear()
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
    await callback.message.edit_text(
        "📝 <b>Внесение данных</b>\n\n"
        "Выберите, что хотите внести:",
        reply_markup=get_quick_input_keyboard(),
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
    await callback.message.answer(
        "😴 Введите <b>длительность сна</b> (часы):\n\n"
        "Например: 7.5 или 8",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(HealthMetricsStates.waiting_for_sleep_duration)
    await state.update_data(quick_input='sleep')
    await callback.answer()


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
    today = date.today()

    # Сохраняем в БД
    success = await save_health_metrics(
        user_id=user_id,
        metric_date=today,
        morning_pulse=data.get('pulse'),
        weight=data.get('weight'),
        sleep_duration=data.get('sleep_duration'),
        sleep_quality=data.get('sleep_quality')
    )

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

        # Возвращаем в меню здоровья
        await message.answer(
            "❤️ <b>Здоровье и метрики</b>\n\nВыберите действие:",
            reply_markup=get_health_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "❌ Ошибка при сохранении данных. Попробуйте позже.",
            reply_markup=ReplyKeyboardRemove()
        )

    await state.clear()


# ============== Статистика ==============

@router.callback_query(F.data == "health:statistics")
async def show_statistics_periods(callback: CallbackQuery):
    """Выбор периода для статистики"""
    await callback.message.edit_text(
        "📊 <b>Статистика здоровья</b>\n\n"
        "Выберите период:",
        reply_markup=get_stats_period_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("health_stats:"))
async def show_statistics(callback: CallbackQuery):
    """Показ статистики за период"""
    days = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    await callback.message.edit_text(
        "⏳ Загрузка статистики...",
        reply_markup=None
    )

    stats = await get_health_statistics(user_id, days)

    if not stats:
        await callback.message.edit_text(
            f"❌ Нет данных за последние {days} дней",
            reply_markup=get_stats_period_keyboard()
        )
        await callback.answer()
        return

    # Форматируем статистику
    msg = f"📊 <b>Статистика за {days} дней</b>\n\n"

    # Пульс
    if stats['pulse']['avg']:
        msg += f"💗 <b>Утренний пульс:</b>\n"
        msg += f"   Среднее: {stats['pulse']['avg']:.1f} уд/мин\n"
        msg += f"   Диапазон: {stats['pulse']['min']} - {stats['pulse']['max']}\n"
        trend = stats['pulse']['trend']
        trend_emoji = "📈" if trend == "increasing" else "📉" if trend == "decreasing" else "➡️"
        msg += f"   Тренд: {trend_emoji}\n\n"

    # Вес
    if stats['weight']['current']:
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
    if stats['sleep']['avg']:
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

    await callback.message.edit_text(
        msg,
        reply_markup=get_stats_period_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


# ============== Графики ==============

@router.callback_query(F.data == "health:graphs")
async def show_graphs_periods(callback: CallbackQuery):
    """Выбор периода для графиков"""
    await callback.message.edit_text(
        "📈 <b>Графики метрик</b>\n\n"
        "Выберите период:",
        reply_markup=get_graphs_period_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("health_graphs:"))
async def show_graphs(callback: CallbackQuery):
    """Показ графиков за период"""
    days = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    await callback.answer("⏳ Генерация графиков...", show_alert=True)

    metrics = await get_latest_health_metrics(user_id, days)

    if not metrics:
        await callback.message.answer(
            f"❌ Нет данных за последние {days} дней"
        )
        return

    try:
        # Генерируем графики
        graph_buffer = await generate_health_graphs(metrics, days)

        # Отправляем как фото
        photo = BufferedInputFile(graph_buffer.read(), filename=f"health_graphs_{days}d.png")
        await callback.message.answer_photo(
            photo=photo,
            caption=f"📈 Графики метрик здоровья за {days} дней"
        )

    except Exception as e:
        logger.error(f"Ошибка при генерации графиков: {e}")
        await callback.message.answer(
            "❌ Ошибка при генерации графиков"
        )


# ============== Анализ сна ==============

@router.callback_query(F.data == "health:sleep_analysis")
async def show_sleep_analysis(callback: CallbackQuery):
    """Глубокий анализ сна"""
    user_id = callback.from_user.id

    await callback.answer("⏳ Анализирую данные...", show_alert=True)

    # Получаем данные за 30 дней
    metrics = await get_latest_health_metrics(user_id, 30)

    if not metrics or len(metrics) < 3:
        await callback.message.answer(
            "❌ Недостаточно данных для анализа.\n\n"
            "Для полного анализа нужно минимум 3 дня с данными о сне."
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

    except Exception as e:
        logger.error(f"Ошибка при анализе сна: {e}")
        await callback.message.answer(
            "❌ Ошибка при анализе данных"
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
