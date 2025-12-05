"""
Детальная отладка фильтрации плавания
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from competitions.parser import RussiaRunningParser, matches_sport_type, check_sport_match

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

async def test():
    print("="*80)
    print("ДЕТАЛЬНАЯ ОТЛАДКА ФИЛЬТРАЦИИ ПЛАВАНИЯ")
    print("="*80)

    async with RussiaRunningParser() as parser:
        # Получаем все события за 1 месяц
        all_events = []

        for i in range(5):
            data = await parser.get_events(skip=i*100, take=100)
            events = data.get("list", [])
            if not events:
                break
            all_events.extend(events)
            print(f"Получено {len(all_events)} событий...")

        print(f"\nВсего получено: {len(all_events)} событий")

        # Фильтруем по периоду (1 месяц)
        now = datetime.now(timezone.utc)
        year = now.year
        month = now.month

        if month == 12:
            last_day = 31
        else:
            next_month = datetime(year, month + 1, 1, tzinfo=timezone.utc)
            last_day_date = next_month - timedelta(days=1)
            last_day = last_day_date.day

        end_date = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)

        print(f"\nТекущая дата: {now.strftime('%d.%m.%Y')}")
        print(f"Конец периода: {end_date.strftime('%d.%m.%Y')}")

        events_in_period = []
        for event in all_events:
            begin_date_str = event.get('beginDate')
            if begin_date_str:
                try:
                    begin_date_obj = datetime.fromisoformat(begin_date_str.replace('Z', '+00:00'))
                    if begin_date_obj <= end_date:
                        events_in_period.append(event)
                except:
                    pass

        print(f"События в периоде (до {end_date.strftime('%d.%m.%Y')}): {len(events_in_period)}")

        # Ищем все что связано с плаванием
        print("\n" + "="*80)
        print("ПОИСК СОБЫТИЙ С ПЛАВАНИЕМ:")
        print("="*80)

        swim_related = []

        for event in events_in_period:
            title = event.get('title', '').lower()
            disc_code = event.get('disciplineCode', '').lower()
            disc_name = event.get('disciplineName', '').lower()

            # Проверяем основную дисциплину
            is_swim_main = 'swim' in disc_code or 'плав' in disc_name or 'swim' in title or 'плав' in title

            # Проверяем дистанции
            race_items = event.get('raceItems', [])
            swim_races = []
            for race in race_items:
                race_code = race.get('disciplineCode', '').lower()
                race_name = race.get('disciplineName', '').lower()
                if 'swim' in race_code or 'плав' in race_name:
                    swim_races.append(f"{race_name} ({race_code})")

            if is_swim_main or swim_races:
                swim_related.append({
                    'event': event,
                    'is_swim_main': is_swim_main,
                    'swim_races': swim_races
                })

        print(f"\nНайдено событий с плаванием: {len(swim_related)}")

        if swim_related:
            print("\nСобытия с плаванием:")
            for i, item in enumerate(swim_related, 1):
                event = item['event']
                print(f"\n{i}. {event.get('title', 'Без названия')}")

                begin_date_str = event.get('beginDate', '')
                if begin_date_str:
                    try:
                        bd = datetime.fromisoformat(begin_date_str.replace('Z', '+00:00'))
                        print(f"   Дата: {bd.strftime('%d.%m.%Y')}")
                    except:
                        print(f"   Дата: {begin_date_str}")

                print(f"   disciplineCode: {event.get('disciplineCode', 'N/A')}")
                print(f"   disciplineName: {event.get('disciplineName', 'N/A')}")

                if item['is_swim_main']:
                    print(f"   ✓ Плавание в основной дисциплине")

                if item['swim_races']:
                    print(f"   ✓ Плавание в дистанциях:")
                    for race in item['swim_races']:
                        print(f"      - {race}")

                # Проверяем функцию matches_sport_type
                result = matches_sport_type(event, "swim")
                print(f"   matches_sport_type(event, 'swim'): {result}")

        else:
            print("\n⚠ События с плаванием НЕ НАЙДЕНЫ!")

        # Проверяем функцию check_sport_match отдельно
        print("\n" + "="*80)
        print("ТЕСТ ФУНКЦИИ check_sport_match:")
        print("="*80)

        test_cases = [
            ("swim", "Плавание", "swim"),
            ("swim", "Swimming", "swim"),
            ("relay-swim", "Плавание (эстафета)", "swim"),
            ("run", "Бег", "swim"),
        ]

        for code, name, target in test_cases:
            result = check_sport_match(code, name, target)
            print(f"check_sport_match('{code}', '{name}', '{target}'): {result}")


if __name__ == "__main__":
    asyncio.run(test())
