import asyncio
import aiosqlite
import os

async def search_competitions_by_city_and_month(city: str, period: str):
    """Copy of the search function with debug"""
    DB_PATH = os.getenv('DB_PATH', 'bot_data.db')

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        if period == 'all':
            query = """
                SELECT * FROM competitions
                WHERE city = ?
                  AND date >= date('now')
                  AND status = 'upcoming'
                  AND is_official = 1
                ORDER BY date ASC
                LIMIT 50
            """
            params = (city,)
        else:
            year, month = period.split('-')
            start_date = f"{year}-{month}-01"

            if month == '12':
                end_date = f"{int(year) + 1}-01-01"
            else:
                end_date = f"{year}-{int(month) + 1:02d}-01"

            print(f"DEBUG: city={repr(city)}, start_date={start_date}, end_date={end_date}")

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
            params = (city, start_date, end_date)

        print(f"DEBUG: Executing query with params: {params}")

        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            print(f"DEBUG: Found {len(rows)} rows")
            return [dict(row) for row in rows]

async def test():
    results = await search_competitions_by_city_and_month('Москва', '2025-11')
    print(f'\nFinal result: Found {len(results)} competitions')
    for comp in results[:5]:
        print(f"  - {comp['name']} on {comp['date']}")

asyncio.run(test())
