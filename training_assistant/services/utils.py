"""
Утилиты для AI сервисов Training Assistant
"""

import os
import logging
import aiosqlite
from typing import Dict

logger = logging.getLogger(__name__)
DB_PATH = os.getenv('DB_PATH', 'database.sqlite')


async def get_user_preferences(user_id: int) -> Dict[str, str]:
    """Получить настройки пользователя для форматирования"""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT distance_unit, weight_unit, date_format
                FROM user_settings
                WHERE user_id = ?
                """,
                (user_id,)
            )
            row = await cursor.fetchone()
            if row:
                return {
                    'distance_unit': row['distance_unit'] or 'км',
                    'weight_unit': row['weight_unit'] or 'кг',
                    'date_format': row['date_format'] or 'ДД.ММ.ГГГГ'
                }
    except Exception as e:
        logger.debug(f"Could not load user preferences: {e}")

    return {
        'distance_unit': 'км',
        'weight_unit': 'кг',
        'date_format': 'ДД.ММ.ГГГГ'
    }
