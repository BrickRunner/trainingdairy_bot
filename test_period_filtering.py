"""
Тестирование фильтрации по периоду
"""

import asyncio
from competitions.parser import fetch_competitions


async def test_period_filtering():
    """Тест фильтрации по периоду"""

    print("="*70)
    print("ТЕСТИРОВАНИЕ ФИЛЬТРАЦИИ ПО ПЕРИОДУ")
    print("="*70)

    # Тест 1: 1 месяц
    print("\n1. Фильтр: 1 месяц")
    try:
        comps = await fetch_competitions(city=None, sport=None, limit=50, period_months=1)
        print(f"   Найдено: {len(comps)} соревнований")
        for i, comp in enumerate(comps[:5], 1):
            print(f"   {i}. {comp['title'][:50]}")
            print(f"      Дата начала: {comp['begin_date']}")
    except Exception as e:
        print(f"   Ошибка: {e}")

    # Тест 2: 6 месяцев
    print("\n2. Фильтр: 6 месяцев")
    try:
        comps = await fetch_competitions(city=None, sport=None, limit=50, period_months=6)
        print(f"   Найдено: {len(comps)} соревнований")
        for i, comp in enumerate(comps[:5], 1):
            print(f"   {i}. {comp['title'][:50]}")
            print(f"      Дата начала: {comp['begin_date']}")
    except Exception as e:
        print(f"   Ошибка: {e}")

    # Тест 3: 12 месяцев (1 год)
    print("\n3. Фильтр: 12 месяцев (1 год)")
    try:
        comps = await fetch_competitions(city=None, sport=None, limit=50, period_months=12)
        print(f"   Найдено: {len(comps)} соревнований")
        for i, comp in enumerate(comps[:5], 1):
            print(f"   {i}. {comp['title'][:50]}")
            print(f"      Дата начала: {comp['begin_date']}")
    except Exception as e:
        print(f"   Ошибка: {e}")

    # Тест 4: Без фильтра по периоду
    print("\n4. Без фильтра по периоду")
    try:
        comps = await fetch_competitions(city=None, sport=None, limit=50, period_months=None)
        print(f"   Найдено: {len(comps)} соревнований")
        for i, comp in enumerate(comps[:5], 1):
            print(f"   {i}. {comp['title'][:50]}")
            print(f"      Дата начала: {comp['begin_date']}")
    except Exception as e:
        print(f"   Ошибка: {e}")

    # Тест 5: Москва + 1 месяц
    print("\n5. Фильтр: Москва + 1 месяц")
    try:
        comps = await fetch_competitions(city="Москва", sport=None, limit=50, period_months=1)
        print(f"   Найдено: {len(comps)} соревнований")
        for i, comp in enumerate(comps[:5], 1):
            print(f"   {i}. {comp['title'][:50]}")
            print(f"      Город: {comp['city']}")
            print(f"      Дата начала: {comp['begin_date']}")
    except Exception as e:
        print(f"   Ошибка: {e}")

    print("\n" + "="*70)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(test_period_filtering())
