"""
Финальный тест работы модуля соревнований
"""

import asyncio
from competitions.parser import fetch_competitions


async def test_competitions():
    """Тест получения соревнований"""

    print("="*70)
    print("ТЕСТ МОДУЛЯ СОРЕВНОВАНИЙ")
    print("="*70)

    # Тест 1: Все соревнования, все виды спорта
    print("\n1. Все города, все виды спорта:")
    try:
        comps = await fetch_competitions(city=None, sport=None, limit=50)
        print(f"   Найдено: {len(comps)} соревнований")
        if comps:
            from datetime import datetime
            for i, comp in enumerate(comps[:5], 1):
                begin_date = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
                date_str = begin_date.strftime('%d.%m.%Y')
                print(f"   {i}. {date_str} - {comp['title'][:50]}")
                print(f"      Город: {comp['city']}")
    except Exception as e:
        print(f"   ✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()

    # Тест 2: Москва
    print("\n2. Москва, все виды спорта:")
    try:
        comps = await fetch_competitions(city="Москва", sport=None, limit=50)
        print(f"   Найдено: {len(comps)} соревнований")
        if comps:
            from datetime import datetime
            for i, comp in enumerate(comps[:5], 1):
                begin_date = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
                date_str = begin_date.strftime('%d.%m.%Y')
                print(f"   {i}. {date_str} - {comp['title'][:50]}")
                print(f"      Город: {comp['city']}")
    except Exception as e:
        print(f"   ✗ Ошибка: {e}")

    # Тест 3: Бег
    print("\n3. Все города, бег:")
    try:
        comps = await fetch_competitions(city=None, sport="run", limit=50)
        print(f"   Найдено: {len(comps)} соревнований")
        if comps:
            from datetime import datetime
            for i, comp in enumerate(comps[:5], 1):
                begin_date = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
                date_str = begin_date.strftime('%d.%m.%Y')
                print(f"   {i}. {date_str} - {comp['title'][:50]}")
                print(f"      Спорт: {comp['sport_type']}")
    except Exception as e:
        print(f"   ✗ Ошибка: {e}")

    print("\n" + "="*70)
    print("ТЕСТ ЗАВЕРШЕН")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(test_competitions())
