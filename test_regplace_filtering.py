"""
Тест фильтрации reg.place по виду спорта
"""
import asyncio
import logging
from competitions.regplace_parser import fetch_competitions

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_regplace_filtering():
    """Тестируем фильтрацию reg.place"""

    print("=" * 80)
    print("ТЕСТ ФИЛЬТРАЦИИ REG.PLACE ПО ВИДАМ СПОРТА")
    print("=" * 80)

    # Тест 1: Бег
    print("\n1. Тест фильтрации по БЕГУ (sport='run'):")
    print("-" * 80)
    run_comps = await fetch_competitions(
        city=None,
        sport="run",
        limit=5,
        period_months=12
    )
    print(f"Найдено {len(run_comps)} беговых соревнований:")
    for comp in run_comps:
        print(f"  ✓ {comp.get('title')} - sport_code='{comp.get('sport_code')}', city={comp.get('city')}")
        print(f"    Дистанций: {len(comp.get('distances', []))}")

    # Тест 2: Велоспорт
    print("\n2. Тест фильтрации по ВЕЛОСПОРТУ (sport='bike'):")
    print("-" * 80)
    bike_comps = await fetch_competitions(
        city=None,
        sport="bike",
        limit=5,
        period_months=12
    )
    print(f"Найдено {len(bike_comps)} велосоревнований:")
    for comp in bike_comps:
        print(f"  ✓ {comp.get('title')} - sport_code='{comp.get('sport_code')}', city={comp.get('city')}")
        print(f"    Дистанций: {len(comp.get('distances', []))}")

    # Тест 3: Плавание
    print("\n3. Тест фильтрации по ПЛАВАНИЮ (sport='swim'):")
    print("-" * 80)
    swim_comps = await fetch_competitions(
        city=None,
        sport="swim",
        limit=5,
        period_months=12
    )
    print(f"Найдено {len(swim_comps)} заплывов:")
    for comp in swim_comps:
        print(f"  ✓ {comp.get('title')} - sport_code='{comp.get('sport_code')}', city={comp.get('city')}")
        print(f"    Дистанций: {len(comp.get('distances', []))}")

    # Тест 4: Все виды спорта
    print("\n4. Тест БЕЗ фильтрации (sport=None):")
    print("-" * 80)
    all_comps = await fetch_competitions(
        city=None,
        sport=None,
        limit=10,
        period_months=12
    )
    print(f"Найдено {len(all_comps)} соревнований:")
    sport_counts = {}
    for comp in all_comps:
        sport_code = comp.get('sport_code', 'unknown')
        sport_counts[sport_code] = sport_counts.get(sport_code, 0) + 1
        print(f"  • {comp.get('title')} - sport_code='{sport_code}'")

    print(f"\nСтатистика по видам спорта:")
    for sport, count in sport_counts.items():
        print(f"  {sport}: {count}")

    # Тест 5: Фильтр по городу
    print("\n5. Тест фильтрации по ГОРОДУ (city='Москва', sport='run'):")
    print("-" * 80)
    moscow_comps = await fetch_competitions(
        city="Москва",
        sport="run",
        limit=5,
        period_months=12
    )
    print(f"Найдено {len(moscow_comps)} беговых соревнований в Москве:")
    for comp in moscow_comps:
        print(f"  ✓ {comp.get('title')} - city={comp.get('city')}, sport={comp.get('sport_code')}")

    print("\n" + "=" * 80)
    print("ТЕСТ ЗАВЕРШЕН")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_regplace_filtering())
