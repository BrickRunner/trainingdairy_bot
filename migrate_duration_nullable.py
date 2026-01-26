"""
Миграция: Убрать NOT NULL constraint для поля duration в таблице trainings

Дата: 2026-01-25
Причина: Для поддержки запланированных тренировок (is_planned=1),
         которые создаются без продолжительности и заполняются учеником позже.
"""

import aiosqlite
import asyncio
import os
from datetime import datetime


DB_PATH = os.getenv('DB_PATH', 'database.sqlite')


async def migrate_duration_nullable():
    """Убирает NOT NULL constraint для поля duration"""

    print(f"🔄 Начало миграции базы данных: {DB_PATH}")
    print(f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Создаем бэкап
    backup_path = f"{DB_PATH}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    try:
        import shutil
        shutil.copy2(DB_PATH, backup_path)
        print(f"✅ Создан бэкап: {backup_path}\n")
    except Exception as e:
        print(f"⚠️  Предупреждение: Не удалось создать бэкап: {e}\n")

    async with aiosqlite.connect(DB_PATH) as db:
        # Проверяем текущую структуру таблицы
        async with db.execute("PRAGMA table_info(trainings)") as cursor:
            columns = await cursor.fetchall()
            print("📋 Текущая структура таблицы trainings:")
            for col in columns:
                print(f"   {col}")

        print("\n🔨 Начинаем миграцию...")

        # 1. Создаем новую таблицу с правильной структурой
        await db.execute("""
            CREATE TABLE trainings_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                date DATE NOT NULL,
                time TEXT,
                duration INTEGER,
                distance REAL,
                avg_pace TEXT,
                pace_unit TEXT,
                avg_pulse INTEGER,
                max_pulse INTEGER,
                exercises TEXT,
                intervals TEXT,
                calculated_volume REAL,
                description TEXT,
                results TEXT,
                comment TEXT,
                fatigue_level INTEGER,
                added_by_coach_id INTEGER,
                is_planned INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (added_by_coach_id) REFERENCES users(id)
            )
        """)
        print("   ✓ Создана новая таблица trainings_new")

        # 2. Копируем данные из старой таблицы
        await db.execute("""
            INSERT INTO trainings_new
            SELECT * FROM trainings
        """)
        print("   ✓ Данные скопированы в новую таблицу")

        # 3. Удаляем старую таблицу
        await db.execute("DROP TABLE trainings")
        print("   ✓ Старая таблица удалена")

        # 4. Переименовываем новую таблицу
        await db.execute("ALTER TABLE trainings_new RENAME TO trainings")
        print("   ✓ Новая таблица переименована в trainings")

        await db.commit()

        # Проверяем новую структуру
        async with db.execute("PRAGMA table_info(trainings)") as cursor:
            columns = await cursor.fetchall()
            print("\n📋 Новая структура таблицы trainings:")
            for col in columns:
                print(f"   {col}")

        # Подсчитываем количество записей
        async with db.execute("SELECT COUNT(*) FROM trainings") as cursor:
            count = await cursor.fetchone()
            print(f"\n📊 Количество тренировок в базе: {count[0]}")

    print("\n✅ Миграция успешно завершена!")
    print(f"💾 Бэкап сохранен: {backup_path}")


async def check_migration_needed():
    """Проверяет, нужна ли миграция"""

    if not os.path.exists(DB_PATH):
        print(f"⚠️  База данных не найдена: {DB_PATH}")
        print("   Миграция не требуется - база будет создана с новой структурой.")
        return False

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("PRAGMA table_info(trainings)") as cursor:
            columns = await cursor.fetchall()

            # Ищем колонку duration
            for col in columns:
                # col = (cid, name, type, notnull, dflt_value, pk)
                if col[1] == 'duration':
                    if col[3] == 1:  # notnull == 1
                        print("⚠️  Обнаружен NOT NULL constraint для поля duration")
                        print("   Требуется миграция.")
                        return True
                    else:
                        print("✅ Поле duration уже nullable")
                        print("   Миграция не требуется.")
                        return False

    print("⚠️  Поле duration не найдено в таблице trainings")
    return False


async def main():
    """Главная функция"""

    print("="*60)
    print("МИГРАЦИЯ БАЗЫ ДАННЫХ")
    print("Убираем NOT NULL constraint для поля duration")
    print("="*60 + "\n")

    # Проверяем, нужна ли миграция
    needs_migration = await check_migration_needed()

    if not needs_migration:
        print("\n🎉 Миграция не требуется!")
        return

    # Запрашиваем подтверждение
    print("\n⚠️  ВНИМАНИЕ: Будет выполнена миграция базы данных!")
    print("   Будет создан бэкап, но рекомендуется создать копию базы вручную.")

    response = input("\n❓ Продолжить? (yes/no): ")

    if response.lower() in ['yes', 'y', 'да', 'д']:
        await migrate_duration_nullable()
    else:
        print("\n❌ Миграция отменена.")


if __name__ == "__main__":
    asyncio.run(main())
