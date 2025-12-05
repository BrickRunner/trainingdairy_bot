"""
Тест фильтрации по видам спорта
"""

import asyncio
from competitions.parser import fetch_competitions


async def test():
    print("="*80)
    print("ТЕСТ ФИЛЬТРАЦИИ ПО ВИДАМ СПОРТА")
    print("="*80)

    # Тест 1: Бег
    print("\n1. Фильтр: Бег (run)")
    print("-"*80)
    comps_run = await fetch_competitions(city=None, sport="run", limit=100, period_months=6)
    print(f"Найдено: {len(comps_run)} соревнований")

    if comps_run:
        print("Первые 5:")
        for i, comp in enumerate(comps_run[:5], 1):
            print(f"  {i}. {comp['title'][:50]}")
            print(f"     Код спорта: {comp.get('sport_code', 'N/A')}")

    # Тест 2: Плавание
    print("\n2. Фильтр: Плавание (swim)")
    print("-"*80)
    comps_swim = await fetch_competitions(city=None, sport="swim", limit=100, period_months=6)
    print(f"Найдено: {len(comps_swim)} соревнований")

    if comps_swim:
        print("Первые 5:")
        for i, comp in enumerate(comps_swim[:5], 1):
            print(f"  {i}. {comp['title'][:50]}")
            print(f"     Код спорта: {comp.get('sport_code', 'N/A')}")

    # Тест 3: Велоспорт
    print("\n3. Фильтр: Велоспорт (bike)")
    print("-"*80)
    comps_bike = await fetch_competitions(city=None, sport="bike", limit=100, period_months=6)
    print(f"Найдено: {len(comps_bike)} соревнований")

    if comps_bike:
        print("Первые 5:")
        for i, comp in enumerate(comps_bike[:5], 1):
            print(f"  {i}. {comp['title'][:50]}")
            print(f"     Код спорта: {comp.get('sport_code', 'N/A')}")

    # Тест 4: Все виды спорта
    print("\n4. Фильтр: Все виды спорта (all)")
    print("-"*80)
    comps_all = await fetch_competitions(city=None, sport="all", limit=100, period_months=6)
    print(f"Найдено: {len(comps_all)} соревнований")

    print("\n" + "="*80)
    print("ИТОГИ:")
    print("="*80)
    print(f"Бег:              {len(comps_run)}")
    print(f"Плавание:         {len(comps_swim)}")
    print(f"Велоспорт:        {len(comps_bike)}")
    print(f"Все виды спорта:  {len(comps_all)}")


if __name__ == "__main__":
    asyncio.run(test())
