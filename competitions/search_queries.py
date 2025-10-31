"""
Функции для поиска соревнований по городу и месяцу
"""

import aiosqlite
import os
from typing import List, Dict, Any
from datetime import datetime

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')


async def search_competitions_by_city_and_month(
    city: str,
    period: str
) -> List[Dict[str, Any]]:
    """
    Поиск соревнований по городу и месяцу

    Args:
        city: Название города
        period: Период в формате 'YYYY-MM' или 'all' для всех месяцев

    Returns:
        Список соревнований
    """

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        if period == 'all':
            # Поиск по всем месяцам (начиная с текущей даты)
            query = """
                SELECT * FROM competitions
                WHERE city = ?
                  AND date >= date('now')
                  AND status = 'upcoming'
                ORDER BY date ASC
                LIMIT 50
            """
            params = (city,)

        else:
            # Поиск по конкретному месяцу
            year, month = period.split('-')

            # Определяем начало и конец месяца
            start_date = f"{year}-{month}-01"

            # Конец месяца (последний день)
            if month == '12':
                end_date = f"{int(year) + 1}-01-01"
            else:
                end_date = f"{year}-{int(month) + 1:02d}-01"

            query = """
                SELECT * FROM competitions
                WHERE city = ?
                  AND date >= ?
                  AND date < ?
                  AND status = 'upcoming'
                ORDER BY date ASC
                LIMIT 50
            """
            params = (city, start_date, end_date)

        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def search_competitions_by_city(city: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Поиск всех соревнований по городу

    Args:
        city: Название города
        limit: Максимальное количество результатов

    Returns:
        Список соревнований
    """

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute(
            """
            SELECT * FROM competitions
            WHERE city = ?
              AND date >= date('now')
              AND status = 'upcoming'
            ORDER BY date ASC
            LIMIT ?
            """,
            (city, limit)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_available_cities() -> List[str]:
    """
    Получить список городов, для которых есть соревнования

    Returns:
        Список городов
    """

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """
            SELECT DISTINCT city
            FROM competitions
            WHERE city IS NOT NULL
              AND date >= date('now')
              AND status = 'upcoming'
            ORDER BY city
            """
        ) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]


async def get_competitions_count_by_city(city: str) -> int:
    """
    Получить количество соревнований в городе

    Args:
        city: Название города

    Returns:
        Количество соревнований
    """

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """
            SELECT COUNT(*) as count
            FROM competitions
            WHERE city = ?
              AND date >= date('now')
              AND status = 'upcoming'
            """,
            (city,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0
