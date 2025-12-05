"""
Отладка фильтрации по датам
"""

import asyncio
from datetime import datetime, timedelta
from competitions.parser import RussiaRunningParser


async def test_date_filtering():
    """Детальная отладка фильтрации по датам"""

    print("="*80)
    print("ОТЛАДКА ФИЛЬТРАЦИИ ПО ДАТАМ")
    print("="*80)

    now = datetime.now()
    end_date_30 = now + timedelta(days=30)

    print(f"\nТекущая дата: {now.strftime('%d.%m.%Y %H:%M')}")
    print(f"Конечная дата (30 дней): {end_date_30.strftime('%d.%m.%Y %H:%M')}")

    async with RussiaRunningParser() as parser:
        # Получаем первые 200 событий
        print(f"\n{'='*80}")
        print("ПОЛУЧЕНИЕ СОБЫТИЙ ИЗ API...")
        print(f"{'='*80}")

        all_events = []
        skip = 0
        batch_size = 100
        max_batches = 5

        for batch_num in range(max_batches):
            print(f"\nЗапрос #{batch_num + 1}: skip={skip}, take={batch_size}")

            data = await parser.get_events(
                skip=skip,
                take=batch_size,
                city=None,
                sport=None
            )

            events_batch = data.get("list", [])
            print(f"  Получено событий: {len(events_batch)}")

            if not events_batch:
                print("  Больше нет событий, останавливаемся")
                break

            all_events.extend(events_batch)

            if len(events_batch) < batch_size:
                print(f"  Получено меньше {batch_size}, это последняя порция")
                break

            skip += batch_size

        print(f"\n{'='*80}")
        print(f"ВСЕГО ПОЛУЧЕНО: {len(all_events)} событий")
        print(f"{'='*80}")

        # Анализируем даты
        print(f"\nПЕРВЫЕ 10 СОБЫТИЙ (с датами):")
        print("-" * 80)
        for i, event in enumerate(all_events[:10], 1):
            title = event.get('title', 'Без названия')[:50]
            begin_date_str = event.get('beginDate', '')

            if begin_date_str:
                try:
                    begin_date = datetime.fromisoformat(begin_date_str.replace('Z', '+00:00'))
                    date_formatted = begin_date.strftime('%d.%m.%Y')

                    # Проверяем, попадает ли в период 30 дней
                    within_30_days = begin_date <= end_date_30
                    status = "✓" if within_30_days else "✗"

                    print(f"{i}. {status} {date_formatted} - {title}")
                except Exception as e:
                    print(f"{i}. ? ОШИБКА парсинга даты '{begin_date_str}' - {title}")
            else:
                print(f"{i}. ? НЕТ ДАТЫ - {title}")

        print(f"\nПОСЛЕДНИЕ 10 СОБЫТИЙ (с датами):")
        print("-" * 80)
        for i, event in enumerate(all_events[-10:], len(all_events) - 9):
            title = event.get('title', 'Без названия')[:50]
            begin_date_str = event.get('beginDate', '')

            if begin_date_str:
                try:
                    begin_date = datetime.fromisoformat(begin_date_str.replace('Z', '+00:00'))
                    date_formatted = begin_date.strftime('%d.%m.%Y')

                    within_30_days = begin_date <= end_date_30
                    status = "✓" if within_30_days else "✗"

                    print(f"{i}. {status} {date_formatted} - {title}")
                except Exception as e:
                    print(f"{i}. ? ОШИБКА парсинга даты '{begin_date_str}' - {title}")
            else:
                print(f"{i}. ? НЕТ ДАТЫ - {title}")

        # Считаем сколько событий попадает в период
        print(f"\n{'='*80}")
        print("СТАТИСТИКА ПО ДАТАМ:")
        print(f"{'='*80}")

        within_30_count = 0
        beyond_30_count = 0
        no_date_count = 0

        for event in all_events:
            begin_date_str = event.get('beginDate', '')

            if begin_date_str:
                try:
                    begin_date = datetime.fromisoformat(begin_date_str.replace('Z', '+00:00'))
                    if begin_date <= end_date_30:
                        within_30_count += 1
                    else:
                        beyond_30_count += 1
                except:
                    no_date_count += 1
            else:
                no_date_count += 1

        print(f"Событий в пределах 30 дней: {within_30_count}")
        print(f"Событий за пределами 30 дней: {beyond_30_count}")
        print(f"Событий без даты или с ошибкой: {no_date_count}")
        print(f"Всего: {len(all_events)}")

        # Теперь тестируем функцию get_competitions
        print(f"\n{'='*80}")
        print("ТЕСТ ФУНКЦИИ get_competitions (period_months=1):")
        print(f"{'='*80}")

        competitions = await parser.get_competitions(
            city=None,
            sport=None,
            limit=1000,
            period_months=1
        )

        print(f"Получено отфильтрованных соревнований: {len(competitions)}")

        if competitions:
            print(f"\nПервые 5:")
            for i, comp in enumerate(competitions[:5], 1):
                begin_date = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
                date_str = begin_date.strftime('%d.%m.%Y')
                print(f"  {i}. {date_str} - {comp['title'][:50]}")

            print(f"\nПоследние 5:")
            for i, comp in enumerate(competitions[-5:], len(competitions) - 4):
                begin_date = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
                date_str = begin_date.strftime('%d.%m.%Y')
                print(f"  {i}. {date_str} - {comp['title'][:50]}")

    print(f"\n{'='*80}")
    print("ОТЛАДКА ЗАВЕРШЕНА")
    print(f"{'='*80}")


if __name__ == "__main__":
    asyncio.run(test_date_filtering())
