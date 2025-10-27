"""
Миграция для добавления полей level_updated_week в таблицу users
Это поле хранит неделю последнего обновления уровня в формате YYYY-WW
"""

import aiosqlite
import os
import asyncio


DB_PATH = os.getenv('DB_PATH', 'database.sqlite')


async def migrate():
    """Добавить поле level_updated_week в таблицу users"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Проверяем, существует ли уже поле
        async with db.execute("PRAGMA table_info(users)") as cursor:
            columns = await cursor.fetchall()
            column_names = [col[1] for col in columns]

        if 'level_updated_week' not in column_names:
            print("Добавление поля level_updated_week в таблицу users...")
            await db.execute(
                "ALTER TABLE users ADD COLUMN level_updated_week TEXT"
            )
            await db.commit()
            print("OK: Поле level_updated_week успешно добавлено")
        else:
            print("Поле level_updated_week уже существует")


if __name__ == '__main__':
    asyncio.run(migrate())
