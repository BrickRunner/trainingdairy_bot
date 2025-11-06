"""
Добавление колонки heart_rate в competition_participants
"""
import sqlite3

conn = sqlite3.connect('database.sqlite')
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE competition_participants ADD COLUMN heart_rate INTEGER")
    conn.commit()
    print("[OK] Added heart_rate column")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("[i] Column heart_rate already exists")
    else:
        print(f"[X] Error: {e}")

conn.close()
