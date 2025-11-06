"""
Проверка реальных соревнований и напоминаний для них
"""
import asyncio
import aiosqlite
import os
from datetime import date, datetime

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')


async def check():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        print("=" * 60)
        print("PROVERKA REALNYH SOREVNOVANIY")
        print("=" * 60)

        # 1. Все соревнования
        print("\n1. Vse sorevnovaniya v BD:")
        cursor = await db.execute(
            """
            SELECT id, name, date, type
            FROM competitions
            ORDER BY date
            """
        )
        comps = await cursor.fetchall()

        for comp in comps:
            comp_date = datetime.strptime(comp['date'], '%Y-%m-%d').date()
            days_diff = (comp_date - date.today()).days
            print(f"\n   ID: {comp['id']}")
            print(f"   Nazvanie: {comp['name']}")
            print(f"   Data: {comp['date']} (cherez {days_diff} dney)")
            print(f"   Tip: {comp['type']}")

            # Проверяем участников
            cursor2 = await db.execute(
                "SELECT COUNT(*) as cnt FROM competition_participants WHERE competition_id = ?",
                (comp['id'],)
            )
            row = await cursor2.fetchone()
            print(f"   Uchastnikov: {row['cnt']}")

            # Проверяем напоминания
            cursor3 = await db.execute(
                "SELECT COUNT(*) as cnt FROM competition_reminders WHERE competition_id = ?",
                (comp['id'],)
            )
            row = await cursor3.fetchone()
            print(f"   Napominaniy: {row['cnt']}")

        # 2. Участники соревнований
        print("\n\n2. Uchastniki sorevnovaniy:")
        cursor = await db.execute(
            """
            SELECT
                cp.id,
                cp.user_id,
                cp.competition_id,
                cp.distance,
                cp.status,
                c.name as comp_name,
                c.date as comp_date
            FROM competition_participants cp
            JOIN competitions c ON cp.competition_id = c.id
            ORDER BY cp.id DESC
            LIMIT 10
            """
        )
        participants = await cursor.fetchall()

        if participants:
            for p in participants:
                print(f"\n   ID: {p['id']}")
                print(f"   User ID: {p['user_id']}")
                print(f"   Sorevnovanie: {p['comp_name']}")
                print(f"   Data: {p['comp_date']}")
                print(f"   Distantsiya: {p['distance']} km")
                print(f"   Status: {p['status']}")

                # Проверяем напоминания для этого участника
                cursor2 = await db.execute(
                    """
                    SELECT id, reminder_type, scheduled_date, sent
                    FROM competition_reminders
                    WHERE user_id = ? AND competition_id = ?
                    ORDER BY scheduled_date
                    """,
                    (p['user_id'], p['competition_id'])
                )
                reminders = await cursor2.fetchall()
                print(f"   Napominaniy dlya etogo uchastnika: {len(reminders)}")
                if reminders:
                    for rem in reminders:
                        status = "otpravleno" if rem['sent'] else "NE otpravleno"
                        print(f"      - {rem['reminder_type']}: {rem['scheduled_date']} ({status})")
        else:
            print("   [X] Net uchastnikov")


if __name__ == "__main__":
    asyncio.run(check())
