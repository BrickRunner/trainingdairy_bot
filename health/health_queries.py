"""
Запросы к базе данных для модуля здоровья
"""

import aiosqlite
from datetime import date, timedelta
from typing import Optional, Dict, List
import logging
import os

logger = logging.getLogger(__name__)

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')


async def save_health_metrics(
    user_id: int,
    metric_date: date,
    morning_pulse: Optional[int] = None,
    weight: Optional[float] = None,
    sleep_duration: Optional[float] = None,
    sleep_quality: Optional[int] = None,
    mood: Optional[int] = None,
    stress_level: Optional[int] = None,
    energy_level: Optional[int] = None,
    notes: Optional[str] = None
) -> bool:
    """
    Сохраняет метрики здоровья за день.
    Обновляет только те поля, которые переданы (не None).
    """
    try:
        logger.info(f"save_health_metrics called: user_id={user_id}, date={metric_date}, "
                   f"pulse={morning_pulse}, weight={weight}, sleep={sleep_duration}, quality={sleep_quality}")

        async with aiosqlite.connect(DB_PATH) as db:
            # Сначала проверяем, есть ли запись
            async with db.execute(
                "SELECT id FROM health_metrics WHERE user_id = ? AND date = ?",
                (user_id, metric_date)
            ) as cursor:
                existing = await cursor.fetchone()
                logger.info(f"Existing record: {existing}")

            if existing:
                # Запись существует - обновляем только переданные поля
                update_parts = []
                params = []

                if morning_pulse is not None:
                    update_parts.append("morning_pulse = ?")
                    params.append(morning_pulse)
                if weight is not None:
                    update_parts.append("weight = ?")
                    params.append(weight)
                if sleep_duration is not None:
                    update_parts.append("sleep_duration = ?")
                    params.append(sleep_duration)
                if sleep_quality is not None:
                    update_parts.append("sleep_quality = ?")
                    params.append(sleep_quality)
                if mood is not None:
                    update_parts.append("mood = ?")
                    params.append(mood)
                if stress_level is not None:
                    update_parts.append("stress_level = ?")
                    params.append(stress_level)
                if energy_level is not None:
                    update_parts.append("energy_level = ?")
                    params.append(energy_level)
                if notes is not None:
                    update_parts.append("notes = ?")
                    params.append(notes)

                if update_parts:
                    update_parts.append("updated_at = CURRENT_TIMESTAMP")
                    params.extend([user_id, metric_date])

                    query = f"""
                        UPDATE health_metrics
                        SET {', '.join(update_parts)}
                        WHERE user_id = ? AND date = ?
                    """
                    logger.info(f"UPDATE query: {query}")
                    logger.info(f"UPDATE params: {params}")
                    await db.execute(query, params)
            else:
                # Записи нет - создаем новую
                logger.info(f"INSERT new record with values: pulse={morning_pulse}, weight={weight}, "
                           f"sleep={sleep_duration}, quality={sleep_quality}")
                await db.execute("""
                    INSERT INTO health_metrics
                    (user_id, date, morning_pulse, weight, sleep_duration, sleep_quality,
                     mood, stress_level, energy_level, notes, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (user_id, metric_date, morning_pulse, weight, sleep_duration,
                      sleep_quality, mood, stress_level, energy_level, notes))

            await db.commit()
            logger.info("Commit successful")
            return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении метрик здоровья: {e}")
        return False


async def get_health_metrics_by_date(user_id: int, metric_date: date) -> Optional[Dict]:
    """Получает метрики здоровья за конкретный день"""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM health_metrics
                WHERE user_id = ? AND date = ?
            """, (user_id, metric_date)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    except Exception as e:
        logger.error(f"Ошибка при получении метрик здоровья: {e}")
        return None


async def get_health_metrics_range(
    user_id: int,
    start_date: date,
    end_date: date
) -> List[Dict]:
    """Получает метрики здоровья за период"""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM health_metrics
                WHERE user_id = ? AND date BETWEEN ? AND ?
                ORDER BY date ASC
            """, (user_id, start_date, end_date)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Ошибка при получении метрик за период: {e}")
        return []


async def get_latest_health_metrics(user_id: int, days: int = 7) -> List[Dict]:
    """Получает последние N дней метрик"""
    end_date = date.today()
    start_date = end_date - timedelta(days=days-1)
    return await get_health_metrics_range(user_id, start_date, end_date)


async def get_health_statistics(user_id: int, days: int = 30) -> Dict:
    """Получает статистику здоровья за период"""
    metrics = await get_latest_health_metrics(user_id, days)

    if not metrics:
        return {}

    pulse_values = [m['morning_pulse'] for m in metrics if m.get('morning_pulse')]
    weight_values = [m['weight'] for m in metrics if m.get('weight')]
    sleep_values = [m['sleep_duration'] for m in metrics if m.get('sleep_duration')]

    stats = {
        'total_days': len(metrics),
        'pulse': {
            'avg': sum(pulse_values) / len(pulse_values) if pulse_values else None,
            'min': min(pulse_values) if pulse_values else None,
            'max': max(pulse_values) if pulse_values else None,
            'trend': _calculate_trend(pulse_values) if len(pulse_values) > 1 else None
        },
        'weight': {
            'current': weight_values[-1] if weight_values else None,
            'start': weight_values[0] if weight_values else None,
            'change': (weight_values[-1] - weight_values[0]) if len(weight_values) > 1 else None,
            'trend': _calculate_trend(weight_values) if len(weight_values) > 1 else None
        },
        'sleep': {
            'avg': sum(sleep_values) / len(sleep_values) if sleep_values else None,
            'min': min(sleep_values) if sleep_values else None,
            'max': max(sleep_values) if sleep_values else None
        }
    }

    return stats


def _calculate_trend(values: List[float]) -> str:
    """Вычисляет тренд (возрастающий/убывающий/стабильный)"""
    if len(values) < 2:
        return 'stable'

    first_half = sum(values[:len(values)//2]) / (len(values)//2)
    second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)

    diff = second_half - first_half
    if abs(diff) < 0.05 * first_half:  # Менее 5% изменения
        return 'stable'
    return 'increasing' if diff > 0 else 'decreasing'


async def check_today_metrics_filled(user_id: int) -> Dict[str, bool]:
    """Проверяет, какие метрики заполнены сегодня"""
    today = date.today()
    metrics = await get_health_metrics_by_date(user_id, today)

    if not metrics:
        return {
            'morning_pulse': False,
            'weight': False,
            'sleep_duration': False
        }

    return {
        'morning_pulse': metrics.get('morning_pulse') is not None,
        'weight': metrics.get('weight') is not None,
        'sleep_duration': metrics.get('sleep_duration') is not None
    }
