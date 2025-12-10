import sqlite3
import sys

DB_PATH = "database.sqlite"

print("="*60)
print("MIGRATION: Adding distance_name field")
print("="*60)

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check current structure
    print("\n1. Checking current structure...")
    cursor.execute("PRAGMA table_info(competition_participants)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]

    print(f"   Found columns: {len(columns)}")

    needs_migration = False
    if 'distance_name' not in column_names:
        print("   WARNING: distance_name field NOT found")
        needs_migration = True
    else:
        print("   OK: distance_name exists")

    if 'heart_rate' not in column_names:
        print("   WARNING: heart_rate field NOT found")
        needs_migration = True
    else:
        print("   OK: heart_rate exists")

    if not needs_migration:
        print("\n   SUCCESS: All required fields exist!")
        print("\nMigration not needed")
        conn.close()
        sys.exit(0)

    # Check if there is data
    cursor.execute("SELECT COUNT(*) FROM competition_participants")
    count = cursor.fetchone()[0]
    print(f"\n2. Records in table: {count}")

    # Create backup
    if count > 0:
        print("\n3. Creating backup...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS competition_participants_backup AS
            SELECT * FROM competition_participants
        """)
        print("   SUCCESS: Backup created: competition_participants_backup")

    # Drop old table
    print("\n4. Dropping old table...")
    cursor.execute("DROP TABLE IF EXISTS competition_participants")
    print("   SUCCESS: Old table dropped")

    # Create new table
    print("\n5. Creating new table with distance_name and heart_rate...")
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
            heart_rate INTEGER,
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
    print("   SUCCESS: New table created")

    # Restore data
    if count > 0:
        print("\n6. Restoring data...")
        cursor.execute("""
            INSERT INTO competition_participants
            (id, competition_id, user_id, distance, distance_name, target_time,
             finish_time, place_overall, place_age_category, age_category,
             heart_rate, qualification, result_comment, result_photo, status,
             registered_at, result_added_at)
            SELECT
                id, competition_id, user_id, distance, NULL, target_time,
                finish_time, place_overall, place_age_category, age_category,
                NULL, qualification, result_comment, result_photo, status,
                registered_at, result_added_at
            FROM competition_participants_backup
        """)
        print(f"   SUCCESS: Restored {count} records")

    conn.commit()

    # Verify
    print("\n7. Verifying new structure...")
    cursor.execute("PRAGMA table_info(competition_participants)")
    new_columns = cursor.fetchall()
    new_column_names = [col[1] for col in new_columns]

    print(f"   Columns in new table: {len(new_columns)}")
    for col in new_columns:
        marker = "[X]" if col[1] == 'distance_name' else "[ ]"
        print(f"   {marker} {col[1]:20s} {col[2]}")

    if 'distance_name' in new_column_names:
        print("\n" + "="*60)
        print("SUCCESS: MIGRATION COMPLETED!")
        print("="*60)
        conn.close()
        sys.exit(0)
    else:
        print("\nERROR: distance_name field not found after migration")
        conn.close()
        sys.exit(1)

except sqlite3.OperationalError as e:
    if "database is locked" in str(e):
        print("\nERROR: Database is locked!")
        print("   Stop the bot and run the script again")
    else:
        print(f"\nERROR: {e}")
    sys.exit(1)

except Exception as e:
    print(f"\nUNEXPECTED ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
