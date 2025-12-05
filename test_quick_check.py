"""
Быстрая проверка фильтрации
"""

import asyncio
import logging
from datetime import datetime, timezone
from competitions.parser import fetch_competitions

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

async def main():
    now = datetime.now(timezone.utc)
    print(f"Текущая дата: {now.strftime('%d.%m.%Y %H:%M')}\n")

    # Тест 1: Все соревнования за месяц
    print("="*60)
    print("Тест 1: Все виды спорта за 1 месяц (лимит 10)")
    print("="*60)

    result = await fetch_competitions(sport="all", period_months=1, limit=10)
    print(f"\nРезультат: {len(result)} соревнований\n")

    if result:
        for i, comp in enumerate(result[:5], 1):
            bd = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
            print(f"{i}. {bd.strftime('%d.%m.%Y')} - {comp['title'][:50]}")

    # Тест 2: Плавание
    print("\n" + "="*60)
    print("Тест 2: Плавание за 1 месяц")
    print("="*60)

    result_swim = await fetch_competitions(sport="swim", period_months=1, limit=20)
    print(f"\nРезультат: {len(result_swim)} соревнований с плаванием\n")

    if result_swim:
        for i, comp in enumerate(result_swim, 1):
            bd = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
            print(f"{i}. {bd.strftime('%d.%m.%Y')} - {comp['title'][:60]}")
    else:
        print("⚠ Соревнования не найдены")

    print("\n" + "="*60)

asyncio.run(main())
