"""
Проверка текущей даты и логики фильтрации
"""

import asyncio
from datetime import datetime, timezone, timedelta
from competitions.parser import RussiaRunningParser


async def test():
    print("="*80)
    print("ПРОВЕРКА ДАТ И ЛОГИКИ ФИЛЬТРАЦИИ")
    print("="*80)

    # Текущая дата
    now = datetime.now(timezone.utc)
    print(f"\nТекущая дата (UTC): {now.strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"Месяц: {now.month}, День: {now.day}, Год: {now.year}")

    # Конец месяца (логика из parser.py)
    year = now.year
    month = now.month

    if month == 12:
        last_day = 31
    else:
        next_month = datetime(year, month + 1, 1, tzinfo=timezone.utc)
        last_day_date = next_month - timedelta(days=1)
        last_day = last_day_date.day

    end_date = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)
    print(f"Конец периода (1 месяц): {end_date.strftime('%d.%m.%Y %H:%M:%S')}")

    # Проверяем дату 13 декабря
    dec_13 = datetime(2025, 12, 13, 10, 0, 0, tzinfo=timezone.utc)
    print(f"\nДата 13 декабря 2025: {dec_13.strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"13 декабря > конец периода? {dec_13 > end_date}")
    print(f"13 декабря <= конец периода? {dec_13 <= end_date}")

    # Получаем первые события из API
    print("\n" + "="*80)
    print("ПЕРВЫЕ СОБЫТИЯ ИЗ API:")
    print("="*80)

    async with RussiaRunningParser() as parser:
        data = await parser.get_events(skip=0, take=10)
        events = data.get("list", [])

        print(f"\nПолучено {len(events)} событий")

        for i, event in enumerate(events[:10], 1):
            begin_date_str = event.get('beginDate', 'N/A')
            title = event.get('title', 'Без названия')[:60]

            if begin_date_str != 'N/A':
                try:
                    bd = datetime.fromisoformat(begin_date_str.replace('Z', '+00:00'))
                    bd_formatted = bd.strftime('%d.%m.%Y')

                    # Проверяем фильтр
                    passes_filter = bd <= end_date
                    status = "✓ ПРОЙДЕТ" if passes_filter else "✗ НЕ ПРОЙДЕТ"

                    print(f"{i}. {bd_formatted} - {title}")
                    print(f"   {status} фильтр (begin_date <= {end_date.strftime('%d.%m.%Y')})")
                except Exception as e:
                    print(f"{i}. {begin_date_str} - {title} (ошибка парсинга: {e})")
            else:
                print(f"{i}. {begin_date_str} - {title}")


if __name__ == "__main__":
    asyncio.run(test())
