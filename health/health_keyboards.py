"""
Клавиатуры для модуля здоровья
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from typing import Optional, Dict


def get_health_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню раздела здоровья"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📝 Внести данные", callback_data="health:add_metrics")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Статистика и графики", callback_data="health:stats_and_graphs")
    )
    builder.row(
        InlineKeyboardButton(text="😴 Анализ сна", callback_data="health:sleep_analysis")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_menu")
    )
    return builder.as_markup()


def get_quick_input_keyboard(today_metrics: Optional[Dict] = None) -> InlineKeyboardMarkup:
    """
    Клавиатура для быстрого ввода данных

    Если today_metrics заполнены, показывает текущие значения с кнопками для изменения
    Если нет - показывает кнопки для первичного ввода
    """
    builder = InlineKeyboardBuilder()

    # Если есть метрики сегодня, показываем текущие значения
    if today_metrics:
        # Пульс
        if today_metrics.get('morning_pulse'):
            builder.row(
                InlineKeyboardButton(
                    text=f"💗 Пульс: {today_metrics['morning_pulse']} уд/мин",
                    callback_data="health:input_pulse"
                )
            )
        else:
            builder.row(
                InlineKeyboardButton(text="💗 Добавить пульс", callback_data="health:input_pulse")
            )

        # Вес
        if today_metrics.get('weight'):
            builder.row(
                InlineKeyboardButton(
                    text=f"⚖️ Вес: {today_metrics['weight']} кг",
                    callback_data="health:input_weight"
                )
            )
        else:
            builder.row(
                InlineKeyboardButton(text="⚖️ Добавить вес", callback_data="health:input_weight")
            )

        # Сон
        if today_metrics.get('sleep_duration'):
            duration = today_metrics['sleep_duration']
            hours = int(duration)
            minutes = int((duration - hours) * 60)
            sleep_text = f"{hours}ч {minutes}м" if minutes > 0 else f"{hours}ч"

            builder.row(
                InlineKeyboardButton(
                    text=f"😴 Сон: {sleep_text}",
                    callback_data="health:input_sleep"
                )
            )
        else:
            builder.row(
                InlineKeyboardButton(text="😴 Добавить сон", callback_data="health:input_sleep")
            )
    else:
        # Нет данных - показываем стандартные кнопки для ввода
        builder.row(
            InlineKeyboardButton(text="✏️ Ввести всё", callback_data="health:input_all")
        )
        builder.row(
            InlineKeyboardButton(text="💗 Только пульс", callback_data="health:input_pulse")
        )
        builder.row(
            InlineKeyboardButton(text="⚖️ Только вес", callback_data="health:input_weight")
        )
        builder.row(
            InlineKeyboardButton(text="😴 Только сон", callback_data="health:input_sleep")
        )

    # Кнопка для ввода данных за другую дату
    builder.row(
        InlineKeyboardButton(text="📅 Ввести за другую дату", callback_data="health:choose_date")
    )

    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="health:menu")
    )
    return builder.as_markup()


def get_sleep_quality_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для оценки качества сна"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="😴 1 - Очень плохо", callback_data="sleep_quality:1")
    )
    builder.row(
        InlineKeyboardButton(text="😕 2 - Плохо", callback_data="sleep_quality:2")
    )
    builder.row(
        InlineKeyboardButton(text="😐 3 - Нормально", callback_data="sleep_quality:3")
    )
    builder.row(
        InlineKeyboardButton(text="🙂 4 - Хорошо", callback_data="sleep_quality:4")
    )
    builder.row(
        InlineKeyboardButton(text="😊 5 - Отлично", callback_data="sleep_quality:5")
    )
    builder.row(
        InlineKeyboardButton(text="⏭️ Пропустить", callback_data="sleep_quality:skip")
    )
    return builder.as_markup()


def get_stats_period_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора периода для статистики и графиков"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📅 Эта неделя", callback_data="health_stats_graphs:week")
    )
    builder.row(
        InlineKeyboardButton(text="📅 Этот месяц", callback_data="health_stats_graphs:month")
    )
    builder.row(
        InlineKeyboardButton(text="📅 Последние 14 дней", callback_data="health_stats_graphs:14")
    )
    builder.row(
        InlineKeyboardButton(text="📅 Последние 30 дней", callback_data="health_stats_graphs:30")
    )
    builder.row(
        InlineKeyboardButton(text="📅 Последние 90 дней", callback_data="health_stats_graphs:90")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="health:menu")
    )
    return builder.as_markup()


def get_graphs_period_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора периода для графиков (устаревшая, используйте get_stats_period_keyboard)"""
    return get_stats_period_keyboard()


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой отмены"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="❌ Отменить"))
    return builder.as_markup(resize_keyboard=True)


def get_skip_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопками пропуска и отмены"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="⏭️ Пропустить"),
        KeyboardButton(text="❌ Отменить")
    )
    return builder.as_markup(resize_keyboard=True)


def get_date_choice_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для выбора даты внесения данных"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📅 Сегодня"),
        KeyboardButton(text="📅 Вчера")
    )
    builder.row(
        KeyboardButton(text="📅 Позавчера"),
        KeyboardButton(text="📝 Ввести дату")
    )
    builder.row(
        KeyboardButton(text="❌ Отменить")
    )
    return builder.as_markup(resize_keyboard=True)
