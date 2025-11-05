"""Test health queries"""
import asyncio
import sys
from datetime import date, timedelta
import os

# Set UTF-8 encoding for Windows console
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# Add path to modules
sys.path.insert(0, '.')

from health.health_queries import (
    get_latest_health_metrics,
    get_current_week_metrics,
    get_current_month_metrics
)

async def main():
    user_id = 8296492604  # ID пользователя из БД

    print("=" * 60)
    print("ТЕСТИРОВАНИЕ ФУНКЦИЙ ЗАПРОСОВ ЗДОРОВЬЯ")
    print("=" * 60)

    # Тест 1: Последние 7 дней
    print("\nTest 1: Last 7 days")
    print(f"Period: {date.today() - timedelta(days=6)} - {date.today()}")
    metrics_7 = await get_latest_health_metrics(user_id, 7)
    print(f"Found records: {len(metrics_7)}")
    for m in metrics_7:
        print(f"  {m['date']}: pulse={m.get('morning_pulse')}, weight={m.get('weight')}, sleep={m.get('sleep_duration')}")

    # Тест 2: Последние 14 дней
    print("\nTest 2: Last 14 days")
    print(f"Period: {date.today() - timedelta(days=13)} - {date.today()}")
    metrics_14 = await get_latest_health_metrics(user_id, 14)
    print(f"Found records: {len(metrics_14)}")
    for m in metrics_14:
        print(f"  {m['date']}: pulse={m.get('morning_pulse')}, weight={m.get('weight')}, sleep={m.get('sleep_duration')}")

    # Тест 3: Последние 30 дней
    print("\nTest 3: Last 30 days")
    print(f"Period: {date.today() - timedelta(days=29)} - {date.today()}")
    metrics_30 = await get_latest_health_metrics(user_id, 30)
    print(f"Found records: {len(metrics_30)}")
    for m in metrics_30:
        print(f"  {m['date']}: pulse={m.get('morning_pulse')}, weight={m.get('weight')}, sleep={m.get('sleep_duration')}")

    # Тест 4: Текущая неделя
    print("\nTest 4: Current week")
    today = date.today()
    weekday = today.weekday()
    start_week = today - timedelta(days=weekday)
    end_week = start_week + timedelta(days=6)
    print(f"Period: {start_week} - {end_week}")
    metrics_week = await get_current_week_metrics(user_id)
    print(f"Found records: {len(metrics_week)}")
    for m in metrics_week:
        print(f"  {m['date']}: pulse={m.get('morning_pulse')}, weight={m.get('weight')}, sleep={m.get('sleep_duration')}")

    # Тест 5: Текущий месяц
    print("\nTest 5: Current month")
    start_month = date(today.year, today.month, 1)
    if today.month == 12:
        end_month = date(today.year, 12, 31)
    else:
        end_month = date(today.year, today.month + 1, 1) - timedelta(days=1)
    print(f"Period: {start_month} - {end_month}")
    metrics_month = await get_current_month_metrics(user_id)
    print(f"Found records: {len(metrics_month)}")
    for m in metrics_month:
        print(f"  {m['date']}: pulse={m.get('morning_pulse')}, weight={m.get('weight')}, sleep={m.get('sleep_duration')}")

    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
