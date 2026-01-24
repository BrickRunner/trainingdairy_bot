import sqlite3
import os

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

print(f"Checking database: {DB_PATH}")
print("=" * 60)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Проверяем coach_links
cursor.execute("SELECT COUNT(*) FROM coach_links")
total = cursor.fetchone()[0]
print(f"Total coach_links: {total}")

cursor.execute("SELECT COUNT(*) FROM coach_links WHERE status='active'")
active = cursor.fetchone()[0]
print(f"Active coach_links: {active}")

# Показываем все записи
cursor.execute("SELECT coach_id, student_id, status FROM coach_links")
links = cursor.fetchall()

print("\nAll coach_links:")
for link in links:
    print(f"  Coach {link[0]} -> Student {link[1]} (status: {link[2]})")

conn.close()
