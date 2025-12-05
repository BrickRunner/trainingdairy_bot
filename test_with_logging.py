"""
Тест с логированием
"""

import asyncio
import logging
from datetime import datetime, timedelta
from competitions.parser import fetch_competitions

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test():
    print("="*80)
    print("ТЕСТ С ЛОГИРОВАНИЕМ: период 1 месяц")
    print("="*80)

    now = datetime.now()
    end_date = now + timedelta(days=30)

    print(f"\nТекущая дата: {now.strftime('%d.%m.%Y')}")
    print(f"Конечная дата периода: {end_date.strftime('%d.%m.%Y')}")
    print("\nЗапускаем получение соревнований...\n")

    comps = await fetch_competitions(city=None, sport=None, limit=1000, period_months=1)

    print(f"\n{'='*80}")
    print(f"РЕЗУЛЬТАТ: Получено {len(comps)} соревнований")
    print(f"{'='*80}")

    if comps:
        # Проверяем первые и последние
        print("\nПервые 3:")
        for i, comp in enumerate(comps[:3], 1):
            begin_date = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
            date_str = begin_date.strftime('%d.%m.%Y')
            print(f"  {i}. {date_str} - {comp['title'][:50]}")

        print("\nПоследние 3:")
        for i, comp in enumerate(comps[-3:], len(comps) - 2):
            begin_date = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
            date_str = begin_date.strftime('%d.%m.%Y')
            is_within = "✓" if begin_date <= end_date else "✗ ОШИБКА"
            print(f"  {is_within} {i}. {date_str} - {comp['title'][:50]}")

        # Проверяем что все в пределах периода
        beyond_period = [c for c in comps if datetime.fromisoformat(c['begin_date'].replace('Z', '+00:00')) > end_date]

        if beyond_period:
            print(f"\n✗ НАЙДЕНО {len(beyond_period)} соревнований ЗА ПРЕДЕЛАМИ ПЕРИОДА:")
            for comp in beyond_period[:5]:
                begin_date = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
                date_str = begin_date.strftime('%d.%m.%Y')
                print(f"  - {date_str} - {comp['title'][:50]}")
        else:
            print("\n✓ ВСЕ СОРЕВНОВАНИЯ В ПРЕДЕЛАХ ПЕРИОДА!")

if __name__ == "__main__":
    asyncio.run(test())
