"""
Тест fetch_competitions для плавания
"""

import asyncio
import logging
from datetime import datetime
from competitions.parser import fetch_competitions

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

async def test():
    print("="*80)
    print("ТЕСТ fetch_competitions ДЛЯ ПЛАВАНИЯ")
    print("="*80)

    # Точно такие же параметры как в боте
    city = None  # Все города
    sport = "swim"
    period_months = 1  # 1 месяц

    print(f"\nПараметры:")
    print(f"  city: {city}")
    print(f"  sport: {sport}")
    print(f"  period_months: {period_months}")
    print(f"  limit: 1000")
    print("\nЗапускаем fetch_competitions...\n")

    comps = await fetch_competitions(
        city=city,
        sport=sport,
        limit=1000,
        period_months=period_months
    )

    print(f"\n{'='*80}")
    print(f"РЕЗУЛЬТАТ: Найдено {len(comps)} соревнований с плаванием")
    print(f"{'='*80}")

    if comps:
        print("\nВсе соревнования:")
        for i, comp in enumerate(comps, 1):
            begin_date = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
            date_str = begin_date.strftime('%d.%m.%Y')
            print(f"{i}. {date_str} - {comp['title']}")
            print(f"   Город: {comp['city']}")
            print(f"   Код спорта: {comp.get('sport_code', 'N/A')}")
    else:
        print("\n⚠ СОРЕВНОВАНИЯ НЕ НАЙДЕНЫ!")
        print("\nПроверим без фильтра по виду спорта:")

        comps_all = await fetch_competitions(
            city=city,
            sport="all",
            limit=100,
            period_months=period_months
        )

        print(f"Всего соревнований в этом месяце: {len(comps_all)}")

        # Ищем плавание вручную
        swim_found = []
        for comp in comps_all:
            title = comp['title'].lower()
            if 'плав' in title or 'swim' in title:
                swim_found.append(comp)

        if swim_found:
            print(f"\nНайдено соревнований со словом 'плав' или 'swim' в названии: {len(swim_found)}")
            for comp in swim_found:
                begin_date = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
                date_str = begin_date.strftime('%d.%m.%Y')
                print(f"  - {date_str} - {comp['title']}")
                print(f"    Код спорта: {comp.get('sport_code', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(test())
