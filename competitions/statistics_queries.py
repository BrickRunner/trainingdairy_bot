"""
Функции для работы со статистикой соревнований
"""

import aiosqlite
import os
from typing import Optional, Dict, Any
from datetime import datetime
from utils.time_formatter import normalize_time

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')


async def get_user_competition_stats(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Получить статистику соревнований пользователя

    Args:
        user_id: ID пользователя

    Returns:
        Словарь со статистикой или None
    """

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute(
            "SELECT * FROM user_competition_stats WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()

            if row:
                return dict(row)

        await db.execute(
            """
            INSERT INTO user_competition_stats (user_id)
            VALUES (?)
            """,
            (user_id,)
        )
        await db.commit()

        return {
            'user_id': user_id,
            'total_competitions': 0,
            'total_completed': 0,
            'total_marathons': 0,
            'total_half_marathons': 0,
            'total_10k': 0,
            'total_5k': 0,
            'best_marathon_time': None,
            'best_half_marathon_time': None,
            'best_10k_time': None,
            'best_5k_time': None,
            'total_distance_km': 0
        }


async def update_user_competition_stats(user_id: int):
    """
    Обновить статистику соревнований пользователя на основе результатов

    Args:
        user_id: ID пользователя
    """

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute(
            """
            SELECT
                cp.distance,
                cp.finish_time,
                c.date
            FROM competition_participants cp
            JOIN competitions c ON cp.competition_id = c.id
            WHERE cp.participant_id = ?
              AND cp.finish_time IS NOT NULL
              AND c.date < date('now')
            """,
            (user_id,)
        ) as cursor:
            results = await cursor.fetchall()

        if not results:
            await db.execute(
                """
                UPDATE user_competition_stats
                SET total_competitions = 0,
                    total_completed = 0,
                    total_marathons = 0,
                    total_half_marathons = 0,
                    total_10k = 0,
                    total_5k = 0,
                    best_marathon_time = NULL,
                    best_half_marathon_time = NULL,
                    best_10k_time = NULL,
                    best_5k_time = NULL,
                    total_distance_km = 0,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (user_id,)
            )
            await db.commit()
            return

        total_completed = len(results)
        total_marathons = 0
        total_half_marathons = 0
        total_10k = 0
        total_5k = 0
        total_distance = 0

        best_marathon = None
        best_half_marathon = None
        best_10k = None
        best_5k = None

        for result in results:
            distance = result['distance']
            finish_time = result['finish_time']

            total_distance += distance

            if 42.0 <= distance <= 42.3:
                total_marathons += 1
                if finish_time:
                    normalized_time = normalize_time(finish_time)
                    if best_marathon is None or time_to_seconds(normalized_time) < time_to_seconds(best_marathon):
                        best_marathon = normalized_time

            elif 21.0 <= distance <= 21.2:
                total_half_marathons += 1
                if finish_time:
                    normalized_time = normalize_time(finish_time)
                    if best_half_marathon is None or time_to_seconds(normalized_time) < time_to_seconds(best_half_marathon):
                        best_half_marathon = normalized_time

            elif 9.5 <= distance <= 10.5:
                total_10k += 1
                if finish_time:
                    normalized_time = normalize_time(finish_time)
                    if best_10k is None or time_to_seconds(normalized_time) < time_to_seconds(best_10k):
                        best_10k = normalized_time

            elif 4.5 <= distance <= 5.5:
                total_5k += 1
                if finish_time:
                    normalized_time = normalize_time(finish_time)
                    if best_5k is None or time_to_seconds(normalized_time) < time_to_seconds(best_5k):
                        best_5k = normalized_time

        async with db.execute(
            """
            SELECT COUNT(*) as total
            FROM competition_participants
            WHERE participant_id = ?
            """,
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            total_competitions = row['total'] if row else 0

        await db.execute(
            """
            UPDATE user_competition_stats
            SET total_competitions = ?,
                total_completed = ?,
                total_marathons = ?,
                total_half_marathons = ?,
                total_10k = ?,
                total_5k = ?,
                best_marathon_time = ?,
                best_half_marathon_time = ?,
                best_10k_time = ?,
                best_5k_time = ?,
                total_distance_km = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """,
            (
                total_competitions,
                total_completed,
                total_marathons,
                total_half_marathons,
                total_10k,
                total_5k,
                best_marathon,
                best_half_marathon,
                best_10k,
                best_5k,
                round(total_distance, 2),
                user_id
            )
        )

        await db.commit()


def time_to_seconds(time_str: str) -> int:
    """
    Конвертировать время в формате HH:MM:SS в секунды

    Args:
        time_str: Время в формате HH:MM:SS

    Returns:
        Количество секунд
    """

    try:
        parts = time_str.split(':')
        if len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        else:
            return 0
    except (ValueError, AttributeError):
        return 0


async def add_result_and_update_stats(user_id: int, competition_id: int, result_data: Dict[str, Any]):
    """
    Добавить результат соревнования и обновить статистику

    Args:
        user_id: ID пользователя
        competition_id: ID соревнования
        result_data: Данные результата (finish_time, place_overall, etc.)
    """

    from competitions.competitions_queries import add_competition_result

    await add_competition_result(user_id, competition_id, result_data)

    await update_user_competition_stats(user_id)
