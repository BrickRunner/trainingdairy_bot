"""
Клавиатуры для раздела достижений и рейтингов
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_achievements_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню раздела достижений"""
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text="📊 Мой рейтинг", callback_data="achievements:my_rating"))
    builder.row(InlineKeyboardButton(text="🎖️ Мои достижения", callback_data="achievements:my_achievements"))
    builder.row(InlineKeyboardButton(text="🏆 Топ-10", callback_data="achievements:top10"))
    builder.row(InlineKeyboardButton(text="👑 Лидеры по достижениям", callback_data="achievements:leaderboard"))
    builder.row(InlineKeyboardButton(text="📈 Рейтинги по периодам", callback_data="achievements:periods"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="achievements:back"))

    return builder.as_markup()


def get_periods_keyboard() -> InlineKeyboardMarkup:
    """Меню выбора периода для рейтинга"""
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text="📅 За неделю", callback_data="achievements:period:week"))
    builder.row(InlineKeyboardButton(text="📆 За месяц", callback_data="achievements:period:month"))
    builder.row(InlineKeyboardButton(text="🌸 За сезон", callback_data="achievements:period:season"))
    builder.row(InlineKeyboardButton(text="🌍 Глобальный", callback_data="achievements:period:global"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="achievements:menu"))

    return builder.as_markup()


def get_back_to_achievements_keyboard() -> InlineKeyboardMarkup:
    """Кнопка возврата в меню достижений"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="◀️ Назад к достижениям", callback_data="achievements:menu"))
    return builder.as_markup()


def get_back_to_periods_keyboard() -> InlineKeyboardMarkup:
    """Кнопка возврата к выбору периодов"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="◀️ Назад к периодам", callback_data="achievements:periods"))
    return builder.as_markup()


def get_achievements_categories_keyboard() -> InlineKeyboardMarkup:
    """Меню выбора категории достижений"""
    from ratings.achievements_data import ACHIEVEMENT_CATEGORIES

    builder = InlineKeyboardBuilder()

    categories = sorted(ACHIEVEMENT_CATEGORIES.items(), key=lambda x: x[1]['order'])

    for cat_id, cat_data in categories:
        builder.row(InlineKeyboardButton(
            text=f"{cat_data['emoji']} {cat_data['name']}",
            callback_data=f"achievements:category:{cat_id}"
        ))

    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="achievements:menu"))

    return builder.as_markup()


def get_back_to_achievements_categories_keyboard() -> InlineKeyboardMarkup:
    """Кнопка возврата к категориям достижений"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="◀️ К категориям", callback_data="achievements:my_achievements"))
    builder.row(InlineKeyboardButton(text="🏠 В меню", callback_data="achievements:menu"))
    return builder.as_markup()
