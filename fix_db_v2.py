import sqlite3
import sys

DB_PATH = "database/training_diary.db"

# Redirect output to file
log_file = open("migration_log.txt", "w", encoding="utf-8")
sys.stdout = log_file
sys.stderr = log_file

try:
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
        print("SUCCESS: distance_name column added!")

        # Verify
        cursor.execute("PRAGMA table_info(competition_participants)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        if 'distance_name' in column_names:
            print("VERIFIED: Column exists now")
        else:
            print("ERROR: Column not found after adding")
    else:
        print("\nINFO: distance_name already exists!")

    conn.close()
    print("\nMigration completed successfully!")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

finally:
    log_file.close()

# Print to console that log was created
with open("migration_log.txt", "r", encoding="utf-8") as f:
    content = f.read()

# Try to print with proper encoding handling
try:
    import codecs
    writer = codecs.getwriter('utf-8')(sys.stdout.buffer)
    writer.write(content)
except:
    pass
