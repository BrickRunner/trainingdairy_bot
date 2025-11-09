"""Проверка структуры БД"""
import asyncio
import aiosqlite

async def check_db():
    async with aiosqlite.connect('training_diary.db') as db:
        db.row_factory = aiosqlite.Row

        print("=== Список всех таблиц в БД ===\n")

        cursor = await db.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            ORDER BY name
        """)

        tables = await cursor.fetchall()

        for table in tables:
            table_name = table['name']
            print(f"\n📋 Таблица: {table_name}")

            # Получаем структуру таблицы
            cursor = await db.execute(f"PRAGMA table_info({table_name})")
            columns = await cursor.fetchall()

            for col in columns:
                print(f"   {col['name']}: {col['type']}")

            # Подсчитываем количество записей
            cursor = await db.execute(f"SELECT COUNT(*) as cnt FROM {table_name}")
            count = await cursor.fetchone()
            print(f"   📊 Записей: {count['cnt']}")

if __name__ == "__main__":
    asyncio.run(check_db())
