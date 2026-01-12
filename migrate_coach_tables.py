"""
Миграция базы данных для режима тренера и напоминаний

Добавляет:
1. Поле added_by_coach_id и is_planned в таблицу trainings
2. Поле coach_nickname в таблицу coach_links
3. Таблицу training_comments
4. Поля proposed_by_coach, proposed_by_coach_id, proposal_status, reminders_enabled в competition_participants
5. Поля training_reminder_days и training_reminder_time в user_settings
"""

import asyncio
import aiosqlite
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')


async def migrate():
    """Выполнить миграцию"""
    logger.info(f"Starting migration for {DB_PATH}")

    async with aiosqlite.connect(DB_PATH) as db:
        # 1. Добавляем поля в trainings
        logger.info("Checking trainings table...")
        try:
            await db.execute("ALTER TABLE trainings ADD COLUMN added_by_coach_id INTEGER")
            logger.info("  + Added added_by_coach_id to trainings")
        except Exception as e:
            if "duplicate column" in str(e).lower():
                logger.info("  - added_by_coach_id already exists")
            else:
                logger.error(f"  ! Error: {e}")

        try:
            await db.execute("ALTER TABLE trainings ADD COLUMN is_planned INTEGER DEFAULT 0")
            logger.info("  + Added is_planned to trainings")
        except Exception as e:
            if "duplicate column" in str(e).lower():
                logger.info("  - is_planned already exists")
            else:
                logger.error(f"  ! Error: {e}")

        # 2. Добавляем поле coach_nickname в coach_links
        logger.info("Checking coach_links table...")
        try:
            await db.execute("ALTER TABLE coach_links ADD COLUMN coach_nickname TEXT")
            logger.info("  + Added coach_nickname to coach_links")
        except Exception as e:
            if "duplicate column" in str(e).lower():
                logger.info("  - coach_nickname already exists")
            else:
                logger.error(f"  ! Error: {e}")

        # 3. Создаём таблицу training_comments
        logger.info("Checking training_comments table...")
        try:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS training_comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    training_id INTEGER NOT NULL,
                    author_id INTEGER NOT NULL,
                    comment TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (training_id) REFERENCES trainings(id),
                    FOREIGN KEY (author_id) REFERENCES users(id)
                )
            """)
            logger.info("  + Created training_comments table")
        except Exception as e:
            logger.error(f"  ! Error creating training_comments: {e}")

        # 4. Добавляем поля в competition_participants
        logger.info("Checking competition_participants table...")

        fields_to_add = [
            ("proposed_by_coach", "INTEGER DEFAULT 0"),
            ("proposed_by_coach_id", "INTEGER"),
            ("proposal_status", "TEXT"),
            ("reminders_enabled", "INTEGER DEFAULT 1"),
        ]

        for field_name, field_type in fields_to_add:
            try:
                await db.execute(f"ALTER TABLE competition_participants ADD COLUMN {field_name} {field_type}")
                logger.info(f"  + Added {field_name} to competition_participants")
            except Exception as e:
                if "duplicate column" in str(e).lower():
                    logger.info(f"  - {field_name} already exists")
                else:
                    logger.error(f"  ! Error adding {field_name}: {e}")

        # 5. Добавляем поля напоминаний в user_settings
        logger.info("Checking user_settings table for reminder fields...")

        reminder_fields = [
            ("training_reminders_enabled", "INTEGER DEFAULT 0"),
            ("training_reminder_days", "TEXT DEFAULT '[]'"),
            ("training_reminder_time", "TEXT"),
        ]

        for field_name, field_type in reminder_fields:
            try:
                await db.execute(f"ALTER TABLE user_settings ADD COLUMN {field_name} {field_type}")
                logger.info(f"  + Added {field_name} to user_settings")
            except Exception as e:
                if "duplicate column" in str(e).lower():
                    logger.info(f"  - {field_name} already exists")
                else:
                    logger.error(f"  ! Error adding {field_name}: {e}")

        # 6. Создаём таблицу competition_reminders если не существует
        logger.info("Checking competition_reminders table...")
        try:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS competition_reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    competition_id INTEGER NOT NULL,
                    reminder_type TEXT NOT NULL,
                    scheduled_date DATE NOT NULL,
                    sent INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sent_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (competition_id) REFERENCES competitions(id),
                    UNIQUE(user_id, competition_id, reminder_type)
                )
            """)
            logger.info("  + Created competition_reminders table")
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info("  - competition_reminders table already exists")
            else:
                logger.error(f"  ! Error creating competition_reminders: {e}")

        await db.commit()
        logger.info("Migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(migrate())
