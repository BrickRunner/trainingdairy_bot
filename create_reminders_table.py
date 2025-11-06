"""
Создание таблицы competition_reminders в bot_data.db
"""
import sqlite3

DB_PATH = 'bot_data.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    # Создаём таблицу напоминаний
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS competition_reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            competition_id INTEGER NOT NULL,
            reminder_type TEXT NOT NULL,
            scheduled_date DATE NOT NULL,
            sent INTEGER DEFAULT 0,
            sent_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_settings(user_id),
            FOREIGN KEY (competition_id) REFERENCES competitions(id)
        )
    """)

    # Создаём индексы
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_comp_reminders_user
        ON competition_reminders(user_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_comp_reminders_scheduled
        ON competition_reminders(scheduled_date, sent)
    """)

    conn.commit()
    print("[OK] Table competition_reminders created successfully!")

except Exception as e:
    print(f"[X] Error: {e}")
    conn.rollback()

finally:
    conn.close()
