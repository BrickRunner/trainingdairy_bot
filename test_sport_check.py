"""
Проверка полей спорта в API
"""

import asyncio
from competitions.parser import RussiaRunningParser


async def test():
    print("="*80)
    print("ПРОВЕРКА ПОЛЕЙ СПОРТА В API")
    print("="*80)

    async with RussiaRunningParser() as parser:
        # Получаем первые 100 событий
        data = await parser.get_events(skip=0, take=100)
        events = data.get("list", [])

        print(f"\nПолучено {len(events)} событий\n")

        # Собираем все уникальные значения полей спорта
        sport_codes = set()
        sport_names = set()
        discipline_names = set()

        for event in events[:50]:  # Первые 50 для анализа
            sport_code = event.get('disciplineCode')
            sport_name = event.get('sportName')
            discipline_name = event.get('disciplineName')

            if sport_code:
                sport_codes.add(sport_code)
            if sport_name:
                sport_names.add(sport_name)
            if discipline_name:
                discipline_names.add(discipline_name)

        print("УНИКАЛЬНЫЕ ЗНАЧЕНИЯ disciplineCode:")
        for code in sorted(sport_codes):
            print(f"  - {code}")

        print("\nУНИКАЛЬНЫЕ ЗНАЧЕНИЯ sportName:")
        for name in sorted(sport_names):
            print(f"  - {name}")

        print("\nУНИКАЛЬНЫЕ ЗНАЧЕНИЯ disciplineName:")
        for name in sorted(discipline_names):
            print(f"  - {name}")

        # Примеры событий с разными видами спорта
        print("\n" + "="*80)
        print("ПРИМЕРЫ СОБЫТИЙ:")
        print("="*80)

        for i, event in enumerate(events[:10], 1):
            title = event.get('title', 'Без названия')[:50]
            discipline_code = event.get('disciplineCode', 'N/A')
            discipline_name = event.get('disciplineName', 'N/A')
            sport_name = event.get('sportName', 'N/A')

            print(f"\n{i}. {title}")
            print(f"   disciplineCode: {discipline_code}")
            print(f"   disciplineName: {discipline_name}")
            print(f"   sportName: {sport_name}")


if __name__ == "__main__":
    asyncio.run(test())
