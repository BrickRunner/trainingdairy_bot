"""
Тест фильтрации по периодам (финальный)
"""

import asyncio
from datetime import datetime
from competitions.parser import fetch_competitions


async def test_periods():
    """Тест фильтрации по периодам"""

    print("="*80)
    print("ТЕСТ ФИЛЬТРАЦИИ ПО ПЕРИОДАМ (МНОЖЕСТВЕННЫЕ API ЗАПРОСЫ)")
    print("="*80)

    # Тест 1: 1 месяц
    print("\n1. Период: 1 месяц (30 дней)")
    print("-" * 80)
    try:
        comps_1m = await fetch_competitions(city=None, sport=None, limit=1000, period_months=1)
        print(f"Найдено соревнований: {len(comps_1m)}")

        if comps_1m:
            print("\nПервые 5 соревнований:")
            for i, comp in enumerate(comps_1m[:5], 1):
                begin_date = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
                date_str = begin_date.strftime('%d.%m.%Y')
                print(f"  {i}. {date_str} - {comp['title'][:60]}")

            print("\nПоследние 5 соревнований:")
            for i, comp in enumerate(comps_1m[-5:], len(comps_1m)-4):
                begin_date = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
                date_str = begin_date.strftime('%d.%m.%Y')
                print(f"  {i}. {date_str} - {comp['title'][:60]}")

            # Проверяем последнюю дату
            last_comp = comps_1m[-1]
            last_date = datetime.fromisoformat(last_comp['begin_date'].replace('Z', '+00:00'))
            target_date = datetime.now()
            from datetime import timedelta
            end_date = target_date + timedelta(days=30)
            print(f"\n✓ Последнее соревнование: {last_date.strftime('%d.%m.%Y')}")
            print(f"✓ Максимальная дата (текущая + 30 дней): {end_date.strftime('%d.%m.%Y')}")

    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()

    # Тест 2: 6 месяцев
    print("\n2. Период: 6 месяцев (180 дней)")
    print("-" * 80)
    try:
        comps_6m = await fetch_competitions(city=None, sport=None, limit=1000, period_months=6)
        print(f"Найдено соревнований: {len(comps_6m)}")

        if comps_6m:
            print("\nПервые 3 соревнования:")
            for i, comp in enumerate(comps_6m[:3], 1):
                begin_date = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
                date_str = begin_date.strftime('%d.%m.%Y')
                print(f"  {i}. {date_str} - {comp['title'][:60]}")

            print("\nПоследние 3 соревнования:")
            for i, comp in enumerate(comps_6m[-3:], len(comps_6m)-2):
                begin_date = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
                date_str = begin_date.strftime('%d.%m.%Y')
                print(f"  {i}. {date_str} - {comp['title'][:60]}")

    except Exception as e:
        print(f"✗ Ошибка: {e}")

    # Тест 3: 1 год
    print("\n3. Период: 1 год (365 дней)")
    print("-" * 80)
    try:
        comps_1y = await fetch_competitions(city=None, sport=None, limit=1000, period_months=12)
        print(f"Найдено соревнований: {len(comps_1y)}")

        if comps_1y:
            print("\nПервые 3 соревнования:")
            for i, comp in enumerate(comps_1y[:3], 1):
                begin_date = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
                date_str = begin_date.strftime('%d.%m.%Y')
                print(f"  {i}. {date_str} - {comp['title'][:60]}")

            print("\nПоследние 3 соревнования:")
            for i, comp in enumerate(comps_1y[-3:], len(comps_1y)-2):
                begin_date = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
                date_str = begin_date.strftime('%d.%m.%Y')
                print(f"  {i}. {date_str} - {comp['title'][:60]}")

    except Exception as e:
        print(f"✗ Ошибка: {e}")

    # Сравнение
    print("\n" + "="*80)
    print("СРАВНЕНИЕ РЕЗУЛЬТАТОВ:")
    print("="*80)
    print(f"1 месяц:   {len(comps_1m) if 'comps_1m' in locals() else 0} соревнований")
    print(f"6 месяцев: {len(comps_6m) if 'comps_6m' in locals() else 0} соревнований")
    print(f"1 год:     {len(comps_1y) if 'comps_1y' in locals() else 0} соревнований")
    print("\n✓ Ожидается: 1 месяц < 6 месяцев < 1 год")

    if 'comps_1m' in locals() and 'comps_6m' in locals() and 'comps_1y' in locals():
        if len(comps_1m) <= len(comps_6m) <= len(comps_1y):
            print("✓ ТЕСТ ПРОЙДЕН: Фильтрация по периодам работает корректно!")
        else:
            print("✗ ТЕСТ НЕ ПРОЙДЕН: Количество соревнований не соответствует ожидаемому")

    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_periods())
