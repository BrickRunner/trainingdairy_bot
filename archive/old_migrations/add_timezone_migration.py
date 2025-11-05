"""
Миграция: Добавление поля timezone в таблицу user_settings
"""

import sqlite3
import os

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

def migrate():
    """Добавить поле timezone в таблицу user_settings"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Проверяем существует ли уже поле timezone
        cursor.execute("PRAGMA table_info(user_settings)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'timezone' not in columns:
            print("Dobavlyaem pole timezone...")
            cursor.execute("""
                ALTER TABLE user_settings
                ADD COLUMN timezone TEXT DEFAULT 'Europe/Moscow'
            """)
            conn.commit()
            print("OK: Pole timezone uspeshno dobavleno!")
        else:
            print("INFO: Pole timezone uzhe suschestvuet")

    except Exception as e:
        print(f"ERROR: Oshibka migracii: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
