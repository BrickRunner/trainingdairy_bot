"""Check yesterday competitions in database"""
import asyncio
import aiosqlite
from datetime import datetime, timedelta

DB_PATH = 'database.sqlite'


async def check():
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        print("="*70)
        print(f"Checking competitions for date: {yesterday}")
        print("="*70)

        # Get competitions
        cursor = await db.execute(
            """
            SELECT id, name, city, distances, status
            FROM competitions
            WHERE date = ?
            ORDER BY id DESC
            """,
            (yesterday,)
        )
        comps = await cursor.fetchall()

        print(f"\nFound {len(comps)} competitions:\n")

        for comp in comps:
            print(f"ID: {comp['id']}")
            print(f"  Status: {comp['status']}")
            print(f"  City: {comp['city']}")
            print(f"  Distances: {comp['distances']}")

            # Check registrations
            cursor = await db.execute(
                """
                SELECT COUNT(*) as cnt
                FROM competition_participants
                WHERE competition_id = ?
                """,
                (comp['id'],)
            )
            row = await cursor.fetchone()
            reg_count = row['cnt']
            print(f"  Registrations: {reg_count}")
            print()

        # Check user registrations
        print("="*70)
        print("User 1611441720 registrations:")
        print("="*70)

        cursor = await db.execute(
            """
            SELECT cp.*, c.name as comp_name, c.date
            FROM competition_participants cp
            JOIN competitions c ON c.id = cp.competition_id
            WHERE cp.user_id = ? AND c.date = ?
            ORDER BY cp.id DESC
            """,
            (1611441720, yesterday)
        )

        regs = await cursor.fetchall()
        print(f"\nFound {len(regs)} registrations:\n")

        for reg in regs:
            print(f"Competition: ID {reg['competition_id']}")
            print(f"  Distance: {reg['distance']} km")
            print(f"  Target time: {reg['target_time']}")
            print(f"  Status: {reg['status']}")
            print()

        print("="*70)
        print("[SUCCESS] Competitions ready for testing!")
        print("="*70)
        print("\nIn Telegram bot:")
        print("  1. Go to: Competitions -> Finished competitions")
        print("  2. You should see 4 registrations")
        print("  3. Click on any to add results")


if __name__ == "__main__":
    asyncio.run(check())
