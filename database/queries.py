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


async def get_training_by_id(training_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Получить тренировку по ID
    
    Args:
        training_id: ID тренировки
        user_id: ID пользователя (для проверки прав)
        
    Returns:
        Словарь с данными тренировки или None
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM trainings WHERE id = ? AND user_id = ?",
            (training_id, user_id)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None


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


async def get_trainings_by_period(user_id: int, period: str) -> list:
    """
    Получить тренировки пользователя за календарный период
    
    Args:
        user_id: ID пользователя
        period: Период ('week' - текущая неделя, '2weeks' - текущая и прошлая недели, 'month' - текущий месяц)
        
    Returns:
        Список тренировок за период (отсортированных по дате тренировки, от старых к новым)
    """
    from datetime import datetime, timedelta
    
    # Определяем начальную дату в зависимости от периода
    today = datetime.now().date()
    
    if period == 'week':
        # Текущая календарная неделя (с понедельника)
        start_date = today - timedelta(days=today.weekday())
    elif period == '2weeks':
        # Текущая и прошлая календарные недели (с понедельника прошлой недели)
        start_date = today - timedelta(days=today.weekday() + 7)
    elif period == 'month':
        # Текущий календарный месяц (с 1-го числа)
        start_date = today.replace(day=1)
    else:
        # По умолчанию - текущая неделя
        start_date = today - timedelta(days=today.weekday())
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT * FROM trainings 
            WHERE user_id = ? 
            AND date >= ?
            AND date <= ?
            ORDER BY date ASC
            """,
            (user_id, start_date.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_training_statistics(user_id: int, period: str) -> Dict[str, Any]:
    """
    Получить статистику тренировок за календарный период
    
    Args:
        user_id: ID пользователя
        period: Период ('week', '2weeks', 'month')
        
    Returns:
        Словарь со статистикой:
        - total_count: общее количество тренировок
        - total_distance: общий километраж
        - types_count: словарь с количеством тренировок по типам
        - avg_fatigue: средний уровень усталости
    """
    from datetime import datetime, timedelta
    
    # Определяем начальную дату в зависимости от периода
    today = datetime.now().date()
    
    if period == 'week':
        # Текущая календарная неделя (с понедельника)
        start_date = today - timedelta(days=today.weekday())
    elif period == '2weeks':
        # Текущая и прошлая календарные недели (с понедельника прошлой недели)
        start_date = today - timedelta(days=today.weekday() + 7)
    elif period == 'month':
        # Текущий календарный месяц (с 1-го числа)
        start_date = today.replace(day=1)
    else:
        # По умолчанию - текущая неделя
        start_date = today - timedelta(days=today.weekday())
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Получаем все тренировки за период (до сегодняшнего дня включительно)
        async with db.execute(
            """
            SELECT type, distance, calculated_volume, fatigue_level
            FROM trainings 
            WHERE user_id = ? 
            AND date >= ?
            AND date <= ?
            """,
            (user_id, start_date.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))
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

async def get_trainings_by_custom_period(user_id: int, start_date: str, end_date: str) -> list:
    """
    Получить тренировки пользователя за произвольный период
    
    Args:
        user_id: ID пользователя
        start_date: Начальная дата в формате 'YYYY-MM-DD'
        end_date: Конечная дата в формате 'YYYY-MM-DD'
        
    Returns:
        Список тренировок за период (отсортированных по дате, от старых к новым)
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT * FROM trainings 
            WHERE user_id = ? 
            AND date >= ?
            AND date <= ?
            ORDER BY date ASC
            """,
            (user_id, start_date, end_date)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_statistics_by_custom_period(user_id: int, start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Получить статистику тренировок за произвольный период
    
    Args:
        user_id: ID пользователя
        start_date: Начальная дата в формате 'YYYY-MM-DD'
        end_date: Конечная дата в формате 'YYYY-MM-DD'
        
    Returns:
        Словарь со статистикой
    """
    trainings = await get_trainings_by_custom_period(user_id, start_date, end_date)
    
    total_count = len(trainings)
    total_distance = 0.0
    types_count = {}
    fatigue_sum = 0
    fatigue_count = 0
    
    for training in trainings:
        # Подсчёт дистанции
        if training.get('distance'):
            total_distance += float(training['distance'])
        elif training.get('calculated_volume'):
            total_distance += float(training['calculated_volume'])
        
        # Подсчёт типов
        t_type = training['type']
        types_count[t_type] = types_count.get(t_type, 0) + 1
        
        # Подсчёт усталости
        if training.get('fatigue_level'):
            fatigue_sum += training['fatigue_level']
            fatigue_count += 1
    
    avg_fatigue = round(fatigue_sum / fatigue_count, 1) if fatigue_count > 0 else 0
    
    return {
        'total_count': total_count,
        'total_distance': round(total_distance, 2),
        'types_count': types_count,
        'avg_fatigue': avg_fatigue
    }


# ========== ФУНКЦИИ ДЛЯ РАБОТЫ С НАСТРОЙКАМИ ==========

async def init_user_settings(user_id: int) -> None:
    """
    Инициализировать настройки пользователя (с дефолтными значениями)
    
    Args:
        user_id: Telegram ID пользователя
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO user_settings (user_id)
            VALUES (?)
            """,
            (user_id,)
        )
        await db.commit()


async def get_user_settings(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Получить настройки пользователя
    
    Args:
        user_id: Telegram ID пользователя
        
    Returns:
        Словарь с настройками или None
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM user_settings WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None


async def update_user_setting(user_id: int, field: str, value: Any) -> None:
    """
    Обновить конкретное поле в настройках пользователя
    
    Args:
        user_id: Telegram ID пользователя
        field: Название поля для обновления
        value: Новое значение
    """
    # Сначала инициализируем настройки если их нет
    await init_user_settings(user_id)
    
    async with aiosqlite.connect(DB_PATH) as db:
        query = f"UPDATE user_settings SET {field} = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?"
        await db.execute(query, (value, user_id))
        await db.commit()


async def calculate_pulse_zones(max_pulse: int) -> Dict[str, tuple]:
    """
    Рассчитать пульсовые зоны на основе максимального пульса
    
    Args:
        max_pulse: Максимальный пульс
        
    Returns:
        Словарь с зонами: {'zone1': (min, max), 'zone2': (min, max), ...}
    """
    return {
        'zone1': (int(max_pulse * 0.50), int(max_pulse * 0.60)),
        'zone2': (int(max_pulse * 0.60), int(max_pulse * 0.70)),
        'zone3': (int(max_pulse * 0.70), int(max_pulse * 0.80)),
        'zone4': (int(max_pulse * 0.80), int(max_pulse * 0.90)),
        'zone5': (int(max_pulse * 0.90), int(max_pulse * 1.00)),
    }


async def set_pulse_zones_auto(user_id: int, age: int) -> None:
    """
    Установить пульсовые зоны автоматически на основе возраста

    Args:
        user_id: Telegram ID пользователя
        age: Возраст пользователя
    """
    # Получаем пол пользователя для более точной формулы
    settings = await get_user_settings(user_id)
    gender = settings.get('gender') if settings else None

    # Формула Карвонена с учётом пола:
    # Мужчины: 220 - возраст
    # Женщины: 226 - возраст
    if gender == 'female':
        max_pulse = 226 - age
    else:
        max_pulse = 220 - age

    zones = await calculate_pulse_zones(max_pulse)
    
    await init_user_settings(user_id)
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            UPDATE user_settings SET 
                max_pulse = ?,
                zone1_min = ?, zone1_max = ?,
                zone2_min = ?, zone2_max = ?,
                zone3_min = ?, zone3_max = ?,
                zone4_min = ?, zone4_max = ?,
                zone5_min = ?, zone5_max = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """,
            (
                max_pulse,
                zones['zone1'][0], zones['zone1'][1],
                zones['zone2'][0], zones['zone2'][1],
                zones['zone3'][0], zones['zone3'][1],
                zones['zone4'][0], zones['zone4'][1],
                zones['zone5'][0], zones['zone5'][1],
                user_id
            )
        )
        await db.commit()


async def set_pulse_zones_manual(user_id: int, max_pulse: int) -> None:
    """
    Установить пульсовые зоны вручную на основе максимального пульса
    
    Args:
        user_id: Telegram ID пользователя
        max_pulse: Максимальный пульс
    """
    zones = await calculate_pulse_zones(max_pulse)
    
    await init_user_settings(user_id)
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            UPDATE user_settings SET 
                max_pulse = ?,
                zone1_min = ?, zone1_max = ?,
                zone2_min = ?, zone2_max = ?,
                zone3_min = ?, zone3_max = ?,
                zone4_min = ?, zone4_max = ?,
                zone5_min = ?, zone5_max = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """,
            (
                max_pulse,
                zones['zone1'][0], zones['zone1'][1],
                zones['zone2'][0], zones['zone2'][1],
                zones['zone3'][0], zones['zone3'][1],
                zones['zone4'][0], zones['zone4'][1],
                zones['zone5'][0], zones['zone5'][1],
                user_id
            )
        )
        await db.commit()


async def get_pulse_zone_for_value(user_id: int, pulse: int) -> Optional[str]:
    """
    Определить в какой зоне находится значение пульса

    Args:
        user_id: Telegram ID пользователя
        pulse: Значение пульса

    Returns:
        Название зоны ('zone1', 'zone2', etc.) или None
    """
    settings = await get_user_settings(user_id)
    if not settings or not settings.get('max_pulse'):
        return None

    zones = [
        ('zone1', settings['zone1_min'], settings['zone1_max']),
        ('zone2', settings['zone2_min'], settings['zone2_max']),
        ('zone3', settings['zone3_min'], settings['zone3_max']),
        ('zone4', settings['zone4_min'], settings['zone4_max']),
        ('zone5', settings['zone5_min'], settings['zone5_max']),
    ]

    # Используем zone_min <= pulse < zone_max для всех зон кроме последней
    # Для последней зоны используем zone_min <= pulse <= zone_max
    for i, (zone_name, zone_min, zone_max) in enumerate(zones):
        if i == len(zones) - 1:
            # Последняя зона - включаем верхнюю границу
            if zone_min <= pulse <= zone_max:
                return zone_name
        else:
            # Остальные зоны - не включаем верхнюю границу
            if zone_min <= pulse < zone_max:
                return zone_name

    return None


import json

async def set_main_training_types(user_id: int, types: list) -> None:
    """
    Установить основные типы тренировок
    
    Args:
        user_id: Telegram ID пользователя
        types: Список типов тренировок
    """
    await update_user_setting(user_id, 'main_training_types', json.dumps(types, ensure_ascii=False))


async def get_main_training_types(user_id: int) -> list:
    """
    Получить основные типы тренировок
    
    Args:
        user_id: Telegram ID пользователя
        
    Returns:
        Список типов тренировок
    """
    settings = await get_user_settings(user_id)
    if not settings or not settings.get('main_training_types'):
        return ['кросс']
    
    try:
        return json.loads(settings['main_training_types'])
    except:
        return ['кросс']


async def set_training_type_goals(user_id: int, goals: dict) -> None:
    """
    Установить цели по типам тренировок
    
    Args:
        user_id: Telegram ID пользователя
        goals: Словарь целей {"кросс": 30, "плавание": 5}
    """
    await update_user_setting(user_id, 'training_type_goals', json.dumps(goals, ensure_ascii=False))


async def get_training_type_goals(user_id: int) -> dict:
    """
    Получить цели по типам тренировок
    
    Args:
        user_id: Telegram ID пользователя
        
    Returns:
        Словарь целей
    """
    settings = await get_user_settings(user_id)
    if not settings or not settings.get('training_type_goals'):
        return {}
    
    try:
        return json.loads(settings['training_type_goals'])
    except:
        return {}


async def set_training_type_goal(user_id: int, training_type: str, goal: float) -> None:
    """
    Установить цель для конкретного типа тренировки
    
    Args:
        user_id: Telegram ID пользователя
        training_type: Тип тренировки
        goal: Целевое значение (км или количество)
    """
    goals = await get_training_type_goals(user_id)
    goals[training_type] = goal
    await set_training_type_goals(user_id, goals)


async def convert_distance(distance: float, from_unit: str, to_unit: str) -> float:
    """
    Конвертировать дистанцию между единицами измерения
    
    Args:
        distance: Значение дистанции
        from_unit: Исходная единица ('км' или 'мили')
        to_unit: Целевая единица ('км' или 'мили')
        
    Returns:
        Сконвертированное значение
    """
    if from_unit == to_unit:
        return distance
    
    if from_unit == 'км' and to_unit == 'мили':
        return distance * 0.621371
    elif from_unit == 'мили' and to_unit == 'км':
        return distance * 1.60934
    
    return distance


async def convert_weight(weight: float, from_unit: str, to_unit: str) -> float:
    """
    Конвертировать вес между единицами измерения

    Args:
        weight: Значение веса
        from_unit: Исходная единица ('кг' или 'фунты')
        to_unit: Целевая единица ('кг' или 'фунты')

    Returns:
        Сконвертированное значение
    """
    if from_unit == to_unit:
        return weight

    if from_unit == 'кг' and to_unit == 'фунты':
        return weight * 2.20462
    elif from_unit == 'фунты' and to_unit == 'кг':
        return weight * 0.453592

    return weight


async def recalculate_all_weights(user_id: int, old_unit: str, new_unit: str) -> dict:
    """
    Пересчитать все значения веса пользователя при изменении единиц измерения

    Args:
        user_id: Telegram ID пользователя
        old_unit: Старая единица измерения ('кг' или 'фунты')
        new_unit: Новая единица измерения ('кг' или 'фунты')

    Returns:
        Словарь с информацией о пересчете:
        - updated_count: количество обновленных полей
        - fields: список обновленных полей
    """
    if old_unit == new_unit:
        return {'updated_count': 0, 'fields': []}

    updated_fields = []

    async with aiosqlite.connect(DB_PATH) as db:
        # Получаем текущие значения веса из user_settings
        async with db.execute(
            "SELECT weight, weight_goal FROM user_settings WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()

            if row:
                current_weight = row[0]
                weight_goal = row[1]

                # Пересчитываем текущий вес если он есть
                if current_weight is not None:
                    new_weight = await convert_weight(current_weight, old_unit, new_unit)
                    new_weight = round(new_weight, 1)  # Округление до 1 знака
                    await db.execute(
                        "UPDATE user_settings SET weight = ? WHERE user_id = ?",
                        (new_weight, user_id)
                    )
                    updated_fields.append(f"Текущий вес: {current_weight:.1f} {old_unit} → {new_weight:.1f} {new_unit}")

                # Пересчитываем целевой вес если он есть
                if weight_goal is not None:
                    new_goal = await convert_weight(weight_goal, old_unit, new_unit)
                    new_goal = round(new_goal, 1)  # Округление до 1 знака
                    await db.execute(
                        "UPDATE user_settings SET weight_goal = ? WHERE user_id = ?",
                        (new_goal, user_id)
                    )
                    updated_fields.append(f"Целевой вес: {weight_goal:.1f} {old_unit} → {new_goal:.1f} {new_unit}")

        await db.commit()

    return {
        'updated_count': len(updated_fields),
        'fields': updated_fields
    }


def format_date_by_setting(date_str: str, format_setting: str) -> str:
    """
    Отформатировать дату согласно настройкам пользователя
    
    Args:
        date_str: Дата в формате 'YYYY-MM-DD'
        format_setting: Формат из настроек ('DD.MM.YYYY', 'MM/DD/YYYY', 'YYYY-MM-DD')
        
    Returns:
        Отформатированная дата
    """
    from datetime import datetime
    
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        
        if format_setting == 'DD.MM.YYYY':
            return date_obj.strftime('%d.%m.%Y')
        elif format_setting == 'MM/DD/YYYY':
            return date_obj.strftime('%m/%d/%Y')
        else:  
            return date_obj.strftime('%Y-%m-%d')
    except:
        return date_str
