"""
Тестирование фильтрации по городу на стороне бота
"""

import asyncio
from competitions.parser import fetch_competitions


async def test_filtering():
    """Тест фильтрации"""

    print("="*70)
    print("ТЕСТИРОВАНИЕ ФИЛЬТРАЦИИ ПО ГОРОДУ")
    print("="*70)

    # Тест 1: Москва
    print("\n1. Фильтр: Москва")
    try:
        comps = await fetch_competitions(city="Москва", limit=10)
        print(f"   Найдено: {len(comps)} соревнований")
        for i, comp in enumerate(comps[:5], 1):
            print(f"   {i}. {comp['title'][:50]}")
            print(f"      Город: {comp['city']}")
            print(f"      Место: {comp['place']}")
    except Exception as e:
        print(f"   Ошибка: {e}")

    # Тест 2: Санкт-Петербург
    print("\n2. Фильтр: Санкт-Петербург")
    try:
        comps = await fetch_competitions(city="Санкт-Петербург", limit=10)
        print(f"   Найдено: {len(comps)} соревнований")
        for i, comp in enumerate(comps[:5], 1):
            print(f"   {i}. {comp['title'][:50]}")
            print(f"      Город: {comp['city']}")
    except Exception as e:
        print(f"   Ошибка: {e}")

    # Тест 3: Все города
    print("\n3. Без фильтра (все города)")
    try:
        comps = await fetch_competitions(limit=10)
        print(f"   Найдено: {len(comps)} соревнований")
        cities = set()
        for comp in comps:
            cities.add(comp['city'])
        print(f"   Города: {', '.join(list(cities)[:5])}")
    except Exception as e:
        print(f"   Ошибка: {e}")

    print("\n" + "="*70)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(test_filtering())
