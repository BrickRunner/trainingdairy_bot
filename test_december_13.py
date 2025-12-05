"""
Поиск события 13 декабря с плаванием
"""

import asyncio
from datetime import datetime
from competitions.parser import RussiaRunningParser, matches_sport_type, check_sport_match


async def test():
    print("="*80)
    print("ПОИСК СОБЫТИЯ 13 ДЕКАБРЯ С ПЛАВАНИЕМ")
    print("="*80)

    async with RussiaRunningParser() as parser:
        all_events = []

        # Получаем больше событий
        for i in range(20):
            data = await parser.get_events(skip=i*100, take=100)
            events = data.get("list", [])
            if not events:
                break
            all_events.extend(events)

        print(f"Получено {len(all_events)} событий")

        # Ищем события 13 декабря
        december_13_events = []

        for event in all_events:
            begin_date_str = event.get('beginDate', '')
            if begin_date_str:
                try:
                    bd = datetime.fromisoformat(begin_date_str.replace('Z', '+00:00'))
                    if bd.day == 13 and bd.month == 12:
                        december_13_events.append(event)
                except:
                    pass

        print(f"\nНайдено событий 13 декабря: {len(december_13_events)}")

        if not december_13_events:
            print("События 13 декабря не найдены!")
            return

        # Анализируем каждое событие
        for i, event in enumerate(december_13_events, 1):
            print(f"\n{'='*80}")
            print(f"СОБЫТИЕ #{i}: {event.get('title', 'Без названия')}")
            print(f"{'='*80}")

            begin_date_str = event.get('beginDate', '')
            if begin_date_str:
                bd = datetime.fromisoformat(begin_date_str.replace('Z', '+00:00'))
                print(f"Дата: {bd.strftime('%d.%m.%Y')}")

            print(f"\nОсновная дисциплина:")
            disc_code = event.get('disciplineCode', 'N/A')
            disc_name = event.get('disciplineName', 'N/A')
            print(f"  disciplineCode: '{disc_code}'")
            print(f"  disciplineName: '{disc_name}'")

            # Проверяем основную дисциплину
            swim_match_main = check_sport_match(disc_code, disc_name, "swim")
            print(f"  check_sport_match для основной дисциплины: {swim_match_main}")

            # Проверяем дистанции
            race_items = event.get('raceItems', [])
            print(f"\nДистанции ({len(race_items)}):")

            has_swim_race = False
            for j, race in enumerate(race_items, 1):
                race_code = race.get('disciplineCode', 'N/A')
                race_name = race.get('disciplineName', 'N/A')
                race_title = race.get('name', 'N/A')

                print(f"\n  Дистанция #{j}: {race_title}")
                print(f"    disciplineCode: '{race_code}'")
                print(f"    disciplineName: '{race_name}'")

                # Проверяем дистанцию
                swim_match_race = check_sport_match(race_code, race_name, "swim")
                print(f"    check_sport_match: {swim_match_race}")

                if swim_match_race:
                    has_swim_race = True
                    print(f"    ✓ ЭТО ПЛАВАНИЕ!")

            # Проверяем matches_sport_type
            print(f"\n{'='*80}")
            result = matches_sport_type(event, "swim")
            print(f"matches_sport_type(event, 'swim'): {result}")

            if has_swim_race and not result:
                print("\n⚠ ОШИБКА: Событие содержит плавание в дистанциях, но matches_sport_type вернул False!")
            elif result:
                print("\n✓ Событие корректно определено как содержащее плавание")
            else:
                print("\n✗ Событие не содержит плавание")


if __name__ == "__main__":
    asyncio.run(test())
