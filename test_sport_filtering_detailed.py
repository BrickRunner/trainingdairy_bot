"""
Детальный тест для проверки фильтрации по видам спорта
"""
import asyncio
import logging

logging.basicConfig(level=logging.DEBUG)

from competitions.competitions_fetcher import fetch_all_competitions

async def test_detailed():
    """Детальный тест"""

    print("\n=== Бег (run) ===")
    run_comps = await fetch_all_competitions(
        city=None,
        sport="run",
        limit=50,
        period_months=1,
        service="RussiaRunning"  # Только RussiaRunning для простоты
    )
    print(f"\nНайдено: {len(run_comps)}")
    for comp in run_comps[:10]:
        print(f"  {comp['title'][:50]} | sport_code: {comp.get('sport_code', 'N/A')}")

    print("\n=== Плавание (swim) ===")
    swim_comps = await fetch_all_competitions(
        city=None,
        sport="swim",
        limit=50,
        period_months=1,
        service="RussiaRunning"
    )
    print(f"\nНайдено: {len(swim_comps)}")
    for comp in swim_comps[:10]:
        print(f"  {comp['title'][:50]} | sport_code: {comp.get('sport_code', 'N/A')}")

    print("\n=== Велоспорт (bike) ===")
    bike_comps = await fetch_all_competitions(
        city=None,
        sport="bike",
        limit=50,
        period_months=1,
        service="RussiaRunning"
    )
    print(f"\nНайдено: {len(bike_comps)}")
    for comp in bike_comps[:10]:
        print(f"  {comp['title'][:50]} | sport_code: {comp.get('sport_code', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(test_detailed())
