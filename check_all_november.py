"""
Проверка всех соревнований на ноябрь 2025
"""
import asyncio
import aiosqlite
import os

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')


async def check():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        print("=" * 60)
        print("VSE SOREVNOVANIYA NA NOYABR 2025")
        print("=" * 60)

        cursor = await db.execute(
            """
            SELECT id, name, date, type, city
            FROM competitions
            WHERE date LIKE '2025-11%'
            ORDER BY date
            """
        )
        comps = await cursor.fetchall()

        if not comps:
            print("\n[X] Net sorevnovaniy na noyabr 2025")
            return

        print(f"\nNaydeno {len(comps)} sorevnovaniy:\n")

        for comp in comps:
            print(f"ID: {comp['id']}")
            print(f"  Nazvanie: {comp['name']}")
            print(f"  Data: {comp['date']}")
            print(f"  Tip: {comp['type']}")
            print(f"  Gorod: {comp.get('city', 'N/A')}")

            # Проверяем участников
            cursor2 = await db.execute(
                "SELECT COUNT(*) as cnt FROM competition_participants WHERE competition_id = ?",
                (comp['id'],)
            )
            row = await cursor2.fetchone()
            participants_count = row['cnt']

            # Проверяем напоминания
            cursor3 = await db.execute(
                "SELECT COUNT(*) as cnt FROM competition_reminders WHERE competition_id = ?",
                (comp['id'],)
            )
            row = await cursor3.fetchone()
            reminders_count = row['cnt']

            print(f"  Uchastnikov: {participants_count}")
            print(f"  Napominaniy: {reminders_count}")
            print()


if __name__ == "__main__":
    asyncio.run(check())
