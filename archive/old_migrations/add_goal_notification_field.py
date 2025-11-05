"""
Миграция: Добавление поля last_goal_notification_week в таблицу user_settings
"""
import sqlite3
import os

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

def migrate():
    """Добавить поле last_goal_notification_week в таблицу user_settings"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Проверяем, существует ли уже это поле
    cursor.execute("PRAGMA table_info(user_settings)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'last_goal_notification_week' not in columns:
        print("INFO: Добавляем поле last_goal_notification_week...")
        cursor.execute("""
            ALTER TABLE user_settings
            ADD COLUMN last_goal_notification_week TEXT
        """)
        conn.commit()
        print("OK: Поле last_goal_notification_week успешно добавлено")
    else:
        print("INFO: Поле last_goal_notification_week уже существует")

    conn.close()

if __name__ == '__main__':
    migrate()
    print("INFO: Миграция завершена")
