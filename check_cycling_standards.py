import asyncio
import aiosqlite

async def check():
    async with aiosqlite.connect('database.sqlite') as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM cycling_standards LIMIT 10') as cursor:
            rows = await cursor.fetchall()
            print('Cycling standards in DB:')
            print('-' * 80)
            for row in rows:
                print(dict(row))

asyncio.run(check())
