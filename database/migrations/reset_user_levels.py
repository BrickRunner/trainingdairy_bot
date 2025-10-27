"""
Скрипт для сброса уровней всех пользователей
Все уровни будут установлены в 'новичок' и пересчитаны заново
"""

import aiosqlite
import os
import asyncio


DB_PATH = os.getenv('DB_PATH', 'database.sqlite')


async def reset_levels():
    """Сбросить уровни всех пользователей"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Сбрасываем уровни и недели обновления
        await db.execute(
            "UPDATE users SET level = 'новичок', level_updated_week = NULL"
        )
        await db.commit()

        # Получаем количество обновленных пользователей
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            row = await cursor.fetchone()
            count = row[0] if row else 0

        print(f"Сброшено уровней пользователей: {count}")
        print("Уровни будут пересчитаны автоматически при следующей тренировке")


if __name__ == '__main__':
    asyncio.run(reset_levels())
