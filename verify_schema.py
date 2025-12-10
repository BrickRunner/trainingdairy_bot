import sqlite3
import sys

DB_PATH = "database/training_diary.db"

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='competition_participants'")
    if not cursor.fetchone():
        print("ERROR: Table competition_participants does not exist")
        sys.exit(1)

    # Check columns
    cursor.execute("PRAGMA table_info(competition_participants)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]

    print(f"Table has {len(columns)} columns")

    if 'distance_name' in column_names:
        print("SUCCESS: distance_name column exists!")
        sys.exit(0)
    else:
        print("ERROR: distance_name column NOT found")
        print("Columns:", column_names)
        sys.exit(1)

except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
finally:
    conn.close()
