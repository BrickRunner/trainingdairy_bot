"""
Миграция: добавление поля heart_rate в таблицу competition_participants
"""
import asyncio
import aiosqlite
import os

DB_PATH = os.getenv('DB_PATH', 'bot_data.db')

async def migrate():
    async with aiosqlite.connect(DB_PATH) as db:
        # Проверяем, существует ли поле
        cursor = await db.execute('PRAGMA table_info(competition_participants)')
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]

        if 'heart_rate' not in column_names:
            print("Добавляем поле heart_rate...")
            await db.execute('''
                ALTER TABLE competition_participants
                ADD COLUMN heart_rate INTEGER
            ''')
            await db.commit()
            print("[OK] Поле heart_rate добавлено")
        else:
            print("[INFO] Поле heart_rate уже существует")

if __name__ == '__main__':
    asyncio.run(migrate())
