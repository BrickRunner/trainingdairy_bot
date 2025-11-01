import asyncio
import aiosqlite
import os

async def check():
    db = await aiosqlite.connect(os.getenv('DB_PATH', 'bot_data.db'))
    cursor = await db.execute('PRAGMA table_info(user_settings)')
    columns = await cursor.fetchall()
    print("User settings columns:")
    for col in columns:
        print(f"  {col[1]} - {col[2]}")
    await db.close()

asyncio.run(check())
