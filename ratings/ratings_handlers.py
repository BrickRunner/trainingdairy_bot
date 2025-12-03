"""
Обработчики для раздела достижений и рейтингов
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import logging

from database.rating_queries import (
    get_user_rating,
    get_global_rankings,
    get_weekly_rankings,
    get_monthly_rankings,
    get_seasonal_rankings,
    get_user_rank
)
from database.level_queries import (
    get_user_level,
    get_user_training_stats_for_level
)
from ratings.rating_calculator import get_season_name
from ratings.user_levels import (
    get_level_emoji,
    get_level_info,
    get_next_level_info,
    get_all_levels_info
)
from ratings.ratings_keyboards import (
    get_achievements_menu_keyboard,
    get_periods_keyboard,
    get_back_to_achievements_keyboard,
    get_back_to_periods_keyboard
)
from bot.keyboards import get_main_menu_keyboard

logger = logging.getLogger(__name__)
router = Router()


def escape_markdown(text: str) -> str:
    """
    Экранировать специальные символы для Markdown

    Args:
        text: Текст для экранирования

    Returns:
        Экранированный текст
    """
    if not text:
        return text
    # Экранируем специальные символы Markdown
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


@router.message(F.text == "🏆 Достижения")
async def show_achievements_menu(message: Message):
    """Показать главное меню достижений"""
    from aiogram.types import ReplyKeyboardRemove

    await message.answer(
        "🏆 **Достижения и рейтинги**\n\n"
        "Здесь вы можете посмотреть свой рейтинг и сравнить результаты с другими пользователями.\n\n"
        "Рейтинг формируется на основе:\n"
        "• Типов тренировок (бег, плавание и т.д.)\n"
        "• Общего времени тренировок\n"
        "• Результатов соревнований",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )
    await message.answer(
        "Выберите действие:",
        reply_markup=get_achievements_menu_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "achievements:menu")
async def show_achievements_menu_callback(callback: CallbackQuery):
    """Показать главное меню достижений (через callback)"""
    await callback.message.edit_text(
        "🏆 **Достижения и рейтинги**\n\n"
        "Здесь вы можете посмотреть свой рейтинг и сравнить результаты с другими пользователями.\n\n"
        "Рейтинг формируется на основе:\n"
        "• Типов тренировок (бег, плавание и т.д.)\n"
        "• Общего времени тренировок\n"
        "• Результатов соревнований",
        reply_markup=get_achievements_menu_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "achievements:my_rating")
async def show_my_rating(callback: CallbackQuery):
    """Показать рейтинг и уровень пользователя"""
    user_id = callback.from_user.id

    # Получаем уровень пользователя
    user_level = await get_user_level(user_id) or 'новичок'
    level_emoji = get_level_emoji(user_level)
    level_data = get_level_info(user_level)

    # Получаем статистику тренировок
    stats = await get_user_training_stats_for_level(user_id)

    # Получаем информацию о следующем уровне
    next_level = get_next_level_info(user_level, stats['avg_per_week'])

    # Получаем рейтинг
    rating = await get_user_rating(user_id)

    text = f"{level_emoji} **Ваш уровень: {user_level.capitalize()}**\n\n"

    # Добавляем статистику по тренировкам
    if stats['total_trainings'] > 0:
        text += (
            f"📅 **Эта неделя:** {stats['current_week_trainings']} тренировок\n"
            f"💪 Всего тренировок: {stats['total_trainings']}\n"
        )

        # Информация о следующем уровне
        if next_level['has_next']:
            trainings_needed = int(next_level['trainings_needed'])
            if trainings_needed > 0:
                text += (
                    f"\n🎯 До уровня **{next_level['next_level']}** {next_level['next_level_emoji']}: "
                    f"еще {trainings_needed} тренировок на этой неделе\n"
                )
            else:
                text += f"\n🎉 Вы готовы к уровню **{next_level['next_level']}** {next_level['next_level_emoji']}!\n"
        else:
            text += "\n⭐ Максимальный уровень достигнут!\n"
    else:
        text += "Добавьте тренировки, чтобы повысить уровень!\n"

    # Рейтинговые очки
    text += "\n━━━━━━━━━━━━━━━━\n📊 **Рейтинг**\n\n"

    if not rating or rating['points'] == 0:
        text += "У вас пока нет рейтинговых очков.\n"
    else:
        # Получаем места в разных рейтингах
        global_rank = await get_user_rank(user_id, 'global')
        week_rank = await get_user_rank(user_id, 'week')
        month_rank = await get_user_rank(user_id, 'month')
        season_rank = await get_user_rank(user_id, 'season')

        season_name = get_season_name()
        text += f"🌍 **Глобальный:** {rating['points']:.1f} очков"

        if global_rank:
            text += f" (#{global_rank})"

        text += f"\n📅 **За неделю:** {rating['week_points']:.1f} очков"
        if week_rank:
            text += f" (#{week_rank})"

        text += f"\n📆 **За месяц:** {rating['month_points']:.1f} очков"
        if month_rank:
            text += f" (#{month_rank})"

        text += f"\n🌸 **За сезон ({season_name}):** {rating['season_points']:.1f} очков"
        if season_rank:
            text += f" (#{season_rank})"

    await callback.message.edit_text(
        text,
        reply_markup=get_back_to_achievements_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "achievements:top10")
async def show_top10(callback: CallbackQuery):
    """Показать топ-10 глобального рейтинга"""
    rankings = await get_global_rankings(limit=10)

    if not rankings:
        await callback.message.edit_text(
            "🏆 **Топ-10**\n\n"
            "Пока нет пользователей в рейтинге.",
            reply_markup=get_back_to_achievements_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
        return

    text = "🏆 **Топ-10 (Глобальный рейтинг)**\n\n"

    medals = ["🥇", "🥈", "🥉"]

    for i, user in enumerate(rankings, 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        name = user.get('name') or user.get('username') or 'Пользователь'
        name = escape_markdown(name)  # Экранируем имя
        points = user.get('points', 0)
        trainings = user.get('total_trainings', 0)

        text += f"{medal} **{name}** — {points:.1f} очков ({trainings} тренировок)\n"

    await callback.message.edit_text(
        text,
        reply_markup=get_back_to_achievements_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "achievements:periods")
async def show_periods_menu(callback: CallbackQuery):
    """Показать меню выбора периода"""
    await callback.message.edit_text(
        "📈 **Рейтинги по периодам**\n\n"
        "Выберите период для просмотра рейтинга:",
        reply_markup=get_periods_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("achievements:period:"))
async def show_period_ranking(callback: CallbackQuery):
    """Показать рейтинг за выбранный период"""
    period = callback.data.split(":")[-1]

    # Получаем рейтинг в зависимости от периода
    if period == "week":
        rankings = await get_weekly_rankings(limit=10)
        title = "📅 Рейтинг за неделю"
    elif period == "month":
        rankings = await get_monthly_rankings(limit=10)
        title = "📆 Рейтинг за месяц"
    elif period == "season":
        rankings = await get_seasonal_rankings(limit=10)
        season_name = get_season_name()
        title = f"🌸 Рейтинг за сезон ({season_name})"
    else:  # global
        rankings = await get_global_rankings(limit=10)
        title = "🌍 Глобальный рейтинг"

    if not rankings:
        await callback.message.edit_text(
            f"{title}\n\n"
            "Пока нет пользователей в рейтинге за этот период.",
            reply_markup=get_back_to_periods_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
        return

    text = f"{title}\n\n"
    medals = ["🥇", "🥈", "🥉"]

    for i, user in enumerate(rankings, 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        name = user.get('name') or user.get('username') or 'Пользователь'
        name = escape_markdown(name)  # Экранируем имя
        points = user.get('points', 0)

        text += f"{medal} **{name}** — {points:.1f} очков\n"

    await callback.message.edit_text(
        text,
        reply_markup=get_back_to_periods_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "achievements:back")
async def back_to_main(callback: CallbackQuery):
    """Вернуться в главное меню"""
    await callback.message.answer(
        "Главное меню:",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.message.delete()
    await callback.answer()
