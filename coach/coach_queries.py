"""
Запросы к базе данных для работы с тренерами и учениками
"""

import aiosqlite
import logging
import secrets
import string
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
import pytz
from database.queries import get_user_settings

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

logger = logging.getLogger(__name__)


def generate_link_code() -> str:
    """Сгенерировать уникальный код для подключения ученика"""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(8))


async def set_coach_mode(user_id: int, is_coach: bool) -> str:
    """
    Включить/выключить режим тренера для пользователя

    Args:
        user_id: ID пользователя
        is_coach: True - включить режим тренера, False - выключить

    Returns:
        Код для подключения учеников (если is_coach=True)
    """
    async with aiosqlite.connect(DB_PATH) as db:
        if is_coach:
            async with db.execute(
                "SELECT coach_link_code FROM user_settings WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()

                if row and row[0]:
                    link_code = row[0]
                    await db.execute(
                        """
                        UPDATE user_settings
                        SET is_coach = 1
                        WHERE user_id = ?
                        """,
                        (user_id,)
                    )
                else:
                    while True:
                        link_code = generate_link_code()
                        async with db.execute(
                            "SELECT user_id FROM user_settings WHERE coach_link_code = ?",
                            (link_code,)
                        ) as check_cursor:
                            if not await check_cursor.fetchone():
                                break

                    await db.execute(
                        """
                        UPDATE user_settings
                        SET is_coach = 1, coach_link_code = ?
                        WHERE user_id = ?
                        """,
                        (link_code, user_id)
                    )
        else:
            await db.execute(
                """
                UPDATE user_settings
                SET is_coach = 0
                WHERE user_id = ?
                """,
                (user_id,)
            )
            link_code = ""

        await db.commit()
        return link_code


async def is_user_coach(user_id: int) -> bool:
    """Проверить, является ли пользователь тренером"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT is_coach FROM user_settings WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return bool(row[0]) if row else False


async def get_coach_link_code(user_id: int) -> Optional[str]:
    """Получить код тренера для подключения учеников"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT coach_link_code FROM user_settings WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def find_coach_by_code(link_code: str) -> Optional[int]:
    """Найти тренера по коду"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """
            SELECT user_id FROM user_settings
            WHERE coach_link_code = ? AND is_coach = 1
            """,
            (link_code,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def add_student_to_coach(coach_id: int, student_id: int) -> bool:
    """
    Добавить ученика к тренеру

    Returns:
        True если успешно, False если активная связь уже существует или coach_id == student_id
    """
    if coach_id == student_id:
        logger.warning(f"User {coach_id} tried to add themselves as student")
        return False

    student_settings = await get_user_settings(student_id)
    student_timezone = student_settings.get('timezone', 'Europe/Moscow') if student_settings else 'Europe/Moscow'

    try:
        tz = pytz.timezone(student_timezone)
        local_time = datetime.now(tz)
        created_at_str = local_time.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        logger.error(f"Error getting timezone {student_timezone}: {e}")
        created_at_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT status FROM coach_links
            WHERE coach_id = ? AND student_id = ?
            """,
            (coach_id, student_id)
        )
        existing = await cursor.fetchone()

        if existing:
            status = existing[0]
            if status == 'active':
                return False
            else:
                await db.execute(
                    """
                    UPDATE coach_links
                    SET status = 'active', removed_at = NULL, created_at = ?, coach_nickname = NULL
                    WHERE coach_id = ? AND student_id = ?
                    """,
                    (created_at_str, coach_id, student_id)
                )
                await db.commit()
                return True
        else:
            await db.execute(
                """
                INSERT INTO coach_links (coach_id, student_id, status, created_at)
                VALUES (?, ?, 'active', ?)
                """,
                (coach_id, student_id, created_at_str)
            )
            await db.commit()
            return True


async def remove_student_from_coach(coach_id: int, student_id: int) -> bool:
    """Удалить ученика от тренера"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            UPDATE coach_links
            SET status = 'removed', removed_at = CURRENT_TIMESTAMP
            WHERE coach_id = ? AND student_id = ? AND status = 'active'
            """,
            (coach_id, student_id)
        )
        await db.commit()
        return True


async def get_coach_students(coach_id: int) -> List[Dict[str, Any]]:
    """Получить список учеников тренера"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """
            SELECT
                u.id,
                u.username,
                s.name,
                cl.created_at,
                cl.coach_nickname
            FROM coach_links cl
            JOIN users u ON u.id = cl.student_id
            LEFT JOIN user_settings s ON s.user_id = cl.student_id
            WHERE cl.coach_id = ? AND cl.status = 'active'
            ORDER BY cl.created_at DESC
            """,
            (coach_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "username": row[1],
                    "name": row[4] or row[2] or row[1],  
                    "connected_at": row[3]
                }
                for row in rows
            ]


async def get_student_coach(student_id: int) -> Optional[Dict[str, Any]]:
    """Получить тренера ученика"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """
            SELECT
                u.id,
                u.username,
                s.name
            FROM coach_links cl
            JOIN users u ON u.id = cl.coach_id
            LEFT JOIN user_settings s ON s.user_id = cl.coach_id
            WHERE cl.student_id = ? AND cl.status = 'active'
            LIMIT 1
            """,
            (student_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "username": row[1],
                    "name": row[2] or row[1]
                }
            return None


async def remove_coach_from_student(student_id: int) -> int:
    """
    Ученик отключается от тренера

    Returns:
        coach_id если успешно, None если тренер не найден
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT coach_id
            FROM coach_links
            WHERE student_id = ? AND status = 'active'
            """,
            (student_id,)
        )
        row = await cursor.fetchone()

        if not row:
            return None

        coach_id = row[0]

        await db.execute(
            """
            UPDATE coach_links
            SET status = 'removed', removed_at = CURRENT_TIMESTAMP
            WHERE student_id = ? AND status = 'active'
            """,
            (student_id,)
        )
        await db.commit()
        return coach_id
