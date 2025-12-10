"""
Проверка и добавление поля distance_name
"""
import asyncio
import aiosqlite
import sys

DB_PATH = "database/training_diary.db"


async def check_and_add():
    """Проверить и добавить поле distance_name"""
    print("Подключение к базе данных...", flush=True)
    async with aiosqlite.connect(DB_PATH) as db:
        print("Подключено!", flush=True)

        # Проверяем структуру таблицы
        print("\nПроверка структуры таблицы competition_participants...", flush=True)
        cursor = await db.execute("PRAGMA table_info(competition_participants)")
        columns = await cursor.fetchall()

        print(f"Найдено {len(columns)} колонок:", flush=True)
        for col in columns:
            print(f"  - {col[1]} ({col[2]})", flush=True)

        column_names = [col[1] for col in columns]

        if 'distance_name' in column_names:
            print("\n✅ Поле distance_name уже существует", flush=True)
            return

        print("\n⚠️ Поле distance_name НЕ найдено", flush=True)
        print("Добавление поля distance_name...", flush=True)

        try:
            # Добавляем новое поле
            await db.execute("""
                ALTER TABLE competition_participants
                ADD COLUMN distance_name TEXT
            """)

            await db.commit()
            print("✅ Поле distance_name успешно добавлено!", flush=True)

            # Проверяем снова
            print("\nПроверка после добавления...", flush=True)
            cursor = await db.execute("PRAGMA table_info(competition_participants)")
            columns = await cursor.fetchall()
            column_names = [col[1] for col in columns]

            if 'distance_name' in column_names:
                print("✅ ПОДТВЕРЖДЕНО: Поле distance_name добавлено", flush=True)
            else:
                print("❌ ОШИБКА: Поле не найдено после добавления", flush=True)

        except Exception as e:
            print(f"❌ Ошибка при добавлении поля: {e}", flush=True)
            sys.exit(1)


if __name__ == '__main__':
    asyncio.run(check_and_add())
    print("\nГотово!", flush=True)
