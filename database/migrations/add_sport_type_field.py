"""
Миграция для добавления поля sport_type в таблицу competitions
Это поле хранит вид спорта: 'бег', 'велоспорт', 'плавание', 'триатлон'
"""

import aiosqlite
import os
import asyncio


DB_PATH = os.getenv('DB_PATH', 'database.sqlite')


async def migrate():
    """Добавить поле sport_type в таблицу competitions"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Проверяем, существует ли уже поле
        async with db.execute("PRAGMA table_info(competitions)") as cursor:
            columns = await cursor.fetchall()
            column_names = [col[1] for col in columns]

        if 'sport_type' not in column_names:
            print("Добавление поля sport_type в таблицу competitions...")
            await db.execute(
                "ALTER TABLE competitions ADD COLUMN sport_type TEXT DEFAULT 'бег'"
            )
            await db.commit()
            print("OK: Поле sport_type успешно добавлено")
        else:
            print("Поле sport_type уже существует")


if __name__ == '__main__':
    asyncio.run(migrate())
