"""
Тест с точными параметрами как в боте:
- Город: Москва
- Период: 1 месяц
- Спорт: бег (run)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from competitions.parser import fetch_competitions

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

async def test():
    print("="*80)
    print("ТЕСТ: Москва + 1 месяц + Бег")
    print("="*80)

    now = datetime.now()
    end_date_30 = now + timedelta(days=30)

    print(f"\nСегодня: {now.strftime('%d.%m.%Y')}")
    print(f"Конец периода (30 дней): {end_date_30.strftime('%d.%m.%Y')}")
    print("\n" + "-"*80)

    # Точно такие же параметры как в боте
    city = "Москва"
    sport = "run"
    period_months = 1

    print(f"Параметры запроса:")
    print(f"  city = '{city}'")
    print(f"  sport = '{sport}'")
    print(f"  period_months = {period_months}")
    print(f"  limit = 1000")
    print("\nЗапускаем...\n")

    comps = await fetch_competitions(
        city=city,
        sport=sport,
        limit=1000,
        period_months=period_months
    )

    print("\n" + "="*80)
    print(f"РЕЗУЛЬТАТ: Найдено {len(comps)} соревнований")
    print("="*80)

    if not comps:
        print("\n⚠ Соревнования не найдены!")
        return

    # Показываем первые 10
    print(f"\nПЕРВЫЕ 10 СОРЕВНОВАНИЙ:")
    print("-"*80)
    for i, comp in enumerate(comps[:10], 1):
        begin_date = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
        date_str = begin_date.strftime('%d.%m.%Y')

        # Проверяем в пределах ли периода
        is_within = begin_date <= end_date_30
        status = "✓" if is_within else "✗ ВНЕ ПЕРИОДА"

        print(f"{i:2}. {status} | {date_str} | {comp['title'][:50]}")
        print(f"     Город: {comp['city']}, Спорт: {comp.get('sport_code', 'N/A')}")

    # Показываем последние 10
    print(f"\nПОСЛЕДНИЕ 10 СОРЕВНОВАНИЙ:")
    print("-"*80)
    for i, comp in enumerate(comps[-10:], len(comps) - 9):
        begin_date = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
        date_str = begin_date.strftime('%d.%m.%Y')

        is_within = begin_date <= end_date_30
        status = "✓" if is_within else "✗ ВНЕ ПЕРИОДА"

        print(f"{i:2}. {status} | {date_str} | {comp['title'][:50]}")
        print(f"     Город: {comp['city']}, Спорт: {comp.get('sport_code', 'N/A')}")

    # Анализируем все даты
    print(f"\n{'='*80}")
    print("АНАЛИЗ ДАТ:")
    print(f"{'='*80}")

    within_period = []
    beyond_period = []

    for comp in comps:
        begin_date = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
        if begin_date <= end_date_30:
            within_period.append(comp)
        else:
            beyond_period.append(comp)

    print(f"В пределах периода (до {end_date_30.strftime('%d.%m.%Y')}): {len(within_period)}")
    print(f"За пределами периода: {len(beyond_period)}")

    if beyond_period:
        print(f"\n⚠ НАЙДЕНО {len(beyond_period)} СОРЕВНОВАНИЙ ЗА ПРЕДЕЛАМИ ПЕРИОДА!")
        print("\nПервые 5 событий за пределами периода:")
        for i, comp in enumerate(beyond_period[:5], 1):
            begin_date = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
            date_str = begin_date.strftime('%d.%m.%Y')
            print(f"  {i}. {date_str} - {comp['title'][:50]}")

        # Самое дальнее событие
        furthest = max(beyond_period, key=lambda c: datetime.fromisoformat(c['begin_date'].replace('Z', '+00:00')))
        furthest_date = datetime.fromisoformat(furthest['begin_date'].replace('Z', '+00:00'))
        print(f"\nСамое дальнее событие: {furthest_date.strftime('%d.%m.%Y')} - {furthest['title'][:50]}")
    else:
        print("\n✓ ВСЕ СОРЕВНОВАНИЯ В ПРЕДЕЛАХ ПЕРИОДА!")

    print("\n" + "="*80)

if __name__ == "__main__":
    asyncio.run(test())
