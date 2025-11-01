import asyncio
import aiosqlite
import os

async def test():
    db = await aiosqlite.connect(os.getenv('DB_PATH', 'bot_data.db'))
    db.row_factory = aiosqlite.Row

    city = 'Москва'
    year, month = '2025', '11'
    start_date = f"{year}-{month}-01"
    end_date = f"{year}-{int(month) + 1:02d}-01"

    print(f"Searching for: city={city}, start={start_date}, end={end_date}")

    query = """
        SELECT * FROM competitions
        WHERE city = ?
          AND date >= ?
          AND date < ?
          AND status = 'upcoming'
          AND is_official = 1
        ORDER BY date ASC
        LIMIT 50
    """

    cursor = await db.execute(query, (city, start_date, end_date))
    rows = await cursor.fetchall()

    print(f"\nFound {len(rows)} competitions")
    for row in rows[:10]:
        comp = dict(row)
        print(f"  - {comp['name']} on {comp['date']} in {comp['city']}")

    # Check without filters
    cursor = await db.execute("SELECT COUNT(*) FROM competitions WHERE city = 'Москва' AND is_official = 1")
    total = (await cursor.fetchone())[0]
    print(f"\nTotal Москва competitions (no date filter): {total}")

    # Check November dates
    cursor = await db.execute("SELECT name, date FROM competitions WHERE date >= '2025-11-01' AND date < '2025-12-01' LIMIT 10")
    nov_comps = await cursor.fetchall()
    print(f"\nNovember competitions (all cities): {len(nov_comps)}")
    for comp in nov_comps:
        print(f"  - {comp[0]} on {comp[1]}")

    await db.close()

asyncio.run(test())
