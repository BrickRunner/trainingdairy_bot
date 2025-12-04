"""
Отладка фильтрации по периоду
"""

import asyncio
from datetime import datetime, timedelta
from competitions.parser import fetch_competitions


async def test_period_debug():
    """Тест с отладочной информацией"""

    print("="*70)
    print("ОТЛАДКА ФИЛЬТРАЦИИ ПО ПЕРИОДУ")
    print("="*70)

    now = datetime.now()
    print(f"\nТекущая дата: {now.strftime('%d.%m.%Y %H:%M:%S')}")

    # Тест 1: 1 месяц (30 дней)
    print("\n" + "="*70)
    print("ТЕСТ: 1 месяц (30 дней)")
    print("="*70)

    end_date_1m = now + timedelta(days=30)
    print(f"Конечная дата фильтра: {end_date_1m.strftime('%d.%m.%Y %H:%M:%S')}")

    try:
        comps = await fetch_competitions(city=None, sport=None, limit=50, period_months=1)
        print(f"\nНайдено соревнований: {len(comps)}")

        if comps:
            print("\nПервые 10 соревнований:")
            for i, comp in enumerate(comps[:10], 1):
                begin_date = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
                date_str = begin_date.strftime('%d.%m.%Y')
                print(f"{i}. {date_str} - {comp['title'][:50]}")
                print(f"   Город: {comp['city']}")

            # Проверяем последнее соревнование
            last_comp = comps[-1]
            last_date = datetime.fromisoformat(last_comp['begin_date'].replace('Z', '+00:00'))
            print(f"\nПоследнее соревнование:")
            print(f"Дата: {last_date.strftime('%d.%m.%Y')}")
            print(f"Название: {last_comp['title'][:50]}")

            # Проверяем, что последнее соревнование не позже конечной даты
            if last_date <= end_date_1m:
                print(f"✓ Фильтр работает корректно")
            else:
                print(f"✗ ОШИБКА: Последнее соревнование ({last_date.strftime('%d.%m.%Y')}) позже конечной даты ({end_date_1m.strftime('%d.%m.%Y')})")

    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

    # Тест 2: Без фильтра
    print("\n" + "="*70)
    print("ТЕСТ: Без фильтра по периоду")
    print("="*70)

    try:
        comps_all = await fetch_competitions(city=None, sport=None, limit=100, period_months=None)
        print(f"\nНайдено соревнований без фильтра: {len(comps_all)}")

        if comps_all:
            print("\nПервые 10 соревнований:")
            for i, comp in enumerate(comps_all[:10], 1):
                begin_date = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
                date_str = begin_date.strftime('%d.%m.%Y')
                print(f"{i}. {date_str} - {comp['title'][:50]}")

    except Exception as e:
        print(f"Ошибка: {e}")

    print("\n" + "="*70)
    print("ОТЛАДКА ЗАВЕРШЕНА")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(test_period_debug())
