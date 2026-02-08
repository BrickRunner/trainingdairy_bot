"""
Функции для работы с рейтингами в базе данных
"""

import aiosqlite
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')


async def update_user_rating(user_id: int, points: float, week_points: float,
                            month_points: float, season_points: float) -> None:
    """
    Обновить рейтинг пользователя

    Args:
        user_id: ID пользователя
        points: Общие очки (за всё время)
        week_points: Очки за неделю
        month_points: Очки за месяц
        season_points: Очки за сезон
    """
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT user_id FROM ratings WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            existing = await cursor.fetchone()

        if existing:
            await db.execute(
                """
                UPDATE ratings
                SET points = ?, week_points = ?, month_points = ?,
                    season_points = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (points, week_points, month_points, season_points, user_id)
            )
        else:
            await db.execute(
                """
                INSERT INTO ratings (user_id, points, week_points, month_points, season_points)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, points, week_points, month_points, season_points)
            )

        await db.commit()


async def get_user_rating(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Получить рейтинг пользователя

    Args:
        user_id: ID пользователя

    Returns:
        Словарь с данными рейтинга или None
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM ratings WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_global_rankings(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Получить глобальный рейтинг (топ пользователей по общим очкам)

    Args:
        limit: Количество пользователей в топе

    Returns:
        Список пользователей с рейтингом
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT
                r.user_id,
                r.points,
                r.week_points,
                r.month_points,
                r.season_points,
                u.username,
                us.name,
                COUNT(DISTINCT t.id) as total_trainings
            FROM ratings r
            LEFT JOIN users u ON r.user_id = u.id
            LEFT JOIN user_settings us ON r.user_id = us.user_id
            LEFT JOIN trainings t ON r.user_id = t.user_id
            GROUP BY r.user_id
            ORDER BY r.points DESC, total_trainings DESC
            LIMIT ?
            """,
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_weekly_rankings(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Получить рейтинг за неделю

    Args:
        limit: Количество пользователей в топе

    Returns:
        Список пользователей с рейтингом за неделю
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT
                r.user_id,
                r.week_points as points,
                u.username,
                us.name
            FROM ratings r
            LEFT JOIN users u ON r.user_id = u.id
            LEFT JOIN user_settings us ON r.user_id = us.user_id
            WHERE r.week_points > 0
            ORDER BY r.week_points DESC
            LIMIT ?
            """,
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_monthly_rankings(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Получить рейтинг за месяц

    Args:
        limit: Количество пользователей в топе

    Returns:
        Список пользователей с рейтингом за месяц
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT
                r.user_id,
                r.month_points as points,
                u.username,
                us.name
            FROM ratings r
            LEFT JOIN users u ON r.user_id = u.id
            LEFT JOIN user_settings us ON r.user_id = us.user_id
            WHERE r.month_points > 0
            ORDER BY r.month_points DESC
            LIMIT ?
            """,
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_seasonal_rankings(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Получить рейтинг за сезон

    Args:
        limit: Количество пользователей в топе

    Returns:
        Список пользователей с рейтингом за сезон
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT
                r.user_id,
                r.season_points as points,
                u.username,
                us.name
            FROM ratings r
            LEFT JOIN users u ON r.user_id = u.id
            LEFT JOIN user_settings us ON r.user_id = us.user_id
            WHERE r.season_points > 0
            ORDER BY r.season_points DESC
            LIMIT ?
            """,
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_user_rank(user_id: int, period: str = 'global') -> Optional[int]:
    """
    Получить место пользователя в рейтинге

    Args:
        user_id: ID пользователя
        period: Период ('global', 'week', 'month', 'season')

    Returns:
        Место в рейтинге или None
    """
    if period == 'week':
        points_field = 'week_points'
    elif period == 'month':
        points_field = 'month_points'
    elif period == 'season':
        points_field = 'season_points'
    else:  
        points_field = 'points'

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            f"SELECT {points_field} FROM ratings WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row or row[0] == 0:
                return None
            user_points = row[0]

        async with db.execute(
            f"""
            SELECT COUNT(*) + 1 as rank
            FROM ratings
            WHERE {points_field} > ?
            """,
            (user_points,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def get_all_users_for_rating_update() -> List[int]:
    """
    Получить список всех пользователей для обновления рейтинга

    Returns:
        Список ID пользователей
    """
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id FROM users") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]


async def get_user_trainings_by_period(user_id: int, start_date: datetime = None,
                                      end_date: datetime = None) -> List[Dict[str, Any]]:
    """
    Получить тренировки пользователя за период

    Args:
        user_id: ID пользователя
        start_date: Начальная дата (если None - все тренировки)
        end_date: Конечная дата

    Returns:
        Список тренировок
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        if start_date is None:
            # Все тренировки
            async with db.execute(
                """
                SELECT type, duration FROM trainings
                WHERE user_id = ?
                AND (is_planned = 0 OR duration IS NOT NULL)
                """,
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
        else:
            # За период
            async with db.execute(
                """
                SELECT type, duration
                FROM trainings
                WHERE user_id = ? AND date >= ? AND date <= ?
                AND (is_planned = 0 OR duration IS NOT NULL)
                """,
                (user_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
            ) as cursor:
                rows = await cursor.fetchall()

        return [dict(row) for row in rows]


async def get_user_competitions_by_period(user_id: int, start_date: datetime = None,
                                         end_date: datetime = None) -> List[Dict[str, Any]]:
    """
    Получить соревнования пользователя за период

    Args:
        user_id: ID пользователя
        start_date: Начальная дата (если None - все соревнования)
        end_date: Конечная дата

    Returns:
        Список соревнований с местами
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        if start_date is None:
            # Все соревнования
            async with db.execute(
                """
                SELECT cp.place_overall as place
                FROM competition_participants cp
                JOIN competitions c ON cp.competition_id = c.id
                WHERE cp.user_id = ? AND cp.place_overall IS NOT NULL
                """,
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
        else:
            # За период
            async with db.execute(
                """
                SELECT cp.place_overall as place
                FROM competition_participants cp
                JOIN competitions c ON cp.competition_id = c.id
                WHERE cp.user_id = ?
                AND cp.place_overall IS NOT NULL
                AND c.date >= ? AND c.date <= ?
                """,
                (user_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
            ) as cursor:
                rows = await cursor.fetchall()

        return [dict(row) for row in rows]


async def get_user_achievements_count(user_id: int) -> int:
    """
    Получить количество достижений пользователя

    Args:
        user_id: ID пользователя

    Returns:
        Количество достижений
    """
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) as cnt FROM achievements WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def get_user_achievement_points(user_id: int) -> int:
    """
    Получить общее количество баллов из достижений

    Args:
        user_id: ID пользователя

    Returns:
        Сумма баллов
    """
    from ratings.achievements_data import ACHIEVEMENTS

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT name FROM achievements WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            total = 0
            for row in rows:
                ach = ACHIEVEMENTS.get(row['name'])
                if ach:
                    total += ach.get('points', 0)
            return total
