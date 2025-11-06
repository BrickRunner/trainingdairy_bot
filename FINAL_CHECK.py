"""
ФИНАЛЬНАЯ ПРОВЕРКА НАПОМИНАНИЙ
"""
import asyncio
import aiosqlite
from datetime import date

# ВАЖНО: Используем ту же базу, что и бот
DB_PATH = 'database.sqlite'


async def check():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        print("=" * 60)
        print("FINAL CHECK - bot_data.db")
        print("=" * 60)

        # Проверяем таблицу
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='competition_reminders'"
        )
        table_exists = await cursor.fetchone()

        if not table_exists:
            print("\n[X] TABLE competition_reminders NOT FOUND!")
            print("Run migration first!")
            return

        print("\n[OK] Table competition_reminders exists")

        # Проверяем соревнование 99
        cursor = await db.execute("SELECT id, name, date FROM competitions WHERE id = 99")
        comp = await cursor.fetchone()

        if comp:
            print(f"\n[OK] Competition 99 found: {comp['name']} on {comp['date']}")
        else:
            print("\n[X] Competition 99 NOT FOUND")
            return

        # Проверяем участника
        cursor = await db.execute(
            "SELECT * FROM competition_participants WHERE competition_id = 99"
        )
        participant = await cursor.fetchone()

        if participant:
            print(f"[OK] Participant found: User {participant['user_id']}, Distance: {participant['distance']}")
        else:
            print("[X] No participants for competition 99")

        # Проверяем напоминания
        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM competition_reminders WHERE competition_id = 99"
        )
        row = await cursor.fetchone()
        reminders_count = row['cnt']

        print(f"\nReminders for competition 99: {reminders_count}")

        if reminders_count == 0:
            print("[!] NO REMINDERS - Need to restart bot!")
            return

        # Показываем напоминания
        cursor = await db.execute(
            """
            SELECT * FROM competition_reminders
            WHERE competition_id = 99
            ORDER BY scheduled_date
            """
        )
        reminders = await cursor.fetchall()

        today = date.today()
        today_str = today.strftime('%Y-%m-%d')

        for rem in reminders:
            status = "SENT" if rem['sent'] else "PENDING"
            is_today = " <-- TODAY!" if rem['scheduled_date'] == today_str else ""
            print(f"  - {rem['reminder_type']}: {rem['scheduled_date']} ({status}){is_today}")

        print("\n" + "=" * 60)
        print("NEXT STEPS:")
        print("1. If reminders count = 0: RESTART BOT")
        print("2. Wait for 10:20 tomorrow for next reminder")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(check())
