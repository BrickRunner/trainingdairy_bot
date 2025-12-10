import sqlite3
import sys
import os

DB_PATH = "database/training_diary.db"
OUTPUT_FILE = "db_check_result.txt"

with open(OUTPUT_FILE, "w") as f:
    try:
        if not os.path.exists(DB_PATH):
            f.write("ERROR: Database file does not exist\n")
            sys.exit(1)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='competition_participants'")
        table = cursor.fetchone()

        if not table:
            f.write("ERROR: Table competition_participants does not exist\n")
            conn.close()
            sys.exit(1)

        f.write("Table competition_participants exists\n\n")

        # Check columns
        cursor.execute("PRAGMA table_info(competition_participants)")
        columns = cursor.fetchall()

        f.write(f"Total columns: {len(columns)}\n\n")
        f.write("Columns:\n")
        for col in columns:
            f.write(f"  {col[1]} ({col[2]})\n")

        column_names = [col[1] for col in columns]

        f.write("\n")
        if 'distance_name' in column_names:
            f.write("SUCCESS: distance_name column EXISTS!\n")
        else:
            f.write("ERROR: distance_name column NOT FOUND\n")

        conn.close()

    except Exception as e:
        f.write(f"ERROR: {e}\n")
        import traceback
        f.write(traceback.format_exc())

print(f"Results written to {OUTPUT_FILE}")
