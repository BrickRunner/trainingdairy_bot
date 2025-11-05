"""
Миграция для добавления функций тренера (Приоритет 1):
- added_by_coach_id в trainings
- is_planned в trainings
- coach_nickname в coach_links
- таблица training_comments
"""

import asyncio
import aiosqlite
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')


async def migrate_database():
    """Применить миграцию для функций тренера"""

    async with aiosqlite.connect(DB_PATH) as db:
        logger.info("Starting coach features migration...")

        # 1. Добавляем added_by_coach_id в trainings
        try:
            logger.info("Adding added_by_coach_id column to trainings...")
            await db.execute("""
                ALTER TABLE trainings
                ADD COLUMN added_by_coach_id INTEGER
            """)
            logger.info("OK: added_by_coach_id column added")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                logger.info("SKIP: added_by_coach_id column already exists")
            else:
                logger.error(f"ERROR adding added_by_coach_id: {e}")

        # 2. Добавляем is_planned в trainings
        try:
            logger.info("Adding is_planned column to trainings...")
            await db.execute("""
                ALTER TABLE trainings
                ADD COLUMN is_planned BOOLEAN DEFAULT 0
            """)
            logger.info("OK: is_planned column added")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                logger.info("SKIP: is_planned column already exists")
            else:
                logger.error(f"ERROR adding is_planned: {e}")

        # 3. Добавляем coach_nickname в coach_links
        try:
            logger.info("Adding coach_nickname column to coach_links...")
            await db.execute("""
                ALTER TABLE coach_links
                ADD COLUMN coach_nickname TEXT
            """)
            logger.info("OK: coach_nickname column added")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                logger.info("SKIP: coach_nickname column already exists")
            else:
                logger.error(f"ERROR adding coach_nickname: {e}")

        # 4. Создаём таблицу training_comments
        try:
            logger.info("Creating training_comments table...")
            await db.execute("""
                CREATE TABLE IF NOT EXISTS training_comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    training_id INTEGER NOT NULL,
                    author_id INTEGER NOT NULL,
                    comment TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    FOREIGN KEY (training_id) REFERENCES trainings(id),
                    FOREIGN KEY (author_id) REFERENCES users(id)
                )
            """)
            logger.info("OK: training_comments table created")
        except Exception as e:
            logger.error(f"ERROR creating training_comments: {e}")

        await db.commit()
        logger.info("Coach features migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(migrate_database())
