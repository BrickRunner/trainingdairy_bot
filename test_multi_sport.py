"""
Проверка соревнований с несколькими видами спорта
"""

import asyncio
from competitions.parser import RussiaRunningParser


async def test():
    print("="*80)
    print("ПРОВЕРКА СОРЕВНОВАНИЙ С НЕСКОЛЬКИМИ ВИДАМИ СПОРТА")
    print("="*80)

    async with RussiaRunningParser() as parser:
        # Получаем события
        data = await parser.get_events(skip=0, take=100)
        events = data.get("list", [])

        print(f"\nПолучено {len(events)} событий\n")
        print("="*80)

        # Ищем события с raceItems (дистанциями)
        for event in events[:30]:
            title = event.get('title', 'Без названия')
            discipline_code = event.get('disciplineCode', 'N/A')
            discipline_name = event.get('disciplineName', 'N/A')
            race_items = event.get('raceItems', [])

            # Собираем все виды спорта из дистанций
            race_disciplines = set()
            for race in race_items:
                race_disc_code = race.get('disciplineCode')
                race_disc_name = race.get('disciplineName')
                if race_disc_code:
                    race_disciplines.add(f"{race_disc_code} ({race_disc_name})")

            # Если есть разные виды спорта в дистанциях
            if len(race_disciplines) > 1:
                print(f"\n📊 {title[:60]}")
                print(f"   Основная дисциплина: {discipline_code} ({discipline_name})")
                print(f"   Дистанции ({len(race_items)}):")
                for race_disc in sorted(race_disciplines):
                    print(f"      - {race_disc}")

        # Проверяем триатлон/мультиспорт
        print("\n" + "="*80)
        print("ПОИСК ТРИАТЛОНА И МУЛЬТИСПОРТА:")
        print("="*80)

        for event in events:
            title = event.get('title', '').lower()
            discipline_code = event.get('disciplineCode', '').lower()
            discipline_name = event.get('disciplineName', '').lower()

            if any(keyword in title or keyword in discipline_code or keyword in discipline_name
                   for keyword in ['триатлон', 'triathlon', 'дуатлон', 'duathlon', 'мульти']):
                print(f"\n🏊‍♂️🚴‍♂️🏃 {event.get('title', 'Без названия')[:60]}")
                print(f"   disciplineCode: {event.get('disciplineCode', 'N/A')}")
                print(f"   disciplineName: {event.get('disciplineName', 'N/A')}")

                race_items = event.get('raceItems', [])
                if race_items:
                    print(f"   Дистанции:")
                    for race in race_items[:5]:
                        print(f"      - {race.get('name', 'N/A')} ({race.get('disciplineCode', 'N/A')})")


if __name__ == "__main__":
    asyncio.run(test())
