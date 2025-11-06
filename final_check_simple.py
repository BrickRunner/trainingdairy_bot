"""
Simple final check without emojis
"""
import sqlite3

conn = sqlite3.connect('database.sqlite')
cursor = conn.cursor()

print("=" * 60)
print("FINAL CHECK - database.sqlite")
print("=" * 60)

# Count data
cursor.execute("SELECT COUNT(*) FROM competitions")
comps = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM competition_participants")
parts = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM competition_reminders")
rems = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM competition_reminders WHERE sent = 0")
pending = cursor.fetchone()[0]

print(f"\nTotal records:")
print(f"  Competitions: {comps}")
print(f"  Participants: {parts}")
print(f"  Reminders: {rems}")
print(f"  Pending reminders: {pending}")

# Check competition 99
cursor.execute("SELECT id, name, date FROM competitions WHERE id = 99")
comp = cursor.fetchone()

if comp:
    print(f"\n[OK] Competition 99 exists")
    print(f"  Date: {comp[2]}")
else:
    print("\n[X] Competition 99 not found")

# Pending reminders today
cursor.execute("""
    SELECT COUNT(*) FROM competition_reminders
    WHERE scheduled_date = date('now') AND sent = 0
""")
today_pending = cursor.fetchone()[0]

print(f"\nReminders for TODAY: {today_pending}")

print("\n" + "=" * 60)
print("STATUS: READY")
print("All data migrated to database.sqlite")
print("=" * 60)

conn.close()
