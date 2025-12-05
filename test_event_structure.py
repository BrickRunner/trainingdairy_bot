"""
Анализ структуры события 13 декабря
"""

import asyncio
import json
from datetime import datetime
from competitions.parser import RussiaRunningParser


async def test():
    print("="*80)
    print("АНАЛИЗ СТРУКТУРЫ СОБЫТИЯ 13 ДЕКАБРЯ")
    print("="*80)

    async with RussiaRunningParser() as parser:
        all_events = []

        # Получаем много событий
        for i in range(20):
            data = await parser.get_events(skip=i*100, take=100)
            events = data.get("list", [])
            if not events:
                break
            all_events.extend(events)
            print(f"Получено {len(all_events)} событий...")

        print(f"\nВсего получено: {len(all_events)} событий")

        # Ищем события 13 декабря
        december_13_events = []

        for event in all_events:
            begin_date_str = event.get('beginDate', '')
            if begin_date_str:
                try:
                    bd = datetime.fromisoformat(begin_date_str.replace('Z', '+00:00'))
                    if bd.day == 13 and bd.month == 12 and bd.year == 2025:
                        december_13_events.append(event)
                except:
                    pass

        print(f"\nНайдено событий 13 декабря 2025: {len(december_13_events)}\n")

        if not december_13_events:
            print("События 13 декабря не найдены!")
            # Ищем ближайшие события
            print("\nПоказываю первые 5 событий из полученных:")
            for i, event in enumerate(all_events[:5], 1):
                bd_str = event.get('beginDate', 'N/A')
                try:
                    bd = datetime.fromisoformat(bd_str.replace('Z', '+00:00'))
                    bd_formatted = bd.strftime('%d.%m.%Y')
                except:
                    bd_formatted = bd_str
                print(f"{i}. {bd_formatted} - {event.get('title', 'N/A')[:60]}")
            return

        # Выводим ПОЛНУЮ структуру каждого события
        for i, event in enumerate(december_13_events, 1):
            print(f"{'='*80}")
            print(f"СОБЫТИЕ #{i}")
            print(f"{'='*80}")

            # Выводим JSON события
            print(json.dumps(event, indent=2, ensure_ascii=False))

            print(f"\n{'='*80}\n")


if __name__ == "__main__":
    asyncio.run(test())
