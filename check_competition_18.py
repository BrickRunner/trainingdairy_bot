"""
Проверка дистанций в соревновании 18
"""
import asyncio
import aiosqlite
import os
import json

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

async def check_comp():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute(
            "SELECT id, name, distances FROM competitions WHERE id = 18"
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                print(f"Competition ID: {row[0]}")
                print(f"Name: {row[1]}")
                print(f"\nDistances (raw): {row[2]}")
                print(f"Type: {type(row[2])}")

                try:
                    distances = json.loads(row[2]) if isinstance(row[2], str) else row[2]
                    print(f"\nParsed distances:")
                    for i, dist in enumerate(distances):
                        print(f"  [{i}] {dist} (type: {type(dist).__name__})")
                        if isinstance(dist, dict):
                            print(f"      distance: {dist.get('distance')}")
                            print(f"      name: {dist.get('name')}")
                except Exception as e:
                    print(f"Error parsing: {e}")

if __name__ == "__main__":
    asyncio.run(check_comp())
