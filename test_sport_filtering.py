"""
Тест для проверки фильтрации по видам спорта
"""
import asyncio
import logging

logging.basicConfig(level=logging.INFO)

from competitions.competitions_fetcher import fetch_all_competitions

async def test_sport_filtering():
    """Тест фильтрации по видам спорта"""

    print("\n=== ТЕСТ 1: Все виды спорта ===")
    all_sports = await fetch_all_competitions(
        city=None,
        sport="all",
        limit=20,
        period_months=1,
        service="all"
    )
    print(f"Найдено всего: {len(all_sports)} соревнований")
    for comp in all_sports[:5]:
        print(f"  - {comp['title']} | Спорт: {comp.get('sport_code', 'N/A')} | Сервис: {comp.get('service', 'N/A')}")

    print("\n=== ТЕСТ 2: Только Бег (run) ===")
    run_comps = await fetch_all_competitions(
        city=None,
        sport="run",
        limit=20,
        period_months=1,
        service="all"
    )
    print(f"Найдено беговых: {len(run_comps)} соревнований")
    for comp in run_comps[:5]:
        print(f"  - {comp['title']} | Спорт: {comp.get('sport_code', 'N/A')} | Сервис: {comp.get('service', 'N/A')}")

    print("\n=== ТЕСТ 3: Только Плавание (swim) ===")
    swim_comps = await fetch_all_competitions(
        city=None,
        sport="swim",
        limit=20,
        period_months=1,
        service="all"
    )
    print(f"Найдено плавательных: {len(swim_comps)} соревнований")
    for comp in swim_comps[:5]:
        print(f"  - {comp['title']} | Спорт: {comp.get('sport_code', 'N/A')} | Сервис: {comp.get('service', 'N/A')}")

    print("\n=== ТЕСТ 4: Только Велоспорт (bike) ===")
    bike_comps = await fetch_all_competitions(
        city=None,
        sport="bike",
        limit=20,
        period_months=1,
        service="all"
    )
    print(f"Найдено велосипедных: {len(bike_comps)} соревнований")
    for comp in bike_comps[:5]:
        print(f"  - {comp['title']} | Спорт: {comp.get('sport_code', 'N/A')} | Сервис: {comp.get('service', 'N/A')}")

    print("\n=== ПРОВЕРКА ===")
    print(f"Все виды: {len(all_sports)}")
    print(f"Бег: {len(run_comps)}")
    print(f"Плавание: {len(swim_comps)}")
    print(f"Велоспорт: {len(bike_comps)}")

    # Проверяем что фильтрация работает
    if len(run_comps) < len(all_sports):
        print("✓ Фильтрация по бегу работает")
    else:
        print("✗ Фильтрация по бегу НЕ работает")

    if len(swim_comps) < len(all_sports):
        print("✓ Фильтрация по плаванию работает")
    else:
        print("✗ Фильтрация по плаванию НЕ работает")

    if len(bike_comps) < len(all_sports):
        print("✓ Фильтрация по велоспорту работает")
    else:
        print("✗ Фильтрация по велоспорту НЕ работает")

if __name__ == "__main__":
    asyncio.run(test_sport_filtering())
