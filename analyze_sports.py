"""
Анализ кодов видов спорта в API
"""

import asyncio
from competitions.parser import RussiaRunningParser


async def analyze():
    print("="*80)
    print("АНАЛИЗ КОДОВ ВИДОВ СПОРТА В API")
    print("="*80)

    async with RussiaRunningParser() as parser:
        all_events = []

        # Получаем побольше событий для анализа
        for i in range(5):
            data = await parser.get_events(skip=i*100, take=100)
            events = data.get("list", [])
            if not events:
                break
            all_events.extend(events)
            print(f"Получено {len(all_events)} событий...")

        print(f"\nВсего получено: {len(all_events)} событий")
        print("\n" + "="*80)
        print("АНАЛИЗ КОДОВ ДИСЦИПЛИН (disciplineCode)")
        print("="*80)

        # Группируем по кодам дисциплин
        discipline_stats = {}

        for event in all_events:
            code = event.get('disciplineCode', 'unknown')
            name = event.get('disciplineName', 'Неизвестно')

            if code not in discipline_stats:
                discipline_stats[code] = {
                    'count': 0,
                    'names': set()
                }

            discipline_stats[code]['count'] += 1
            discipline_stats[code]['names'].add(name)

        # Сортируем по количеству
        sorted_stats = sorted(discipline_stats.items(), key=lambda x: x[1]['count'], reverse=True)

        print("\nКод → Названия (количество событий):")
        print("-"*80)

        for code, stats in sorted_stats:
            names = ', '.join(sorted(stats['names']))
            print(f"\n'{code}' ({stats['count']} событий):")
            print(f"  Названия: {names}")

        # Группируем по основным видам спорта
        print("\n" + "="*80)
        print("РЕКОМЕНДУЕМЫЕ ГРУППЫ ДЛЯ ФИЛЬТРАЦИИ:")
        print("="*80)

        # Ищем все связанные с бегом
        run_codes = [code for code in discipline_stats.keys() if 'run' in code.lower() or 'бег' in str(discipline_stats[code]['names']).lower()]
        swim_codes = [code for code in discipline_stats.keys() if 'swim' in code.lower() or 'плав' in str(discipline_stats[code]['names']).lower()]
        bike_codes = [code for code in discipline_stats.keys() if 'bike' in code.lower() or 'cycle' in code.lower() or 'велос' in str(discipline_stats[code]['names']).lower()]

        print("\nБЕГ - коды:", run_codes)
        print("ПЛАВАНИЕ - коды:", swim_codes)
        print("ВЕЛОСПОРТ - коды:", bike_codes)

        # Примеры событий
        print("\n" + "="*80)
        print("ПРИМЕРЫ СОБЫТИЙ ПО КОДАМ:")
        print("="*80)

        for code in list(discipline_stats.keys())[:10]:
            examples = [e for e in all_events if e.get('disciplineCode') == code][:2]
            if examples:
                print(f"\nКод '{code}':")
                for ex in examples:
                    print(f"  - {ex.get('title', 'Без названия')[:60]}")


if __name__ == "__main__":
    asyncio.run(analyze())
