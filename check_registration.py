"""
Проверка регистраций пользователя
"""
import asyncio
import aiosqlite

async def check():
    user_id = 1611441720

    async with aiosqlite.connect('database.sqlite') as db:
        db.row_factory = aiosqlite.Row

        # Проверим регистрации
        cursor = await db.execute('''
            SELECT cp.competition_id, cp.distance, c.name, c.sport_type
            FROM competition_participants cp
            JOIN competitions c ON c.id = cp.competition_id
            WHERE cp.user_id = ?
            ORDER BY cp.competition_id
            LIMIT 10
        ''', (user_id,))
        rows = await cursor.fetchall()

        print(f"Регистрации пользователя {user_id}:")
        for row in rows:
            print(f"  ID: {row['competition_id']}, {row['name']} ({row['sport_type']}), дистанция: {row['distance']}km")

        # Проверим соревнования
        cursor = await db.execute('''
            SELECT id, name, sport_type
            FROM competitions
            ORDER BY id
            LIMIT 10
        ''')
        rows = await cursor.fetchall()

        print(f"\nСоревнования:")
        for row in rows:
            print(f"  ID: {row['id']}, {row['name']} ({row['sport_type']})")

asyncio.run(check())
