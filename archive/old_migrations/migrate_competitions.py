"""
Миграция базы данных: добавление таблиц для соревнований
"""

import aiosqlite
import asyncio
import os

DB_PATH = os.getenv('DB_PATH', 'bot_data.db')


async def migrate_database():
    """Выполнить миграцию базы данных"""

    print("=" * 60)
    print("DATABASE MIGRATION - COMPETITIONS TABLES")
    print("=" * 60)
    print()

    async with aiosqlite.connect(DB_PATH) as db:
        # 1. Проверяем существует ли старая таблица competitions
        async with db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='competitions'"
        ) as cursor:
            old_table = await cursor.fetchone()

        if old_table:
            print("WARNING: Found old table 'competitions'")
            print("   Creating backup...")

            # Создаём резервную копию старой таблицы
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS competitions_backup AS
                SELECT * FROM competitions
                """
            )
            print("   OK: Backup created: 'competitions_backup'")

            # Удаляем старую таблицу
            await db.execute("DROP TABLE IF EXISTS competitions")
            print("   OK: Old table dropped")
            print()

        # 2. Проверяем старую таблицу competition_participants
        async with db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='competition_participants'"
        ) as cursor:
            old_participants = await cursor.fetchone()

        if old_participants:
            print("WARNING: Found old table 'competition_participants'")

            # Создаём резервную копию
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS competition_participants_backup AS
                SELECT * FROM competition_participants
                """
            )
            print("   OK: Backup created: 'competition_participants_backup'")

            # Удаляем старую таблицу
            await db.execute("DROP TABLE IF EXISTS competition_participants")
            print("   OK: Old table dropped")
            print()

        # 3. Создаём новую таблицу competitions
        print("Создание таблицы 'competitions'...")
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS competitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                -- Основная информация
                name TEXT NOT NULL,
                date DATE NOT NULL,
                city TEXT,
                country TEXT DEFAULT 'Россия',
                location TEXT,

                -- Детали соревнования
                distances TEXT,
                type TEXT,
                description TEXT,
                official_url TEXT,

                -- Организатор
                organizer TEXT,

                -- Статусы
                registration_status TEXT DEFAULT 'unknown',
                status TEXT DEFAULT 'upcoming',

                -- Метаданные
                created_by INTEGER,
                is_official BOOLEAN DEFAULT 0,
                source_url TEXT,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (created_by) REFERENCES users(id)
            )
            """
        )
        print("   OK: Table 'competitions' created")
        print()

        # 4. Создаём новую таблицу competition_participants
        print("Creating table 'competition_participants'...")
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS competition_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                competition_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,

                -- Выбор дистанции и цели
                distance REAL,
                target_time TEXT,

                -- Результат после забега
                finish_time TEXT,
                place_overall INTEGER,
                place_age_category INTEGER,
                age_category TEXT,
                result_comment TEXT,
                result_photo TEXT,

                -- Статусы
                status TEXT DEFAULT 'registered',

                -- Даты
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                result_added_at TIMESTAMP,

                FOREIGN KEY (competition_id) REFERENCES competitions(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(competition_id, user_id, distance)
            )
            """
        )
        print("   OK: Table 'competition_participants' created")
        print()

        # 5. Создаём таблицу personal_records
        print("Creating table 'personal_records'...")
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS personal_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,
                distance REAL NOT NULL,

                -- Лучший результат
                best_time TEXT NOT NULL,
                competition_id INTEGER,
                date DATE NOT NULL,

                -- Метаданные
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (competition_id) REFERENCES competitions(id),
                UNIQUE(user_id, distance)
            )
            """
        )
        print("   OK: Table 'personal_records' created")
        print()

        await db.commit()

    print("=" * 60)
    print("MIGRATION COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Run bot: python main.py")
    print("2. Add test competitions: python add_test_competitions.py")
    print()


if __name__ == "__main__":
    asyncio.run(migrate_database())
