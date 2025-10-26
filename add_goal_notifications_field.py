"""
Миграция: Добавление поля goal_notifications в таблицу user_settings
"""
import sqlite3
import os

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

def migrate():
    """Добавить поле goal_notifications в таблицу user_settings"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Проверяем, существует ли уже это поле
    cursor.execute("PRAGMA table_info(user_settings)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'goal_notifications' not in columns:
        print("INFO: Добавляем поле goal_notifications...")
        cursor.execute("""
            ALTER TABLE user_settings
            ADD COLUMN goal_notifications TEXT
        """)
        conn.commit()
        print("OK: Поле goal_notifications успешно добавлено")
    else:
        print("INFO: Поле goal_notifications уже существует")

    conn.close()

if __name__ == '__main__':
    migrate()
    print("INFO: Миграция завершена")
