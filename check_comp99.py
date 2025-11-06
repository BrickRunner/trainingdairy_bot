"""
Проверка соревнования ID 99
"""
import asyncio
import aiosqlite
import os

DB_PATH = os.getenv('DB_PATH', 'bot_data.db')


async def check():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Проверяем соревнование
        cursor = await db.execute("SELECT * FROM competitions WHERE id = 99")
        comp = await cursor.fetchone()

        if not comp:
            print("[X] Competition 99 NOT FOUND")
        else:
            print("[OK] Competition 99 EXISTS:")
            print(f"  Name: {comp['name']}")
            print(f"  Date: {comp['date']}")
            print(f"  Type: {comp['type']}")

        # Проверяем участников
        cursor = await db.execute("SELECT * FROM competition_participants WHERE competition_id = 99")
        participants = await cursor.fetchall()
        print(f"\nParticipants: {len(participants)}")
        for p in participants:
            print(f"  User: {p['user_id']}, Distance: {p['distance']}, Status: {p['status']}")

        # Проверяем напоминания
        cursor = await db.execute("SELECT * FROM competition_reminders WHERE competition_id = 99 ORDER BY scheduled_date")
        reminders = await cursor.fetchall()
        print(f"\nReminders: {len(reminders)}")
        for rem in reminders:
            status = "sent" if rem['sent'] else "pending"
            print(f"  Type: {rem['reminder_type']}, Date: {rem['scheduled_date']}, Status: {status}")


if __name__ == "__main__":
    asyncio.run(check())
