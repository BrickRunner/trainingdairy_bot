"""
Проверка конкретного напоминания
"""
import asyncio
import aiosqlite
import os
from datetime import date

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')


async def check():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Проверяем напоминание ID 94
        cursor = await db.execute(
            """
            SELECT
                r.*,
                c.name as comp_name,
                c.date as comp_date
            FROM competition_reminders r
            LEFT JOIN competitions c ON r.competition_id = c.id
            WHERE r.id = 94
            """
        )
        reminder = await cursor.fetchone()

        if not reminder:
            print("[X] Napominanie ID 94 NE NAYDENO")

            # Покажем все напоминания на сегодня
            print("\nVse napominaniya na segodnya (2025-11-06):")
            cursor = await db.execute(
                """
                SELECT
                    r.id,
                    r.user_id,
                    r.competition_id,
                    r.reminder_type,
                    r.scheduled_date,
                    r.sent,
                    c.name as comp_name
                FROM competition_reminders r
                LEFT JOIN competitions c ON r.competition_id = c.id
                WHERE r.scheduled_date = '2025-11-06'
                ORDER BY r.id
                """
            )
            today_reminders = await cursor.fetchall()

            if today_reminders:
                for rem in today_reminders:
                    status = "OTPRAVLENO" if rem['sent'] else "NE otpravleno"
                    print(f"  ID: {rem['id']}, User: {rem['user_id']}, Comp: {rem['comp_name']}, Type: {rem['reminder_type']}, Status: {status}")
            else:
                print("  [X] Net napominaniy na segodnya")
            return

        print("=" * 60)
        print("NAPOMINANIE ID 94")
        print("=" * 60)
        print(f"User ID: {reminder['user_id']}")
        print(f"Competition ID: {reminder['competition_id']}")
        print(f"Competition name: {reminder['comp_name']}")
        print(f"Competition date: {reminder['comp_date']}")
        print(f"Reminder type: {reminder['reminder_type']}")
        print(f"Scheduled date: {reminder['scheduled_date']}")
        print(f"Sent: {reminder['sent']} ({'DA' if reminder['sent'] else 'NET'})")
        print(f"Sent at: {reminder['sent_at'] or 'N/A'}")
        print(f"Created at: {reminder['created_at']}")

        # Проверяем соревнование
        print("\n" + "=" * 60)
        print("PROVERKA SOREVNOVANIYA")
        print("=" * 60)

        if reminder['competition_id']:
            cursor = await db.execute(
                "SELECT * FROM competitions WHERE id = ?",
                (reminder['competition_id'],)
            )
            comp = await cursor.fetchone()

            if comp:
                print(f"Nazvanie: {comp['name']}")
                print(f"Data: {comp['date']}")
                print(f"Tip: {comp['type']}")
            else:
                print("[X] Sorevnovanie NE NAYDENO - eto problema!")
        else:
            print("[X] competition_id = NULL")

        # Проверяем участника
        print("\n" + "=" * 60)
        print("PROVERKA UCHASTNIKA")
        print("=" * 60)

        cursor = await db.execute(
            """
            SELECT * FROM competition_participants
            WHERE user_id = ? AND competition_id = ?
            """,
            (reminder['user_id'], reminder['competition_id'])
        )
        participant = await cursor.fetchone()

        if participant:
            print(f"Status: {participant['status']}")
            print(f"Distantsiya: {participant['distance']} km")
        else:
            print("[X] Uchastnik NE NAYDEN - eto problema!")


if __name__ == "__main__":
    asyncio.run(check())
