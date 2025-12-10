"""
Принудительная миграция - пересоздание таблицы competition_participants
ВАЖНО: Запускать только когда бот остановлен!
"""
import sqlite3
import sys

DB_PATH = "database.sqlite"

print("=" * 60)
print("МИГРАЦИЯ: Добавление поля distance_name")
print("=" * 60)

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Проверяем текущую структуру
    print("\n1. Проверка текущей структуры...")
    cursor.execute("PRAGMA table_info(competition_participants)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]

    print(f"   Найдено колонок: {len(columns)}")

    if 'distance_name' in column_names:
        print("   ✅ Поле distance_name уже существует!")
        print("\n✅ Миграция не требуется")
        conn.close()
        sys.exit(0)

    print("   ⚠️  Поле distance_name НЕ найдено")

    # Проверяем, есть ли данные
    cursor.execute("SELECT COUNT(*) FROM competition_participants")
    count = cursor.fetchone()[0]
    print(f"\n2. Записей в таблице: {count}")

    # Создаём резервную копию данных
    if count > 0:
        print("\n3. Создание резервной копии данных...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS competition_participants_backup AS
            SELECT * FROM competition_participants
        """)
        print("   ✅ Резервная копия создана: competition_participants_backup")

    # Удаляем старую таблицу
    print("\n4. Удаление старой таблицы...")
    cursor.execute("DROP TABLE IF EXISTS competition_participants")
    print("   ✅ Старая таблица удалена")

    # Создаём новую таблицу с правильной структурой
    print("\n5. Создание новой таблицы с полем distance_name...")
    cursor.execute("""
        CREATE TABLE competition_participants (
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
    print("   ✅ Новая таблица создана")

    # Восстанавливаем данные если были
    if count > 0:
        print("\n6. Восстановление данных...")
        cursor.execute("""
            INSERT INTO competition_participants
            (id, competition_id, user_id, distance, distance_name, target_time,
             finish_time, place_overall, place_age_category, age_category,
             qualification, result_comment, result_photo, status,
             registered_at, result_added_at)
            SELECT
                id, competition_id, user_id, distance, NULL, target_time,
                finish_time, place_overall, place_age_category, age_category,
                qualification, result_comment, result_photo, status,
                registered_at, result_added_at
            FROM competition_participants_backup
        """)
        print(f"   ✅ Восстановлено записей: {count}")

    conn.commit()

    # Проверка
    print("\n7. Проверка новой структуры...")
    cursor.execute("PRAGMA table_info(competition_participants)")
    new_columns = cursor.fetchall()
    new_column_names = [col[1] for col in new_columns]

    print(f"   Колонок в новой таблице: {len(new_columns)}")
    for col in new_columns:
        marker = "✓" if col[1] == 'distance_name' else " "
        print(f"   {marker} {col[1]:20s} {col[2]}")

    if 'distance_name' in new_column_names:
        print("\n" + "=" * 60)
        print("✅ МИГРАЦИЯ УСПЕШНО ЗАВЕРШЕНА!")
        print("=" * 60)
        conn.close()
        sys.exit(0)
    else:
        print("\n❌ ОШИБКА: Поле distance_name не найдено после миграции")
        conn.close()
        sys.exit(1)

except sqlite3.OperationalError as e:
    if "database is locked" in str(e):
        print("\n❌ ОШИБКА: База данных заблокирована!")
        print("   Остановите бота и запустите скрипт снова")
    else:
        print(f"\n❌ ОШИБКА: {e}")
    sys.exit(1)

except Exception as e:
    print(f"\n❌ НЕОЖИДАННАЯ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
