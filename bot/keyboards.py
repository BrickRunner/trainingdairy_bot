"""
Клавиатуры и кнопки для интерфейса бота
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню бота"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="➕ Добавить тренировку"),
        KeyboardButton(text="📊 Статистика")
    )
    builder.row(
        KeyboardButton(text="📈 Графики"),
        KeyboardButton(text="🏆 Достижения")
    )
    builder.row(
        KeyboardButton(text="⚙️ Настройки"),
        KeyboardButton(text="ℹ️ Помощь")
    )
    return builder.as_markup(resize_keyboard=True)


def get_training_types_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа тренировки"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🏃 Кросс", callback_data="training_type:кросс")
    )
    # Позже добавим другие типы:
    # builder.row(
    #     InlineKeyboardButton(text="⚡ Интервальная", callback_data="training_type:интервальная")
    # )
    # builder.row(
    #     InlineKeyboardButton(text="💪 Силовая", callback_data="training_type:силовая")
    # )
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )
    return builder.as_markup()


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой отмены"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="❌ Отменить"))
    return builder.as_markup(resize_keyboard=True)


def get_skip_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопками пропуска и отмены"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="⏭️ Пропустить"),
        KeyboardButton(text="❌ Отменить")
    )
    return builder.as_markup(resize_keyboard=True)


def get_fatigue_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора уровня усталости"""
    builder = InlineKeyboardBuilder()
    for i in range(1, 11):
        builder.button(text=str(i), callback_data=f"fatigue:{i}")
    builder.adjust(5)  # 5 кнопок в ряду
    return builder.as_markup()
