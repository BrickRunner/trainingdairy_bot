import asyncio
import aiosqlite
import os

async def check():
    db = await aiosqlite.connect(os.getenv('DB_PATH', 'bot_data.db'))

    # Count official competitions
    cursor = await db.execute('SELECT COUNT(*) FROM competitions WHERE is_official = 1')
    count = (await cursor.fetchone())[0]
    print(f'Official competitions in DB: {count}')

    # Show sample competitions
    cursor = await db.execute('SELECT name, city, date FROM competitions WHERE is_official = 1 ORDER BY date LIMIT 10')
    rows = await cursor.fetchall()
    print('\nSample competitions:')
    for row in rows:
        print(f'  {row[0][:50]} - {row[1]} - {row[2]}')

    await db.close()

asyncio.run(check())
