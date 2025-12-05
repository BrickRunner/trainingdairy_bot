"""
Тест фильтра велоспорта
"""

import asyncio
import logging
from datetime import datetime
from competitions.parser import fetch_competitions, matches_sport_type

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')

async def main():
    print("="*80)
    print("ТЕСТ ФИЛЬТРА ВЕЛОСПОРТА")
    print("="*80)

    # Получаем события с фильтром "велоспорт"
    result_bike = await fetch_competitions(sport="bike", period_months=1, limit=10)

    print(f"\nНайдено событий (велоспорт): {len(result_bike)}\n")

    if result_bike:
        for i, comp in enumerate(result_bike, 1):
            bd = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
            print(f"\n{i}. {bd.strftime('%d.%m.%Y')} - {comp['title']}")
            print(f"   sport_code: {comp.get('sport_code')}")
            print(f"   city: {comp.get('city')}")

            # Показываем дистанции
            distances = comp.get('distances', [])
            if distances:
                print(f"   Дистанции ({len(distances)}):")
                for d in distances[:5]:
                    print(f"      - {d.get('name', 'N/A')} | sport: {d.get('sport', 'N/A')} | code: {d.get('sport_code', 'N/A')}")

    # Также проверим события с фильтром "бег"
    print("\n" + "="*80)
    print("ДЛЯ СРАВНЕНИЯ: СОБЫТИЯ С БЕГОМ")
    print("="*80)

    result_run = await fetch_competitions(sport="run", period_months=1, limit=5)
    print(f"\nНайдено событий (бег): {len(result_run)}\n")

    if result_run:
        for i, comp in enumerate(result_run[:3], 1):
            bd = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
            print(f"\n{i}. {bd.strftime('%d.%m.%Y')} - {comp['title']}")
            print(f"   sport_code: {comp.get('sport_code')}")

asyncio.run(main())
