"""
Клавиатуры для раздела помощи
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_help_main_menu() -> InlineKeyboardMarkup:
    """Главное меню помощи"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="🚀 Начало работы", callback_data="help:start")
    )
    builder.row(
        InlineKeyboardButton(text="➕ Добавление тренировок", callback_data="help:trainings")
    )
    builder.row(
        InlineKeyboardButton(text="🏃 Соревнования", callback_data="help:competitions")
    )
    builder.row(
        InlineKeyboardButton(text="❤️ Здоровье", callback_data="help:health")
    )
    builder.row(
        InlineKeyboardButton(text="🏆 Рейтинги и достижения", callback_data="help:ratings")
    )
    builder.row(
        InlineKeyboardButton(text="👨‍🏫 Кабинет тренера", callback_data="help:coach")
    )
    builder.row(
        InlineKeyboardButton(text="📥 Экспорт в PDF", callback_data="help:export")
    )
    builder.row(
        InlineKeyboardButton(text="🤖 Training Assistant", callback_data="help:assistant")
    )
    builder.row(
        InlineKeyboardButton(text="❓ FAQ", callback_data="help:faq")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Закрыть", callback_data="help:close")
    )

    return builder.as_markup()


def get_trainings_help_menu() -> InlineKeyboardMarkup:
    """Меню помощи по тренировкам"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="🏃 Кросс", callback_data="help:training_run")
    )
    builder.row(
        InlineKeyboardButton(text="🏊 Плавание", callback_data="help:training_swim")
    )
    builder.row(
        InlineKeyboardButton(text="🚴 Велотренировка", callback_data="help:training_bike")
    )
    builder.row(
        InlineKeyboardButton(text="💪 Силовая", callback_data="help:training_strength")
    )
    builder.row(
        InlineKeyboardButton(text="⚡ Интервальная", callback_data="help:training_interval")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Просмотр тренировок", callback_data="help:view_trainings")
    )
    builder.row(
        InlineKeyboardButton(text="🗑 Удаление тренировок", callback_data="help:delete_training")
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="help:menu")
    )

    return builder.as_markup()


def get_coach_help_menu() -> InlineKeyboardMarkup:
    """Меню помощи по функциям тренера"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="🔗 Как стать тренером", callback_data="help:coach_become")
    )
    builder.row(
        InlineKeyboardButton(text="👥 Добавление учеников", callback_data="help:coach_students")
    )
    builder.row(
        InlineKeyboardButton(text="➕ Назначение тренировок", callback_data="help:coach_assign")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Просмотр статистики", callback_data="help:coach_stats")
    )
    builder.row(
        InlineKeyboardButton(text="💬 Комментарии", callback_data="help:coach_comments")
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="help:menu")
    )

    return builder.as_markup()


def get_faq_menu() -> InlineKeyboardMarkup:
    """Меню FAQ"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="📱 Как начать?", callback_data="help:faq_start")
    )
    builder.row(
        InlineKeyboardButton(text="⚙️ Как изменить настройки?", callback_data="help:faq_settings")
    )
    builder.row(
        InlineKeyboardButton(text="🔢 Единицы измерения", callback_data="help:faq_units")
    )
    builder.row(
        InlineKeyboardButton(text="📅 Формат даты", callback_data="help:faq_dates")
    )
    builder.row(
        InlineKeyboardButton(text="🔄 Как обновить тренировку?", callback_data="help:faq_edit")
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="help:menu")
    )

    return builder.as_markup()


def get_back_to_help_button() -> InlineKeyboardMarkup:
    """Кнопка возврата в главное меню помощи"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="« Назад в меню помощи", callback_data="help:menu")
    )
    return builder.as_markup()


def get_back_to_section_button(section: str) -> InlineKeyboardMarkup:
    """Кнопка возврата к разделу"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data=f"help:{section}")
    )
    builder.row(
        InlineKeyboardButton(text="🏠 Главное меню помощи", callback_data="help:menu")
    )
    return builder.as_markup()
