"""
Тестирование нового парсера
"""

import asyncio
from competitions.parser import fetch_competitions, SPORT_CODES


async def test_parser():
    """Тестируем парсер"""

    print("="*70)
    print("ТЕСТИРОВАНИЕ ПАРСЕРА")
    print("="*70)

    # Тест 1: Все соревнования
    print("\n1. Получение всех соревнований (первые 10):")
    try:
        competitions = await fetch_competitions(limit=10)
        print(f"   Получено: {len(competitions)} соревнований")

        if competitions:
            comp = competitions[0]
            print(f"\n   Пример первого соревнования:")
            print(f"   ID: {comp['id']}")
            print(f"   Название: {comp['title']}")
            print(f"   Город: {comp['city']}")
            print(f"   Место: {comp['place']}")
            print(f"   Дата начала: {comp['begin_date']}")
            print(f"   Дата окончания: {comp['end_date']}")
            print(f"   Спорт: {comp['sport_code']}")
            print(f"   Участников: {comp['participants_count']}")
            print(f"   URL: {comp['url']}")
            print(f"   Дистанции:")
            for dist in comp['distances'][:3]:
                print(f"      - {dist['name']}: {dist['distance']} км")

    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

    # Тест 2: Фильтр по городу
    print("\n2. Фильтр по городу (Москва):")
    try:
        competitions = await fetch_competitions(city="Москва", limit=5)
        print(f"   Получено: {len(competitions)} соревнований в Москве")

        for i, comp in enumerate(competitions[:3], 1):
            print(f"   {i}. {comp['title']} - {comp['city']}")

    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

    # Тест 3: Фильтр по виду спорта
    print("\n3. Фильтр по виду спорта (Бег):")
    try:
        competitions = await fetch_competitions(sport="run", limit=5)
        print(f"   Получено: {len(competitions)} беговых соревнований")

        for i, comp in enumerate(competitions[:3], 1):
            print(f"   {i}. {comp['title']} - {comp['sport_code']}")

    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

    # Тест 4: Комбинированный фильтр
    print("\n4. Комбинированный фильтр (Москва + Бег):")
    try:
        competitions = await fetch_competitions(city="Москва", sport="run", limit=5)
        print(f"   Получено: {len(competitions)} беговых соревнований в Москве")

        for i, comp in enumerate(competitions[:3], 1):
            print(f"   {i}. {comp['title']}")
            print(f"      Место: {comp['place']}")
            print(f"      Дата: {comp['begin_date']}")

    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

    print("\n" + "="*70)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(test_parser())
