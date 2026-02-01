"""
Найти соревнование "11111"
"""
import asyncio
import aiosqlite

async def find():
    async with aiosqlite.connect('database.sqlite') as db:
        db.row_factory = aiosqlite.Row

        # Ищем соревнование
        cursor = await db.execute('''
            SELECT id, name, sport_type
            FROM competitions
            WHERE name LIKE '%11111%'
        ''')
        rows = await cursor.fetchall()

        print("Соревнования с '11111':")
        for row in rows:
            print(f"  ID: {row['id']}, Name: {row['name']}, Sport: {row['sport_type']}")

        # Ищем последний результат этого пользователя
        user_id = 1611441720
        cursor = await db.execute('''
            SELECT
                cp.competition_id,
                c.name,
                c.sport_type,
                cp.distance,
                cp.finish_time,
                cp.qualification,
                cp.result_added_at
            FROM competition_participants cp
            JOIN competitions c ON c.id = cp.competition_id
            WHERE cp.user_id = ?
            ORDER BY cp.result_added_at DESC
            LIMIT 5
        ''', (user_id,))
        rows = await cursor.fetchall()

        print(f"\nПоследние 5 результатов пользователя {user_id}:")
        for row in rows:
            print(f"  Comp ID: {row['competition_id']}, {row['name']} ({row['sport_type']})")
            print(f"    Distance: {row['distance']}km, Time: {row['finish_time']}, Qual: {row['qualification']}")
            print(f"    Added: {row['result_added_at']}")

asyncio.run(find())
