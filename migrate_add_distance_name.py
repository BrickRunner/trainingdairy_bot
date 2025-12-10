"""
Миграция: добавление поля distance_name в competition_participants
Пересоздание таблицы с сохранением данных
"""
import sqlite3
import json

DB_PATH = "database/training_diary.db"


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Создаём временную таблицу с новой структурой
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS competition_participants_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competition_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,

                distance REAL,
                distance_name TEXT,
                target_time TEXT,

                finish_time TEXT,
                place_overall INTEGER,
                place_age_category INTEGER,
                age_category TEXT,
                qualification TEXT,
                result_comment TEXT,
                result_photo TEXT,

                status TEXT DEFAULT 'registered',

                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                result_added_at TIMESTAMP,

                FOREIGN KEY (competition_id) REFERENCES competitions(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(competition_id, user_id, distance, distance_name)
            )
        """)

        # 2. Копируем данные из старой таблицы
        cursor.execute("""
            INSERT INTO competition_participants_new
            (id, competition_id, user_id, distance, distance_name, target_time,
             finish_time, place_overall, place_age_category, age_category,
             qualification, result_comment, result_photo, status,
             registered_at, result_added_at)
            SELECT
                id, competition_id, user_id, distance, NULL as distance_name, target_time,
                finish_time, place_overall, place_age_category, age_category,
                qualification, result_comment, result_photo, status,
                registered_at, result_added_at
            FROM competition_participants
        """)

        # 3. Удаляем старую таблицу
        cursor.execute("DROP TABLE competition_participants")

        # 4. Переименовываем новую таблицу
        cursor.execute("ALTER TABLE competition_participants_new RENAME TO competition_participants")

        conn.commit()

        # 5. Проверка
        cursor.execute("PRAGMA table_info(competition_participants)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        if 'distance_name' in column_names:
            with open("migration_success.txt", "w", encoding="utf-8") as f:
                f.write("SUCCESS: distance_name column added\n")
                f.write(f"Total columns: {len(columns)}\n")
                for col in columns:
                    f.write(f"  - {col[1]} ({col[2]})\n")
            return True
        else:
            with open("migration_error.txt", "w", encoding="utf-8") as f:
                f.write("ERROR: distance_name column not found after migration\n")
            return False

    except Exception as e:
        conn.rollback()
        with open("migration_error.txt", "w", encoding="utf-8") as f:
            f.write(f"ERROR: {str(e)}\n")
            import traceback
            f.write(traceback.format_exc())
        return False

    finally:
        conn.close()


if __name__ == '__main__':
    success = migrate()
    exit(0 if success else 1)
