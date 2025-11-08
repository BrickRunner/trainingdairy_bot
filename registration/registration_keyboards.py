"""
Клавиатуры для процесса регистрации
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_gender_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора пола"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👨 Мужской", callback_data="reg_gender:male"),
        InlineKeyboardButton(text="👩 Женский", callback_data="reg_gender:female")
    )
    return builder.as_markup()


def get_training_types_keyboard(selected_types: list) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора основных типов тренировок

    Args:
        selected_types: Список уже выбранных типов тренировок
    """
    builder = InlineKeyboardBuilder()

    # Все доступные типы тренировок
    all_types = [
        ("🏃 Кросс", "кросс"),
        ("🏊 Плавание", "плавание"),
        ("🚴 Велотренировка", "велотренировка"),
        ("💪 Силовая", "силовая"),
        ("⚡ Интервальная", "интервальная")
    ]

    for display_name, type_value in all_types:
        # Добавляем галочку для выбранных типов
        text = f"✅ {display_name}" if type_value in selected_types else display_name
        builder.button(text=text, callback_data=f"reg_toggle_type:{type_value}")

    builder.adjust(2)  # По 2 кнопки в ряд

    # Кнопка подтверждения (активна только если выбран хотя бы один тип)
    if selected_types:
        builder.row(
            InlineKeyboardButton(text="✅ Продолжить", callback_data="reg_confirm_types")
        )

    return builder.as_markup()


def get_skip_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой пропуска"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⏭ Пропустить", callback_data="reg_skip")
    )
    return builder.as_markup()
