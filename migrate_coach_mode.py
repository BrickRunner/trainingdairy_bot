"""
Миграция для добавления режима тренера
Добавляет:
- is_coach в user_settings
- coach_link_code в user_settings
- Обновляет структуру coach_links
"""

import asyncio
import aiosqlite
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "training_diary.db"


async def migrate_database():
    """Применить миграцию для режима тренера"""

    async with aiosqlite.connect(DB_PATH) as db:
        logger.info("Starting coach mode migration...")

        try:
            # Добавляем is_coach в user_settings
            logger.info("Adding is_coach column to user_settings...")
            await db.execute("""
                ALTER TABLE user_settings
                ADD COLUMN is_coach BOOLEAN DEFAULT 0
            """)
            logger.info("OK: is_coach column added")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                logger.info("SKIP: is_coach column already exists")
            else:
                logger.error(f"ERROR adding is_coach: {e}")

        try:
            # Добавляем coach_link_code в user_settings
            logger.info("Adding coach_link_code column to user_settings...")
            await db.execute("""
                ALTER TABLE user_settings
                ADD COLUMN coach_link_code TEXT UNIQUE
            """)
            logger.info("OK: coach_link_code column added")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                logger.info("SKIP: coach_link_code column already exists")
            else:
                logger.error(f"ERROR adding coach_link_code: {e}")

        try:
            # Добавляем removed_at в coach_links
            logger.info("Adding removed_at column to coach_links...")
            await db.execute("""
                ALTER TABLE coach_links
                ADD COLUMN removed_at TIMESTAMP
            """)
            logger.info("OK: removed_at column added")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                logger.info("SKIP: removed_at column already exists")
            else:
                logger.error(f"ERROR adding removed_at: {e}")

        # Обновляем статус по умолчанию для существующих записей
        try:
            logger.info("Updating existing coach_links status to 'active'...")
            await db.execute("""
                UPDATE coach_links
                SET status = 'active'
                WHERE status = 'pending'
            """)
            await db.commit()
            logger.info("OK: existing links updated")
        except Exception as e:
            logger.error(f"ERROR updating status: {e}")

        await db.commit()
        logger.info("Coach mode migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(migrate_database())
