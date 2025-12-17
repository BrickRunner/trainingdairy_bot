"""
Тест объединенного получения соревнований из всех сервисов
"""

import asyncio
import logging
from competitions.competitions_fetcher import fetch_all_competitions, SERVICE_CODES
import sys
import io

# Установка правильной кодировки для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def test_all_services():
    """Тест получения соревнований из всех сервисов"""
    print("\n" + "="*60)
    print("ТЕСТ: ВСЕ СЕРВИСЫ")
    print("="*60)

    comps = await fetch_all_competitions(
        city="Москва",
        sport="run",
        limit=10,
        period_months=3,
        service="all"
    )

    print(f"\nПолучено соревнований: {len(comps)}")

    # Группируем по сервисам
    by_service = {}
    for comp in comps:
        service = comp.get('service', 'Unknown')
        by_service.setdefault(service, []).append(comp)

    print("\nРаспределение по сервисам:")
    for service, items in by_service.items():
        print(f"  {service}: {len(items)} соревнований")

    print("\nПервые 10 соревнований:")
    for i, comp in enumerate(comps[:10], 1):
        print(f"\n{i}. {comp['title']}")
        print(f"   Сервис: {comp.get('service', 'N/A')}")
        print(f"   Город: {comp['city']}")
        print(f"   Дата: {comp.get('formatted_date', 'N/A')}")

async def test_each_service():
    """Тест каждого сервиса отдельно"""
    print("\n" + "="*80)
    print("ТЕСТ: КАЖДЫЙ СЕРВИС ОТДЕЛЬНО")
    print("="*80)

    services = ["RussiaRunning", "Timerman", "HeroLeague"]

    for service in services:
        print(f"\n{'='*60}")
        print(f"Сервис: {service}")
        print('='*60)

        try:
            comps = await fetch_all_competitions(
                city="Москва",
                limit=3,
                service=service
            )

            print(f"Получено: {len(comps)} соревнований")

            for i, comp in enumerate(comps, 1):
                print(f"\n{i}. {comp['title']}")
                print(f"   Город: {comp['city']}")
                print(f"   Дата: {comp.get('formatted_date', 'N/A')}")
                print(f"   Организатор: {comp.get('organizer', 'N/A')}")

        except Exception as e:
            print(f"❌ Ошибка: {e}")

async def test_service_codes():
    """Тест констант SERVICE_CODES"""
    print("\n" + "="*60)
    print("ТЕСТ: SERVICE_CODES")
    print("="*60)

    print("\nСписок доступных сервисов:")
    for name, code in SERVICE_CODES.items():
        print(f"  {name} → {code}")

    expected_services = ["RussiaRunning", "Timerman", "Лига Героев", "Все сервисы"]
    for service in expected_services:
        if service in SERVICE_CODES:
            print(f"✅ {service}: {SERVICE_CODES[service]}")
        else:
            print(f"❌ {service}: ОТСУТСТВУЕТ")

async def run_all_tests():
    """Запустить все тесты"""
    print("\n" + "="*80)
    print("ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ ВСЕХ СЕРВИСОВ")
    print("="*80)

    await test_service_codes()
    await test_each_service()
    await test_all_services()

    print("\n" + "="*80)
    print("✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(run_all_tests())
