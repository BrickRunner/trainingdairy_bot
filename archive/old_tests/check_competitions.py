"""
Script to check competitions in database
"""
import asyncio
import aiosqlite
import os

async def main():
    db = await aiosqlite.connect(os.getenv('DB_PATH', 'bot_data.db'))
    db.row_factory = aiosqlite.Row

    # Check all competitions
    cursor = await db.execute(
        'SELECT id, name, city, is_official, created_by, source_url FROM competitions ORDER BY id DESC LIMIT 20'
    )
    rows = await cursor.fetchall()

    print('\n=== COMPETITIONS IN DATABASE ===\n')
    for row in rows:
        print(f"ID: {row[0]}")
        print(f"  Name: {row[1][:60]}")
        print(f"  City: {row[2]}")
        print(f"  is_official: {row[3]}")
        print(f"  created_by: {row[4]}")
        print(f"  source: {row[5]}")
        print()

    # Check official count
    cursor = await db.execute('SELECT COUNT(*) FROM competitions WHERE is_official = 1')
    official_count = (await cursor.fetchone())[0]

    # Check user-created count
    cursor = await db.execute('SELECT COUNT(*) FROM competitions WHERE is_official = 0')
    user_count = (await cursor.fetchone())[0]

    print(f'Official competitions (is_official=1): {official_count}')
    print(f'User-created competitions (is_official=0): {user_count}')

    await db.close()

if __name__ == '__main__':
    asyncio.run(main())
