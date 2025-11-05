import asyncio
from competitions.search_queries import search_competitions_by_city_and_month

async def test():
    # Test search for Moscow November 2025
    results = await search_competitions_by_city_and_month('Москва', '2025-11')
    print(f'Found {len(results)} competitions for Москва 2025-11')
    for comp in results[:5]:
        print(f"  - {comp['name']} on {comp['date']}")

asyncio.run(test())
