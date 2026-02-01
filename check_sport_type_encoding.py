"""
Проверка кодировки sport_type в БД
"""
import asyncio
import aiosqlite

async def check():
    async with aiosqlite.connect('database.sqlite') as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute('''
            SELECT id, name, sport_type
            FROM competitions
            WHERE id = 22
        ''')
        row = await cursor.fetchone()

        if row:
            sport_type = row['sport_type']
            print(f"Competition: {row['name']}")
            print(f"Sport type: '{sport_type}'")
            print(f"Type: {type(sport_type)}")
            print(f"Length: {len(sport_type)}")
            print(f"Bytes: {sport_type.encode('utf-8')}")
            print(f"Repr: {repr(sport_type)}")

            # Сравним с разными вариантами
            variants = ['пла', 'плавание', 'swim']
            for v in variants:
                print(f"\nСравнение с '{v}':")
                print(f"  Equals: {sport_type == v}")
                print(f"  Lower equals: {sport_type.lower() == v.lower()}")
                print(f"  Startswith: {sport_type.lower().startswith(v.lower())}")
                print(f"  In: {v in sport_type.lower()}")

asyncio.run(check())
