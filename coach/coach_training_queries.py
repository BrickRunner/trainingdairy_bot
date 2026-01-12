"""
Запросы для работы с тренировками учеников
"""

import aiosqlite
import logging
import os
from typing import Optional, List, Dict, Any
from datetime import datetime

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')
logger = logging.getLogger(__name__)


async def add_training_for_student(
    coach_id: int,
    student_id: int,
    training_data: Dict[str, Any]
) -> int:
    """
    Добавить тренировку для ученика от имени тренера

    Args:
        coach_id: ID тренера
        student_id: ID ученика
        training_data: Данные тренировки (type, date, duration, distance, etc.)

    Returns:
        ID созданной тренировки
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO trainings (
                user_id, type, date, time, duration, distance,
                avg_pace, pace_unit, avg_pulse, max_pulse,
                exercises, intervals, calculated_volume,
                description, results, comment, fatigue_level,
                added_by_coach_id, is_planned
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                student_id,
                training_data.get('type'),
                training_data.get('date'),
                training_data.get('time'),
                training_data.get('duration'),
                training_data.get('distance'),
                training_data.get('avg_pace'),
                training_data.get('pace_unit'),
                training_data.get('avg_pulse'),
                training_data.get('max_pulse'),
                training_data.get('exercises'),
                training_data.get('intervals'),
                training_data.get('calculated_volume'),
                training_data.get('description'),
                training_data.get('results'),
                training_data.get('comment'),
                training_data.get('fatigue_level'),
                coach_id,
                training_data.get('is_planned', 0)
            )
        )
        training_id = cursor.lastrowid
        await db.commit()

        logger.info(f"Coach {coach_id} added training {training_id} for student {student_id}")
        return training_id


async def get_student_trainings(
    student_id: int,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Получить тренировки ученика

    Args:
        student_id: ID ученика
        limit: Количество тренировок
        offset: Смещение

    Returns:
        Список тренировок
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT
                t.*,
                u.username as coach_username
            FROM trainings t
            LEFT JOIN users u ON u.id = t.added_by_coach_id
            WHERE t.user_id = ?
            ORDER BY t.date DESC, t.created_at DESC
            LIMIT ? OFFSET ?
            """,
            (student_id, limit, offset)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_student_trainings_by_period(
    student_id: int,
    period: str
) -> List[Dict[str, Any]]:
    """
    Получить тренировки ученика за указанный период

    Args:
        student_id: ID ученика
        period: Период:
            - 'week': от понедельника до воскресенья текущей недели
            - '2weeks': последние 14 дней до сегодня
            - 'month': с 1 до последнего числа текущего месяца
            - 'all': все тренировки

    Returns:
        Список тренировок
    """
    from datetime import datetime, timedelta
    import calendar

    today = datetime.now().date()

    if period == 'week':
        # Текущая календарная неделя: от понедельника до воскресенья
        start_date = today - timedelta(days=today.weekday())  # Понедельник
        end_date = start_date + timedelta(days=6)  # Воскресенье
    elif period == '2weeks':
        # Последние 14 дней до сегодня
        start_date = today - timedelta(days=13)
        end_date = today
    elif period == 'month':
        # Текущий календарный месяц: с 1 до последнего числа
        start_date = today.replace(day=1)
        # Последний день месяца
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_date = today.replace(day=last_day)
    else:  # all
        start_date = None
        end_date = None

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        if start_date:
            async with db.execute(
                """
                SELECT
                    t.*,
                    u.username as coach_username
                FROM trainings t
                LEFT JOIN users u ON u.id = t.added_by_coach_id
                WHERE t.user_id = ? AND t.date >= ? AND t.date <= ?
                ORDER BY t.date DESC, t.created_at DESC
                """,
                (student_id, start_date.isoformat(), end_date.isoformat())
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        else:
            async with db.execute(
                """
                SELECT
                    t.*,
                    u.username as coach_username
                FROM trainings t
                LEFT JOIN users u ON u.id = t.added_by_coach_id
                WHERE t.user_id = ?
                ORDER BY t.date DESC, t.created_at DESC
                LIMIT 100
                """,
                (student_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]


async def get_training_with_comments(training_id: int) -> Optional[Dict[str, Any]]:
    """
    Получить тренировку с комментариями

    Args:
        training_id: ID тренировки

    Returns:
        Тренировка с комментариями
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Получаем тренировку
        async with db.execute(
            """
            SELECT t.*, u.username as coach_username
            FROM trainings t
            LEFT JOIN users u ON u.id = t.added_by_coach_id
            WHERE t.id = ?
            """,
            (training_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            training = dict(row)

        # Получаем комментарии
        async with db.execute(
            """
            SELECT
                tc.*,
                u.username as author_username,
                s.name as author_name
            FROM training_comments tc
            JOIN users u ON u.id = tc.author_id
            LEFT JOIN user_settings s ON s.user_id = tc.author_id
            WHERE tc.training_id = ?
            ORDER BY tc.created_at ASC
            """,
            (training_id,)
        ) as cursor:
            comments = await cursor.fetchall()
            training['comments'] = [dict(c) for c in comments]

        return training


async def add_comment_to_training(
    training_id: int,
    author_id: int,
    comment: str
) -> int:
    """
    Добавить комментарий к тренировке

    Args:
        training_id: ID тренировки
        author_id: ID автора (тренер или ученик)
        comment: Текст комментария

    Returns:
        ID комментария
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO training_comments (training_id, author_id, comment)
            VALUES (?, ?, ?)
            """,
            (training_id, author_id, comment)
        )
        comment_id = cursor.lastrowid
        await db.commit()

        logger.info(f"User {author_id} added comment {comment_id} to training {training_id}")
        return comment_id


async def update_comment(
    comment_id: int,
    new_text: str
) -> bool:
    """
    Обновить комментарий

    Args:
        comment_id: ID комментария
        new_text: Новый текст

    Returns:
        True если успешно
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            UPDATE training_comments
            SET comment = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (new_text, comment_id)
        )
        await db.commit()
        return True


async def delete_comment(comment_id: int) -> bool:
    """
    Удалить комментарий

    Args:
        comment_id: ID комментария

    Returns:
        True если успешно
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM training_comments WHERE id = ?",
            (comment_id,)
        )
        await db.commit()
        return True


async def set_student_nickname(
    coach_id: int,
    student_id: int,
    nickname: str
) -> bool:
    """
    Установить псевдоним ученика (виден только тренеру)

    Args:
        coach_id: ID тренера
        student_id: ID ученика
        nickname: Псевдоним

    Returns:
        True если успешно
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            UPDATE coach_links
            SET coach_nickname = ?
            WHERE coach_id = ? AND student_id = ? AND status = 'active'
            """,
            (nickname, coach_id, student_id)
        )
        await db.commit()
        logger.info(f"Coach {coach_id} set nickname '{nickname}' for student {student_id}")
        return True


async def get_student_display_name(
    coach_id: int,
    student_id: int
) -> str:
    """
    Получить отображаемое имя ученика (псевдоним или реальное имя)

    Args:
        coach_id: ID тренера
        student_id: ID ученика

    Returns:
        Отображаемое имя
    """
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """
            SELECT
                cl.coach_nickname,
                s.name,
                u.username
            FROM coach_links cl
            LEFT JOIN user_settings s ON s.user_id = cl.student_id
            LEFT JOIN users u ON u.id = cl.student_id
            WHERE cl.coach_id = ? AND cl.student_id = ? AND cl.status = 'active'
            """,
            (coach_id, student_id)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return "Неизвестно"

            nickname, name, username = row

            # Приоритет: псевдоним > имя > username
            if nickname:
                return nickname
            elif name:
                return name
            else:
                return username or "Неизвестно"


async def can_coach_access_student(
    coach_id: int,
    student_id: int
) -> bool:
    """
    Проверить, имеет ли тренер доступ к ученику

    Args:
        coach_id: ID тренера
        student_id: ID ученика

    Returns:
        True если доступ есть
    """
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """
            SELECT COUNT(*) FROM coach_links
            WHERE coach_id = ? AND student_id = ? AND status = 'active'
            """,
            (coach_id, student_id)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] > 0 if row else False
