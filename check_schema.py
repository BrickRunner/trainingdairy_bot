"""
Проверка схемы базы данных
"""
import sqlite3

DB_PATH = "database/training_diary.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Check table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='competition_participants'")
table = cursor.fetchone()

if table:
    print("✅ Таблица competition_participants существует")

    # Check columns
    cursor.execute("PRAGMA table_info(competition_participants)")
    columns = cursor.fetchall()

    print(f"\n📋 Колонки таблицы ({len(columns)}):")
    for col in columns:
        print(f"  {col[1]:20s} {col[2]:10s} {'NOT NULL' if col[3] else ''}")

    column_names = [col[1] for col in columns]

    if 'distance_name' in column_names:
        print("\n✅ Поле distance_name найдено!")
    else:
        print("\n❌ Поле distance_name НЕ найдено!")
else:
    print("❌ Таблица competition_participants не существует")

conn.close()
