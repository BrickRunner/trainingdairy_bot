"""
Клавиатуры для модуля здоровья
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def get_health_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню раздела здоровья"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📝 Внести данные", callback_data="health:add_metrics")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="health:statistics")
    )
    builder.row(
        InlineKeyboardButton(text="📈 Графики", callback_data="health:graphs")
    )
    builder.row(
        InlineKeyboardButton(text="😴 Анализ сна", callback_data="health:sleep_analysis")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_menu")
    )
    return builder.as_markup()


def get_quick_input_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для быстрого ввода данных"""
    builder = InlineKeyboardBuilder()
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
    """Клавиатура выбора периода для статистики"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📅 Неделя", callback_data="health_stats:7")
    )
    builder.row(
        InlineKeyboardButton(text="📅 2 недели", callback_data="health_stats:14")
    )
    builder.row(
        InlineKeyboardButton(text="📅 Месяц", callback_data="health_stats:30")
    )
    builder.row(
        InlineKeyboardButton(text="📅 3 месяца", callback_data="health_stats:90")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="health:menu")
    )
    return builder.as_markup()


def get_graphs_period_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора периода для графиков"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📅 Неделя", callback_data="health_graphs:7")
    )
    builder.row(
        InlineKeyboardButton(text="📅 2 недели", callback_data="health_graphs:14")
    )
    builder.row(
        InlineKeyboardButton(text="📅 Месяц", callback_data="health_graphs:30")
    )
    builder.row(
        InlineKeyboardButton(text="📅 3 месяца", callback_data="health_graphs:90")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="health:menu")
    )
    return builder.as_markup()


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
