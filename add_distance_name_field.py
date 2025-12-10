"""
Миграция: добавление поля distance_name в таблицу competition_participants
"""
import asyncio
import aiosqlite

DB_PATH = "database/training_diary.db"


async def add_distance_name_field():
    """Добавить поле distance_name в таблицу competition_participants"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Проверяем, есть ли уже поле distance_name
        cursor = await db.execute("PRAGMA table_info(competition_participants)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]

        if 'distance_name' in column_names:
            print("✅ Поле distance_name уже существует")
            return

        print("Добавление поля distance_name...")

        # Добавляем новое поле
        await db.execute("""
            ALTER TABLE competition_participants
            ADD COLUMN distance_name TEXT
        """)

        await db.commit()
        print("✅ Поле distance_name успешно добавлено!")


if __name__ == '__main__':
    asyncio.run(add_distance_name_field())
