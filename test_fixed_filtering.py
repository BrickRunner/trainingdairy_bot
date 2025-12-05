"""
Тест исправленной фильтрации по периоду и виду спорта
"""

import asyncio
import logging
from datetime import datetime, timezone
from competitions.parser import fetch_competitions

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test():
    print("="*80)
    print("ТЕСТ ИСПРАВЛЕННОЙ ФИЛЬТРАЦИИ")
    print("="*80)

    now = datetime.now(timezone.utc)
    print(f"\nТекущая дата (UTC): {now.strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"Месяц: {now.month}, Год: {now.year}")

    # Тест 1: Все виды спорта за 1 месяц
    print("\n" + "="*80)
    print("ТЕСТ 1: Все виды спорта за 1 месяц")
    print("="*80)

    comps_all = await fetch_competitions(
        city=None,
        sport="all",
        limit=50,
        period_months=1
    )

    print(f"\nНайдено соревнований (все виды): {len(comps_all)}")
    if comps_all:
        print("\nПервые 10 соревнований:")
        for i, comp in enumerate(comps_all[:10], 1):
            begin_date = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
            date_str = begin_date.strftime('%d.%m.%Y')
            print(f"{i}. {date_str} - {comp['title'][:60]}")
            print(f"   Город: {comp['city']}, Спорт: {comp.get('sport_code', 'N/A')}")

    # Тест 2: Только плавание за 1 месяц
    print("\n" + "="*80)
    print("ТЕСТ 2: Только плавание за 1 месяц")
    print("="*80)

    comps_swim = await fetch_competitions(
        city=None,
        sport="swim",
        limit=50,
        period_months=1
    )

    print(f"\nНайдено соревнований (плавание): {len(comps_swim)}")
    if comps_swim:
        print("\nВсе соревнования с плаванием:")
        for i, comp in enumerate(comps_swim, 1):
            begin_date = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
            date_str = begin_date.strftime('%d.%m.%Y')
            print(f"{i}. {date_str} - {comp['title'][:70]}")
            print(f"   Город: {comp['city']}, Спорт: {comp.get('sport_code', 'N/A')}")
    else:
        print("\n⚠ Соревнования с плаванием не найдены!")

        # Проверим, есть ли события с плаванием в названии среди всех
        swim_in_title = [c for c in comps_all if 'плав' in c['title'].lower() or 'swim' in c['title'].lower()]
        if swim_in_title:
            print(f"\nНо найдено {len(swim_in_title)} событий со словом 'плав' или 'swim' в названии:")
            for comp in swim_in_title[:5]:
                begin_date = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
                date_str = begin_date.strftime('%d.%m.%Y')
                print(f"  - {date_str} - {comp['title'][:60]}")

    # Тест 3: Только бег за 1 месяц
    print("\n" + "="*80)
    print("ТЕСТ 3: Только бег за 1 месяц")
    print("="*80)

    comps_run = await fetch_competitions(
        city=None,
        sport="run",
        limit=20,
        period_months=1
    )

    print(f"\nНайдено соревнований (бег): {len(comps_run)}")
    if comps_run:
        print("\nПервые 5 соревнований:")
        for i, comp in enumerate(comps_run[:5], 1):
            begin_date = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
            date_str = begin_date.strftime('%d.%m.%Y')
            print(f"{i}. {date_str} - {comp['title'][:60]}")

    # Тест 4: Проверка периода на 6 месяцев
    print("\n" + "="*80)
    print("ТЕСТ 4: Все виды спорта за 6 месяцев")
    print("="*80)

    comps_6months = await fetch_competitions(
        city=None,
        sport="all",
        limit=30,
        period_months=6
    )

    print(f"\nНайдено соревнований (6 месяцев): {len(comps_6months)}")
    if comps_6months:
        # Показываем диапазон дат
        dates = [datetime.fromisoformat(c['begin_date'].replace('Z', '+00:00')) for c in comps_6months]
        min_date = min(dates)
        max_date = max(dates)
        print(f"Диапазон дат: от {min_date.strftime('%d.%m.%Y')} до {max_date.strftime('%d.%m.%Y')}")

    print("\n" + "="*80)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test())
