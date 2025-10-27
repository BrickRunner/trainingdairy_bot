"""
Скрипт для пересчета уровней всех пользователей
"""

import aiosqlite
import os
import asyncio
import sys

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from database.level_queries import calculate_and_update_user_level


DB_PATH = os.getenv('DB_PATH', 'database.sqlite')


async def get_all_user_ids():
    """Получить ID всех пользователей"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id FROM users") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]


async def recalculate_all_levels():
    """Пересчитать уровни всех пользователей"""
    user_ids = await get_all_user_ids()

    if not user_ids:
        print("Нет пользователей в базе данных")
        return

    print(f"Пересчет уровней для {len(user_ids)} пользователей...")

    for user_id in user_ids:
        try:
            result = await calculate_and_update_user_level(user_id)
            status = "изменен" if result['level_changed'] else "не изменен"
            print(f"Пользователь {user_id}: {result['old_level']} -> {result['new_level']} ({status})")
            print(f"  Тренировок на этой неделе: {result['current_week_trainings']}")
            print(f"  Всего тренировок: {result['total_trainings']}")
        except Exception as e:
            print(f"Ошибка при пересчете уровня пользователя {user_id}: {e}")

    print(f"\nГотово! Пересчитано уровней: {len(user_ids)}")


if __name__ == '__main__':
    asyncio.run(recalculate_all_levels())
