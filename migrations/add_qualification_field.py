"""
Миграция: добавление поля qualification в таблицы competition_participants и personal_records
"""
import asyncio
import aiosqlite
import os

DB_PATH = os.getenv('DB_PATH', 'bot_data.db')

async def migrate():
    async with aiosqlite.connect(DB_PATH) as db:
        # Добавляем поле qualification в competition_participants
        cursor = await db.execute('PRAGMA table_info(competition_participants)')
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]

        if 'qualification' not in column_names:
            print("Добавляем поле qualification в competition_participants...")
            await db.execute('''
                ALTER TABLE competition_participants
                ADD COLUMN qualification TEXT
            ''')
            await db.commit()
            print("[OK] Поле qualification добавлено в competition_participants")
        else:
            print("[INFO] Поле qualification уже существует в competition_participants")

        # Добавляем поле qualification в personal_records
        cursor = await db.execute('PRAGMA table_info(personal_records)')
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]

        if 'qualification' not in column_names:
            print("Добавляем поле qualification в personal_records...")
            await db.execute('''
                ALTER TABLE personal_records
                ADD COLUMN qualification TEXT
            ''')
            await db.commit()
            print("[OK] Поле qualification добавлено в personal_records")
        else:
            print("[INFO] Поле qualification уже существует в personal_records")

if __name__ == '__main__':
    asyncio.run(migrate())
