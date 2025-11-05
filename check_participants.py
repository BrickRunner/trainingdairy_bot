"""
Проверка записей участников соревнований
"""
import asyncio
import aiosqlite
import os

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')


async def check():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Проверяем структуру таблицы
        print("Struktura tablitsy competition_participants:")
        cursor = await db.execute("PRAGMA table_info(competition_participants)")
        columns = await cursor.fetchall()
        for col in columns:
            print(f"   - {col['name']}: {col['type']}")

        # Все записи
        print("\nVse zapisi v competition_participants:")
        cursor = await db.execute(
            """
            SELECT
                cp.*,
                c.name as comp_name,
                c.date as comp_date
            FROM competition_participants cp
            LEFT JOIN competitions c ON cp.competition_id = c.id
            ORDER BY cp.id DESC
            LIMIT 20
            """
        )
        rows = await cursor.fetchall()

        if rows:
            for row in rows:
                print(f"\n   ID: {row['id']}")
                print(f"   User ID: {row['user_id']}")
                print(f"   Competition: {row.get('comp_name', 'N/A')}")
                print(f"   Date: {row.get('comp_date', 'N/A')}")
                print(f"   Distance: {row.get('distance', 'N/A')}")
                print(f"   Status: {row.get('status', 'N/A')}")
                print(f"   Target time: {row.get('target_time', 'N/A')}")
        else:
            print("   [X] Net zapisey")

        # Подсчёт по статусам
        print("\n\nStatistika po statusam:")
        cursor = await db.execute(
            """
            SELECT status, COUNT(*) as cnt
            FROM competition_participants
            GROUP BY status
            """
        )
        rows = await cursor.fetchall()

        if rows:
            for row in rows:
                print(f"   {row['status'] or 'NULL'}: {row['cnt']}")
        else:
            print("   [X] Net zapisey")


if __name__ == "__main__":
    asyncio.run(check())
