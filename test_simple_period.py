"""
Простой тест периода
"""

import asyncio
from datetime import datetime, timedelta
from competitions.parser import fetch_competitions


async def test():
    print("Тестируем период 1 месяц (30 дней)")
    print("="*80)

    now = datetime.now()
    end_date = now + timedelta(days=30)

    print(f"Сегодня: {now.strftime('%d.%m.%Y')}")
    print(f"Конец периода: {end_date.strftime('%d.%m.%Y')}")
    print()

    comps = await fetch_competitions(city=None, sport=None, limit=1000, period_months=1)

    print(f"Найдено: {len(comps)} соревнований")
    print()

    if comps:
        # Проверяем все даты
        print("Проверка всех дат:")
        beyond_count = 0

        for i, comp in enumerate(comps, 1):
            begin_date = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))

            if begin_date > end_date:
                beyond_count += 1
                date_str = begin_date.strftime('%d.%m.%Y')
                print(f"  ✗ {i}. {date_str} - ЗА ПРЕДЕЛАМИ ПЕРИОДА - {comp['title'][:50]}")

        if beyond_count == 0:
            print("  ✓ Все соревнования в пределах периода!")
        else:
            print(f"\n✗ ОШИБКА: {beyond_count} соревнований за пределами периода!")

        # Показываем последние 5
        print(f"\nПоследние 5 соревнований:")
        for i, comp in enumerate(comps[-5:], len(comps) - 4):
            begin_date = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
            date_str = begin_date.strftime('%d.%m.%Y')
            status = "✓" if begin_date <= end_date else "✗"
            print(f"  {status} {i}. {date_str} - {comp['title'][:50]}")


if __name__ == "__main__":
    asyncio.run(test())
