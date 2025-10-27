"""
Функции для работы с уровнями пользователей в базе данных
"""

import aiosqlite
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

# Путь к базе данных
DB_PATH = os.getenv('DB_PATH', 'database.sqlite')


async def update_user_level(user_id: int, level: str, update_week: str = None) -> None:
    """
    Обновить уровень пользователя

    Args:
        user_id: ID пользователя
        level: Новый уровень
        update_week: Неделя обновления в формате YYYY-WW (если None, берется текущая)
    """
    if update_week is None:
        # Получаем текущую неделю в формате YYYY-WW
        from datetime import datetime
        today = datetime.now()
        # ISO неделя: год и номер недели
        year, week, _ = today.isocalendar()
        update_week = f"{year}-{week:02d}"

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET level = ?, level_updated_week = ? WHERE id = ?",
            (level, update_week, user_id)
        )
        await db.commit()


async def get_user_level(user_id: int) -> Optional[str]:
    """
    Получить текущий уровень пользователя

    Args:
        user_id: ID пользователя

    Returns:
        Уровень пользователя или None
    """
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT level FROM users WHERE id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def get_user_level_with_week(user_id: int) -> tuple[Optional[str], Optional[str]]:
    """
    Получить текущий уровень пользователя и неделю последнего обновления

    Args:
        user_id: ID пользователя

    Returns:
        Кортеж (уровень, неделя_обновления) или (None, None)
    """
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT level, level_updated_week FROM users WHERE id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return (row[0], row[1]) if row else (None, None)


async def get_user_training_stats_for_level(user_id: int) -> Dict[str, Any]:
    """
    Получить статистику тренировок пользователя для расчета уровня
    Расчет ведется по текущей календарной неделе (понедельник-воскресенье)

    Args:
        user_id: ID пользователя

    Returns:
        Словарь со статистикой
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Получаем текущую дату
        today = datetime.now().date()

        # Находим начало текущей недели (понедельник)
        week_start = today - timedelta(days=today.weekday())

        # Находим конец текущей недели (воскресенье)
        week_end = week_start + timedelta(days=6)

        # Получаем количество тренировок за текущую неделю
        async with db.execute(
            """
            SELECT COUNT(*) as current_week_trainings
            FROM trainings
            WHERE user_id = ?
            AND date >= ?
            AND date <= ?
            """,
            (user_id, week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d'))
        ) as cursor:
            row = await cursor.fetchone()
            current_week_trainings = row['current_week_trainings'] if row else 0

        # Получаем общую статистику (для отображения)
        async with db.execute(
            """
            SELECT MIN(date) as first_training_date,
                   MAX(date) as last_training_date,
                   COUNT(*) as total_trainings
            FROM trainings
            WHERE user_id = ?
            """,
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()

            if not row or not row['first_training_date']:
                return {
                    'total_trainings': 0,
                    'current_week_trainings': 0,
                    'avg_per_week': 0.0,
                    'first_training_date': None,
                    'last_training_date': None
                }

            first_date = datetime.strptime(row['first_training_date'], '%Y-%m-%d')
            last_date = datetime.strptime(row['last_training_date'], '%Y-%m-%d')
            total_trainings = row['total_trainings']

            return {
                'total_trainings': total_trainings,
                'current_week_trainings': current_week_trainings,
                'avg_per_week': float(current_week_trainings),  # Уровень = тренировки текущей недели
                'first_training_date': first_date,
                'last_training_date': last_date
            }


async def calculate_and_update_user_level(user_id: int) -> Dict[str, Any]:
    """
    Рассчитать и обновить уровень пользователя на основе его активности

    Логика:
    1. Уровень сохраняется 3 недели с момента последнего изменения
    2. Уровень может только ПОВЫСИТЬСЯ, если заработан новый на текущей неделе
    3. Уровень ПОНИЖАЕТСЯ только через 3 недели без тренировок

    Args:
        user_id: ID пользователя

    Returns:
        Словарь с информацией об обновлении уровня
    """
    from ratings.user_levels import (
        get_level_by_avg_trainings,
        get_level_emoji
    )

    # Получаем текущую неделю
    today = datetime.now()
    year, week, _ = today.isocalendar()
    current_week = f"{year}-{week:02d}"

    # Получаем текущий уровень и неделю последнего обновления
    current_level, level_updated_week = await get_user_level_with_week(user_id)
    if not current_level:
        current_level = 'новичок'
        level_updated_week = current_week

    # Получаем статистику тренировок
    stats = await get_user_training_stats_for_level(user_id)

    # Рассчитываем уровень на основе тренировок текущей недели
    earned_level = get_level_by_avg_trainings(stats['avg_per_week'])

    # Определяем список уровней для сравнения
    levels_order = ['новичок', 'любитель', 'профи', 'элитный']
    current_level_index = levels_order.index(current_level) if current_level in levels_order else 0
    earned_level_index = levels_order.index(earned_level) if earned_level in levels_order else 0

    # Вычисляем разницу недель с последнего обновления
    if level_updated_week:
        try:
            updated_year, updated_week = map(int, level_updated_week.split('-'))
            from datetime import date
            # Создаем даты для подсчета разницы недель
            updated_date = date.fromisocalendar(updated_year, updated_week, 1)
            current_date = date.fromisocalendar(year, week, 1)
            weeks_diff = (current_date - updated_date).days // 7
        except:
            weeks_diff = 0
    else:
        weeks_diff = 0

    new_level = current_level
    level_changed = False

    # Логика обновления уровня:
    # 1. Если заработан БОЛЕЕ ВЫСОКИЙ уровень - повышаем сразу
    if earned_level_index > current_level_index:
        new_level = earned_level
        level_changed = True

    # 2. Если прошло 3+ недель без тренировок - понижаем на один уровень
    elif weeks_diff >= 3 and stats['current_week_trainings'] == 0:
        if current_level_index > 0:
            new_level = levels_order[current_level_index - 1]
            level_changed = True

    # Обновляем уровень, если он изменился
    if level_changed:
        await update_user_level(user_id, new_level, current_week)

    return {
        'old_level': current_level,
        'new_level': new_level,
        'level_changed': level_changed,
        'level_emoji': get_level_emoji(new_level),
        'current_week_trainings': stats['current_week_trainings'],
        'total_trainings': stats['total_trainings'],
        'weeks_since_update': weeks_diff
    }
