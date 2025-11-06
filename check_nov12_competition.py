"""
Проверка соревнования на 12 ноября
"""
import asyncio
import aiosqlite
import os

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')


async def check():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        print("=" * 60)
        print("PROVERKA SOREVNOVANIYA NA 12.11.2025")
        print("=" * 60)

        # Ищем соревнование на 12 ноября
        cursor = await db.execute(
            """
            SELECT *
            FROM competitions
            WHERE date = '2025-11-12'
            """
        )
        comps = await cursor.fetchall()

        if not comps:
            print("\n[X] NE NAYDENO sorevnovaniy na 12.11.2025")
            print("\nProverka vseh sorevnovaniy na noyabr:")

            cursor = await db.execute(
                """
                SELECT id, name, date, type
                FROM competitions
                WHERE date LIKE '2025-11%'
                ORDER BY date
                """
            )
            nov_comps = await cursor.fetchall()

            if nov_comps:
                for comp in nov_comps:
                    print(f"  - {comp['date']}: {comp['name']} (ID: {comp['id']}, tip: {comp['type']})")
            else:
                print("  [X] Net sorevnovaniy na noyabr")
            return

        print(f"\n[OK] Naydeno {len(comps)} sorevnovaniy na 12.11.2025:\n")

        for comp in comps:
            print(f"ID: {comp['id']}")
            print(f"Nazvanie: {comp['name']}")
            print(f"Data: {comp['date']}")
            print(f"Gorod: {comp.get('city', 'N/A')}")
            print(f"Tip: {comp['type']}")
            print(f"Distantsii: {comp.get('distances', 'N/A')}")

            # Проверяем участников
            cursor2 = await db.execute(
                """
                SELECT *
                FROM competition_participants
                WHERE competition_id = ?
                """,
                (comp['id'],)
            )
            participants = await cursor2.fetchall()

            print(f"\nUchastnikov: {len(participants)}")
            if participants:
                for p in participants:
                    print(f"  - User ID: {p['user_id']}, distantsiya: {p['distance']} km, status: {p['status']}")

                    # Проверяем напоминания
                    cursor3 = await db.execute(
                        """
                        SELECT *
                        FROM competition_reminders
                        WHERE user_id = ? AND competition_id = ?
                        ORDER BY scheduled_date
                        """,
                        (p['user_id'], comp['id'])
                    )
                    reminders = await cursor3.fetchall()

                    print(f"    Napominaniy: {len(reminders)}")
                    if reminders:
                        for rem in reminders:
                            status = "otpravleno" if rem['sent'] else "NE otpravleno"
                            print(f"      - {rem['reminder_type']}: {rem['scheduled_date']} ({status})")
                    else:
                        print("      [X] NAPOMINANIYA NE SOZDANY!")
            else:
                print("  [X] Net uchastnikov")

            print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(check())
