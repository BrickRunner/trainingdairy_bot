import sqlite3

DB_PATH = "database/training_diary.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Check current structure
cursor.execute("PRAGMA table_info(competition_participants)")
columns = cursor.fetchall()

print("Current columns:")
for col in columns:
    print(f"  {col[1]} - {col[2]}")

column_names = [col[1] for col in columns]

if 'distance_name' not in column_names:
    print("\nAdding distance_name column...")
    cursor.execute("ALTER TABLE competition_participants ADD COLUMN distance_name TEXT")
    conn.commit()
    print("Done!")
else:
    print("\ndistance_name already exists!")

conn.close()
