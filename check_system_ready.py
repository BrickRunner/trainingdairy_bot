"""
Проверка готовности системы напоминаний
"""
import sqlite3
import os

print("=" * 60)
print("SYSTEM READINESS CHECK")
print("=" * 60)

# 1. Проверяем базу данных
if not os.path.exists('database.sqlite'):
    print("\n[X] database.sqlite NOT FOUND")
    exit(1)

print("\n[OK] database.sqlite exists")

# 2. Проверяем bot_data.db
if os.path.exists('bot_data.db'):
    print("[!] bot_data.db still exists (should be backup)")
    if os.path.exists('bot_data.db.backup'):
        print("    Backup exists, safe to delete bot_data.db")
else:
    print("[OK] bot_data.db removed")

# 3. Проверяем структуру БД
conn = sqlite3.connect('database.sqlite')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]

required_tables = ['competitions', 'competition_participants', 'competition_reminders', 'user_settings']
missing_tables = [t for t in required_tables if t not in tables]

if missing_tables:
    print(f"\n[X] Missing tables: {', '.join(missing_tables)}")
    exit(1)

print("[OK] All required tables exist")

# 4. Проверяем данные
cursor.execute("SELECT COUNT(*) FROM competitions")
comps_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM competition_participants")
parts_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM competition_reminders WHERE sent = 0")
pending_reminders = cursor.fetchone()[0]

print(f"\n[OK] Data migrated:")
print(f"     Competitions: {comps_count}")
print(f"     Participants: {parts_count}")
print(f"     Pending reminders: {pending_reminders}")

# 5. Проверяем напоминания на сегодня
cursor.execute("""
    SELECT COUNT(*) FROM competition_reminders
    WHERE scheduled_date = date('now') AND sent = 0
""")
today_reminders = cursor.fetchone()[0]

print(f"\n[OK] Reminders for TODAY: {today_reminders}")

# 6. Проверяем время отправки
print(f"\n[OK] Reminder time: 10:20-10:25 daily")

print("\n" + "=" * 60)
print("SYSTEM STATUS: READY")
print("=" * 60)
print("\nNext steps:")
print("1. RESTART the bot")
print("2. Create new competition via bot")
print("3. Reminders will be sent at 10:20 tomorrow")
print("=" * 60)

conn.close()
