"""
Фоновая задача для автоматического обновления рейтингов
"""

import asyncio
import logging
from datetime import datetime, time

from database.rating_queries import (
    get_all_users_for_rating_update,
    get_user_trainings_by_period,
    get_user_competitions_by_period,
    update_user_rating
)
from ratings.rating_calculator import (
    calculate_total_points,
    get_period_dates
)

logger = logging.getLogger(__name__)


async def update_single_user_rating(user_id: int) -> None:
    """
    Обновить рейтинг одного пользователя

    Args:
        user_id: ID пользователя
    """
    try:
        trainings_all = await get_user_trainings_by_period(user_id)
        competitions_all = await get_user_competitions_by_period(user_id)
        global_points = calculate_total_points(trainings_all, competitions_all)

        week_start, week_end = get_period_dates('week')
        trainings_week = await get_user_trainings_by_period(user_id, week_start, week_end)
        competitions_week = await get_user_competitions_by_period(user_id, week_start, week_end)
        week_points = calculate_total_points(trainings_week, competitions_week)

        month_start, month_end = get_period_dates('month')
        trainings_month = await get_user_trainings_by_period(user_id, month_start, month_end)
        competitions_month = await get_user_competitions_by_period(user_id, month_start, month_end)
        month_points = calculate_total_points(trainings_month, competitions_month)

        season_start, season_end = get_period_dates('season')
        trainings_season = await get_user_trainings_by_period(user_id, season_start, season_end)
        competitions_season = await get_user_competitions_by_period(user_id, season_start, season_end)
        season_points = calculate_total_points(trainings_season, competitions_season)

        await update_user_rating(
            user_id=user_id,
            points=global_points,
            week_points=week_points,
            month_points=month_points,
            season_points=season_points
        )

        logger.debug(
            f"Обновлен рейтинг пользователя {user_id}: "
            f"global={global_points}, week={week_points}, month={month_points}, season={season_points}"
        )

    except Exception as e:
        logger.error(f"Ошибка при обновлении рейтинга пользователя {user_id}: {e}")


async def update_all_ratings() -> None:
    """
    Обновить рейтинги всех пользователей
    """
    try:
        logger.info("Начинаем обновление рейтингов всех пользователей")

        users = await get_all_users_for_rating_update()

        if not users:
            logger.info("Нет пользователей для обновления рейтинга")
            return

        for user_id in users:
            await update_single_user_rating(user_id)

        logger.info(f"Обновлены рейтинги {len(users)} пользователей")

    except Exception as e:
        logger.error(f"Ошибка при обновлении рейтингов: {e}")


async def schedule_rating_updates() -> None:
    """
    Запланировать регулярное обновление рейтингов

    Обновление происходит каждый день в 03:00
    """
    logger.info("Запущен планировщик обновления рейтингов")

    while True:
        try:
            now = datetime.now()

            target_time = time(3, 0)

            from datetime import timedelta
            target_datetime = datetime.combine(now.date(), target_time)

            if now.time() >= target_time:
                target_datetime = datetime.combine(now.date() + timedelta(days=1), target_time)

            delay = (target_datetime - now).total_seconds()

            logger.info(f"Следующее обновление рейтингов в {target_datetime.strftime('%Y-%m-%d %H:%M:%S')}")

            await asyncio.sleep(delay)

            await update_all_ratings()

        except Exception as e:
            logger.error(f"Ошибка в планировщике обновления рейтингов: {e}")
            await asyncio.sleep(3600)
