"""
Миграция: добавление столбцов для плавания в таблицу trainings
"""

import aiosqlite
import asyncio
import os

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')


async def migrate():
    """Добавить столбцы для плавания в таблицу trainings"""
    async with aiosqlite.connect(DB_PATH) as db:
        print("Проверка текущей структуры таблицы trainings...")

        # Проверяем существующие столбцы
        async with db.execute("PRAGMA table_info(trainings)") as cursor:
            columns = await cursor.fetchall()
            existing_columns = [col[1] for col in columns]
            print(f"Существующие столбцы: {existing_columns}")

        # Список столбцов для добавления
        columns_to_add = [
            ('swimming_location', 'TEXT'),
            ('pool_length', 'INTEGER'),
            ('swimming_styles', 'TEXT'),
            ('swimming_sets', 'TEXT')
        ]

        # Добавляем недостающие столбцы
        for column_name, column_type in columns_to_add:
            if column_name not in existing_columns:
                print(f"Добавление столбца {column_name} ({column_type})...")
                try:
                    await db.execute(f"ALTER TABLE trainings ADD COLUMN {column_name} {column_type}")
                    await db.commit()
                    print(f"✅ Столбец {column_name} успешно добавлен")
                except Exception as e:
                    print(f"❌ Ошибка при добавлении столбца {column_name}: {e}")
            else:
                print(f"ℹ️  Столбец {column_name} уже существует")

        print("\n✅ Миграция завершена!")

        # Проверяем финальную структуру
        async with db.execute("PRAGMA table_info(trainings)") as cursor:
            columns = await cursor.fetchall()
            print(f"\nФинальная структура таблицы trainings:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")


if __name__ == '__main__':
    asyncio.run(migrate())
