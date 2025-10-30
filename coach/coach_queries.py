"""
Запросы к базе данных для работы с тренерами и учениками
"""

import aiosqlite
import logging
import secrets
import string
from typing import Optional, List, Dict, Any
from database.queries import DB_PATH

logger = logging.getLogger(__name__)


def generate_link_code() -> str:
    """Сгенерировать уникальный код для подключения ученика"""
    # Генерируем 8-символьный код из букв и цифр
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
            # Проверяем есть ли уже код
            async with db.execute(
                "SELECT coach_link_code FROM user_settings WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()

                if row and row[0]:
                    link_code = row[0]
                else:
                    # Генерируем уникальный код
                    while True:
                        link_code = generate_link_code()
                        # Проверяем что код уникален
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
            # Выключаем режим тренера
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
        True если успешно, False если связь уже существует
    """
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                """
                INSERT INTO coach_links (coach_id, student_id, status)
                VALUES (?, ?, 'active')
                """,
                (coach_id, student_id)
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            # Связь уже существует
            return False


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
                cl.created_at
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
                    "name": row[2] or row[1],
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


async def remove_coach_from_student(student_id: int) -> bool:
    """Ученик отключается от тренера"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            UPDATE coach_links
            SET status = 'removed', removed_at = CURRENT_TIMESTAMP
            WHERE student_id = ? AND status = 'active'
            """,
            (student_id,)
        )
        await db.commit()
        return True
