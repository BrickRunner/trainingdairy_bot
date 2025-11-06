"""
Миграция всех данных в единую базу database.sqlite
"""
import sqlite3
import os

SOURCE_DB = 'bot_data.db'
TARGET_DB = 'database.sqlite'


def migrate():
    """Перенести все данные из bot_data.db в database.sqlite"""

    if not os.path.exists(SOURCE_DB):
        print(f"[X] Source database {SOURCE_DB} not found")
        return

    print("=" * 60)
    print("MIGRATION TO SINGLE DATABASE")
    print("=" * 60)

    # Подключаемся к обеим базам
    source_conn = sqlite3.connect(SOURCE_DB)
    target_conn = sqlite3.connect(TARGET_DB)

    source_cursor = source_conn.cursor()
    target_cursor = target_conn.cursor()

    try:
        # 1. Переносим соревнования
        print("\n1. Migrating competitions...")
        source_cursor.execute("SELECT * FROM competitions")
        competitions = source_cursor.fetchall()

        if competitions:
            # Получаем структуру таблицы
            source_cursor.execute("PRAGMA table_info(competitions)")
            columns = [col[1] for col in source_cursor.fetchall()]

            placeholders = ','.join(['?' for _ in columns])
            columns_str = ','.join(columns)

            for comp in competitions:
                try:
                    target_cursor.execute(
                        f"INSERT OR IGNORE INTO competitions ({columns_str}) VALUES ({placeholders})",
                        comp
                    )
                except Exception as e:
                    print(f"  [!] Error inserting competition {comp[0]}: {e}")

            print(f"  [OK] Migrated {len(competitions)} competitions")
        else:
            print("  [i] No competitions to migrate")

        # 2. Переносим участников
        print("\n2. Migrating competition_participants...")
        source_cursor.execute("SELECT * FROM competition_participants")
        participants = source_cursor.fetchall()

        if participants:
            source_cursor.execute("PRAGMA table_info(competition_participants)")
            columns = [col[1] for col in source_cursor.fetchall()]

            placeholders = ','.join(['?' for _ in columns])
            columns_str = ','.join(columns)

            for participant in participants:
                try:
                    target_cursor.execute(
                        f"INSERT OR IGNORE INTO competition_participants ({columns_str}) VALUES ({placeholders})",
                        participant
                    )
                except Exception as e:
                    print(f"  [!] Error inserting participant: {e}")

            print(f"  [OK] Migrated {len(participants)} participants")
        else:
            print("  [i] No participants to migrate")

        # 3. Создаём таблицу напоминаний если её нет
        print("\n3. Creating competition_reminders table...")
        target_cursor.execute("""
            CREATE TABLE IF NOT EXISTS competition_reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                competition_id INTEGER NOT NULL,
                reminder_type TEXT NOT NULL,
                scheduled_date DATE NOT NULL,
                sent INTEGER DEFAULT 0,
                sent_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_settings(user_id),
                FOREIGN KEY (competition_id) REFERENCES competitions(id)
            )
        """)

        target_cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_comp_reminders_user
            ON competition_reminders(user_id)
        """)

        target_cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_comp_reminders_scheduled
            ON competition_reminders(scheduled_date, sent)
        """)

        print("  [OK] Table created")

        # 4. Переносим напоминания (если есть)
        print("\n4. Migrating competition_reminders...")
        try:
            source_cursor.execute("SELECT * FROM competition_reminders")
            reminders = source_cursor.fetchall()

            if reminders:
                source_cursor.execute("PRAGMA table_info(competition_reminders)")
                columns = [col[1] for col in source_cursor.fetchall()]

                placeholders = ','.join(['?' for _ in columns])
                columns_str = ','.join(columns)

                for reminder in reminders:
                    try:
                        target_cursor.execute(
                            f"INSERT OR IGNORE INTO competition_reminders ({columns_str}) VALUES ({placeholders})",
                            reminder
                        )
                    except Exception as e:
                        print(f"  [!] Error inserting reminder: {e}")

                print(f"  [OK] Migrated {len(reminders)} reminders")
            else:
                print("  [i] No reminders to migrate")
        except sqlite3.OperationalError:
            print("  [i] No reminders table in source database")

        # Коммитим изменения
        target_conn.commit()

        print("\n" + "=" * 60)
        print("MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)

        # Показываем статистику
        target_cursor.execute("SELECT COUNT(*) FROM competitions")
        comps_count = target_cursor.fetchone()[0]

        target_cursor.execute("SELECT COUNT(*) FROM competition_participants")
        parts_count = target_cursor.fetchone()[0]

        target_cursor.execute("SELECT COUNT(*) FROM competition_reminders")
        rems_count = target_cursor.fetchone()[0]

        print(f"\nFinal counts in {TARGET_DB}:")
        print(f"  Competitions: {comps_count}")
        print(f"  Participants: {parts_count}")
        print(f"  Reminders: {rems_count}")

    except Exception as e:
        print(f"\n[X] Migration failed: {e}")
        target_conn.rollback()
        raise

    finally:
        source_conn.close()
        target_conn.close()


if __name__ == "__main__":
    migrate()
