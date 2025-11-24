"""
Миграция для добавления колонки qualification в таблицы
competition_participants и personal_records
"""

import asyncio
import sys
import os
import io

# Устанавливаем UTF-8 кодировку для вывода на Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aiosqlite


async def add_qualification_column():
    """
    Добавляет колонку qualification в таблицы competition_participants и personal_records
    """
    db_path = os.getenv('DB_PATH', 'database.sqlite')

    if not os.path.exists(db_path):
        print("⚠️ База данных не найдена. Колонка будет добавлена при создании таблиц.")
        return

    async with aiosqlite.connect(db_path) as db:
        try:
            # Проверяем, существует ли колонка в competition_participants
            async with db.execute("PRAGMA table_info(competition_participants)") as cursor:
                columns = await cursor.fetchall()
                column_names = [col[1] for col in columns]

                if 'qualification' not in column_names:
                    print("📝 Добавление колонки qualification в competition_participants...")
                    await db.execute("""
                        ALTER TABLE competition_participants
                        ADD COLUMN qualification TEXT
                    """)
                    await db.commit()
                    print("✅ Колонка qualification добавлена в competition_participants")
                else:
                    print("✓ Колонка qualification уже существует в competition_participants")

        except Exception as e:
            print(f"⚠️ Ошибка при добавлении колонки в competition_participants: {e}")

        try:
            # Проверяем, существует ли колонка в personal_records
            async with db.execute("PRAGMA table_info(personal_records)") as cursor:
                columns = await cursor.fetchall()
                column_names = [col[1] for col in columns]

                if 'qualification' not in column_names:
                    print("📝 Добавление колонки qualification в personal_records...")
                    await db.execute("""
                        ALTER TABLE personal_records
                        ADD COLUMN qualification TEXT
                    """)
                    await db.commit()
                    print("✅ Колонка qualification добавлена в personal_records")
                else:
                    print("✓ Колонка qualification уже существует в personal_records")

        except Exception as e:
            print(f"⚠️ Ошибка при добавлении колонки в personal_records: {e}")


async def main():
    """
    Основная функция
    """
    print("=" * 60)
    print("Миграция: Добавление колонки qualification")
    print("=" * 60)

    await add_qualification_column()

    print("\n" + "=" * 60)
    print("✅ Миграция завершена!")
    print("=" * 60)
    print("\n💡 Теперь можно:")
    print("   1. Перезапустить бота")
    print("   2. Запустить обновление разрядов: python migrations/update_qualifications.py")


if __name__ == "__main__":
    asyncio.run(main())
