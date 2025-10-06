"""
Функции для работы с базой данных (CRUD операции)
"""

import aiosqlite
import os
from datetime import datetime
from typing import Optional, Dict, Any

from database.models import ALL_TABLES

# Путь к базе данных
DB_PATH = os.getenv('DB_PATH', 'database.sqlite')


async def init_db():
    """Инициализация базы данных (создание таблиц)"""
    async with aiosqlite.connect(DB_PATH) as db:
        for table_sql in ALL_TABLES:
            await db.execute(table_sql)
        await db.commit()


async def add_user(user_id: int, username: str) -> None:
    """
    Добавить пользователя в базу данных
    
    Args:
        user_id: Telegram ID пользователя
        username: Имя пользователя
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO users (id, username)
            VALUES (?, ?)
            """,
            (user_id, username)
        )
        await db.commit()


async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Получить данные пользователя
    
    Args:
        user_id: Telegram ID пользователя
        
    Returns:
        Словарь с данными пользователя или None
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None


async def add_training(data: Dict[str, Any]) -> None:
    """
    Добавить тренировку в базу данных
    
    Args:
        data: Словарь с данными тренировки
              Обязательные поля: user_id, type, date, time, duration
              Опциональные: distance, avg_pace, pace_unit, avg_pulse, max_pulse, exercises, intervals, calculated_volume, description, results, comment, fatigue_level
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO trainings 
            (user_id, type, date, time, duration, distance, avg_pace, pace_unit, avg_pulse, max_pulse, exercises, intervals, calculated_volume, description, results, comment, fatigue_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data['user_id'],
                data['training_type'],
                data['date'],
                data.get('time'),
                data['duration'],
                data.get('distance'),
                data.get('avg_pace'),
                data.get('pace_unit'),
                data.get('avg_pulse'),
                data.get('max_pulse'),
                data.get('exercises'),
                data.get('intervals'),
                data.get('calculated_volume'),
                data.get('description'),
                data.get('results'),
                data.get('comment'),
                data.get('fatigue_level')
            )
        )
        await db.commit()


async def get_user_trainings(user_id: int, limit: int = 10) -> list:
    """
    Получить тренировки пользователя
    
    Args:
        user_id: Telegram ID пользователя
        limit: Максимальное количество тренировок
        
    Returns:
        Список словарей с данными тренировок
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT * FROM trainings 
            WHERE user_id = ? 
            ORDER BY date DESC, created_at DESC
            LIMIT ?
            """,
            (user_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_training_count(user_id: int) -> int:
    """
    Получить количество тренировок пользователя
    
    Args:
        user_id: Telegram ID пользователя
        
    Returns:
        Количество тренировок
    """
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM trainings WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def update_user_level(user_id: int, level: str) -> None:
    """
    Обновить уровень пользователя
    
    Args:
        user_id: Telegram ID пользователя
        level: Новый уровень
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET level = ? WHERE id = ?",
            (level, user_id)
        )
        await db.commit()


async def delete_training(training_id: int, user_id: int) -> bool:
    """
    Удалить тренировку
    
    Args:
        training_id: ID тренировки
        user_id: ID пользователя (для проверки прав)
        
    Returns:
        True если тренировка удалена, False если не найдена или нет прав
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM trainings WHERE id = ? AND user_id = ?",
            (training_id, user_id)
        )
        await db.commit()
        return cursor.rowcount > 0


async def get_trainings_by_period(user_id: int, days: int) -> list:
    """
    Получить тренировки пользователя за определенный период
    
    Args:
        user_id: ID пользователя
        days: Количество дней (7 - неделя, 14 - 2 недели, 30 - месяц)
        
    Returns:
        Список тренировок за период (отсортированных по дате тренировки, от старых к новым)
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT * FROM trainings 
            WHERE user_id = ? 
            AND date >= date('now', ? || ' days')
            ORDER BY date ASC
            """,
            (user_id, f'-{days}')
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_training_statistics(user_id: int, days: int) -> Dict[str, Any]:
    """
    Получить статистику тренировок за период
    
    Args:
        user_id: ID пользователя
        days: Количество дней для анализа
        
    Returns:
        Словарь со статистикой:
        - total_count: общее количество тренировок
        - total_distance: общий километраж
        - types_count: словарь с количеством тренировок по типам
        - avg_fatigue: средний уровень усталости
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Получаем все тренировки за период
        async with db.execute(
            """
            SELECT type, distance, calculated_volume, fatigue_level
            FROM trainings 
            WHERE user_id = ? 
            AND date >= date('now', ? || ' days')
            """,
            (user_id, f'-{days}')
        ) as cursor:
            trainings = await cursor.fetchall()
        
        if not trainings:
            return {
                'total_count': 0,
                'total_distance': 0.0,
                'types_count': {},
                'avg_fatigue': 0
            }
        
        # Подсчёт статистики
        total_count = len(trainings)
        total_distance = 0.0
        types_count = {}
        fatigue_sum = 0
        fatigue_count = 0
        
        for training in trainings:
            # Подсчёт по типам
            t_type = training['type']
            types_count[t_type] = types_count.get(t_type, 0) + 1
            
            # Подсчёт дистанции
            distance = training['distance']
            calculated_volume = training['calculated_volume']
            
            if calculated_volume:  # Для интервальных тренировок
                total_distance += calculated_volume
            elif distance:  # Для остальных
                total_distance += distance
            
            # Подсчёт усталости
            if training['fatigue_level']:
                fatigue_sum += training['fatigue_level']
                fatigue_count += 1
        
        avg_fatigue = round(fatigue_sum / fatigue_count, 1) if fatigue_count > 0 else 0
        
        return {
            'total_count': total_count,
            'total_distance': round(total_distance, 2),
            'types_count': types_count,
            'avg_fatigue': avg_fatigue
        }

