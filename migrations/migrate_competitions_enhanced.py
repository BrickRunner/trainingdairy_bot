"""
Миграция для расширенной функциональности соревнований:
- Добавление полей для хранения деталей соревнований
- Расширение таблицы участников (цель, результаты, напоминания)
- Добавление таблицы для предложений соревнований от тренеров
- Добавление таблицы для напоминаний о соревнованиях
"""

import sqlite3
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = os.getenv('DB_PATH', 'bot_data.db')


def migrate():
    """Выполнить миграцию базы данных"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        logger.info("Starting competitions enhanced migration...")

        # 1. Расширяем таблицу competitions
        logger.info("Extending competitions table...")

        # Добавляем новые поля в competitions
        new_columns_competitions = [
            ("city", "TEXT"),
            ("country", "TEXT DEFAULT 'Россия'"),
            ("location", "TEXT"),
            ("distances", "TEXT"),  # JSON array
            ("type", "TEXT"),  # марафон, полумарафон, забег, трейл, ультра
            ("description", "TEXT"),
            ("official_url", "TEXT"),
            ("organizer", "TEXT"),
            ("registration_status", "TEXT DEFAULT 'unknown'"),  # open, closed, unknown
            ("is_official", "INTEGER DEFAULT 0"),  # парсеное или созданное пользователем
            ("source_url", "TEXT"),  # откуда спарсено
        ]

        for column_name, column_type in new_columns_competitions:
            try:
                cursor.execute(f"ALTER TABLE competitions ADD COLUMN {column_name} {column_type}")
                logger.info(f"  ✓ Added column: {column_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    logger.info(f"  - Column {column_name} already exists")
                else:
                    raise

        # 2. Расширяем таблицу competition_participants
        logger.info("Extending competition_participants table...")

        new_columns_participants = [
            ("distance", "REAL"),  # выбранная дистанция
            ("target_time", "TEXT"),  # целевое время в формате HH:MM:SS
            ("finish_time", "TEXT"),  # финишное время
            ("place_overall", "INTEGER"),  # общее место
            ("place_age_group", "INTEGER"),  # место в возрастной группе
            ("place_gender", "INTEGER"),  # место среди пола
            ("registration_date", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("result_added_date", "TIMESTAMP"),
            ("notes", "TEXT"),  # заметки пользователя
            ("proposed_by_coach", "INTEGER DEFAULT 0"),  # предложено тренером
            ("proposed_by_coach_id", "INTEGER"),  # ID тренера который предложил
            ("proposal_status", "TEXT"),  # pending, accepted, rejected (для предложений от тренера)
            ("reminders_enabled", "INTEGER DEFAULT 1"),  # включены ли напоминания
        ]

        for column_name, column_type in new_columns_participants:
            try:
                cursor.execute(f"ALTER TABLE competition_participants ADD COLUMN {column_name} {column_type}")
                logger.info(f"  ✓ Added column: {column_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    logger.info(f"  - Column {column_name} already exists")
                else:
                    raise

        # 3. Создаём таблицу для напоминаний о соревнованиях
        logger.info("Creating competition_reminders table...")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS competition_reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                competition_id INTEGER NOT NULL,
                reminder_type TEXT NOT NULL,  -- '30days', '14days', '7days', '3days', '1day', 'result_input'
                scheduled_date DATE NOT NULL,
                sent INTEGER DEFAULT 0,
                sent_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (competition_id) REFERENCES competitions(id),
                UNIQUE(user_id, competition_id, reminder_type)
            )
        """)
        logger.info("  ✓ Created competition_reminders table")

        # 4. Создаём таблицу для статистики соревнований пользователя
        logger.info("Creating user_competition_stats table...")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_competition_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                total_competitions INTEGER DEFAULT 0,
                total_completed INTEGER DEFAULT 0,
                total_marathons INTEGER DEFAULT 0,
                total_half_marathons INTEGER DEFAULT 0,
                total_10k INTEGER DEFAULT 0,
                total_5k INTEGER DEFAULT 0,
                best_marathon_time TEXT,
                best_half_marathon_time TEXT,
                best_10k_time TEXT,
                best_5k_time TEXT,
                total_distance_km REAL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        logger.info("  ✓ Created user_competition_stats table")

        # 5. Создаём индексы для оптимизации запросов
        logger.info("Creating indexes...")

        indexes = [
            ("idx_competitions_date", "CREATE INDEX IF NOT EXISTS idx_competitions_date ON competitions(date)"),
            ("idx_competitions_city", "CREATE INDEX IF NOT EXISTS idx_competitions_city ON competitions(city)"),
            ("idx_competitions_status", "CREATE INDEX IF NOT EXISTS idx_competitions_status ON competitions(status)"),
            ("idx_comp_participants_user", "CREATE INDEX IF NOT EXISTS idx_comp_participants_user ON competition_participants(participant_id)"),
            ("idx_comp_participants_comp", "CREATE INDEX IF NOT EXISTS idx_comp_participants_comp ON competition_participants(competition_id)"),
            ("idx_comp_reminders_user", "CREATE INDEX IF NOT EXISTS idx_comp_reminders_user ON competition_reminders(user_id)"),
            ("idx_comp_reminders_scheduled", "CREATE INDEX IF NOT EXISTS idx_comp_reminders_scheduled ON competition_reminders(scheduled_date, sent)"),
        ]

        for index_name, index_sql in indexes:
            cursor.execute(index_sql)
            logger.info(f"  ✓ Created index: {index_name}")

        conn.commit()
        logger.info("✅ Migration completed successfully!")

    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Migration failed: {e}")
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
