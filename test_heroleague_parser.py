"""
Тест парсера HeroLeague для проверки корректности работы с реальным API
"""

import asyncio
import logging
from competitions.heroleague_parser import fetch_competitions
from datetime import datetime
import json
import sys

# Установка правильной кодировки для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_basic_fetch():
    """Базовый тест получения соревнований"""
    print("\n" + "="*60)
    print("ТЕСТ 1: Базовое получение соревнований")
    print("="*60)

    comps = await fetch_competitions(limit=10)
    print(f"\nПолучено соревнований: {len(comps)}")

    if comps:
        print("\nПервое соревнование:")
        first = comps[0]
        for key, value in first.items():
            print(f"  {key}: {value}")
    else:
        print("❌ Не удалось получить соревнования")

    return len(comps) > 0

async def test_city_filter():
    """Тест фильтрации по городу"""
    print("\n" + "="*60)
    print("ТЕСТ 2: Фильтрация по городу (Москва)")
    print("="*60)

    comps = await fetch_competitions(city="Москва", limit=5)
    print(f"\nПолучено соревнований в Москве: {len(comps)}")

    for i, comp in enumerate(comps, 1):
        print(f"\n{i}. {comp['title']}")
        print(f"   Город: {comp['city']}")
        print(f"   Дата: {comp.get('formatted_date', 'N/A')}")
        print(f"   Тип: {comp.get('event_type', 'N/A')}")

    return len(comps) > 0

async def test_sport_filter():
    """Тест фильтрации по виду спорта"""
    print("\n" + "="*60)
    print("ТЕСТ 3: Фильтрация по виду спорта")
    print("="*60)

    # Тест: бег
    print("\n--- Бег (run) ---")
    run_comps = await fetch_competitions(sport="run", limit=5)
    print(f"Найдено соревнований по бегу: {len(run_comps)}")
    for comp in run_comps[:3]:
        print(f"  - {comp['title']} ({comp.get('event_type', 'N/A')})")

    # Тест: лыжи
    print("\n--- Лыжи (ski) ---")
    ski_comps = await fetch_competitions(sport="ski", limit=5)
    print(f"Найдено лыжных соревнований: {len(ski_comps)}")
    for comp in ski_comps[:3]:
        print(f"  - {comp['title']} ({comp.get('event_type', 'N/A')})")

    return len(run_comps) > 0 or len(ski_comps) > 0

async def test_period_filter():
    """Тест фильтрации по периоду"""
    print("\n" + "="*60)
    print("ТЕСТ 4: Фильтрация по периоду (3 месяца)")
    print("="*60)

    comps = await fetch_competitions(period_months=3, limit=10)
    print(f"\nПолучено соревнований на 3 месяца: {len(comps)}")

    if comps:
        print("\nПервые 5 соревнований:")
        for i, comp in enumerate(comps[:5], 1):
            print(f"{i}. {comp['title']}")
            print(f"   Дата: {comp.get('formatted_date', 'N/A')}")
            print(f"   Город: {comp['city']}")

    return True

async def test_combined_filters():
    """Тест комбинированных фильтров"""
    print("\n" + "="*60)
    print("ТЕСТ 5: Комбинированные фильтры")
    print("="*60)

    print("\n--- Бег в Москве на 6 месяцев ---")
    comps = await fetch_competitions(
        city="Москва",
        sport="run",
        period_months=6,
        limit=5
    )

    print(f"Найдено: {len(comps)} соревнований")
    for i, comp in enumerate(comps, 1):
        print(f"\n{i}. {comp['title']}")
        print(f"   Дата: {comp.get('formatted_date', 'N/A')}")
        print(f"   Тип: {comp.get('event_type', 'N/A')}")
        print(f"   Описание дистанций: {comp.get('distances_text', 'N/A')[:80]}...")

    return True

async def test_data_structure():
    """Проверка структуры данных"""
    print("\n" + "="*60)
    print("ТЕСТ 6: Проверка структуры данных")
    print("="*60)

    comps = await fetch_competitions(limit=1)

    if comps:
        comp = comps[0]
        required_fields = ['id', 'title', 'city', 'service', 'begin_date', 'organizer']

        print("\nПроверка обязательных полей:")
        all_present = True
        for field in required_fields:
            present = field in comp and comp[field]
            status = "✅" if present else "❌"
            print(f"  {status} {field}: {comp.get(field, 'MISSING')}")
            all_present = all_present and present

        return all_present
    else:
        print("❌ Не удалось получить соревнования для проверки")
        return False

async def run_all_tests():
    """Запустить все тесты"""
    print("\n" + "="*80)
    print("ТЕСТИРОВАНИЕ ПАРСЕРА HEROLEAGUE")
    print("="*80)

    results = {
        "Базовое получение": await test_basic_fetch(),
        "Фильтр по городу": await test_city_filter(),
        "Фильтр по спорту": await test_sport_filter(),
        "Фильтр по периоду": await test_period_filter(),
        "Комбинированные фильтры": await test_combined_filters(),
        "Структура данных": await test_data_structure(),
    }

    print("\n" + "="*80)
    print("РЕЗУЛЬТАТЫ ТЕСТОВ")
    print("="*80)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")

    passed = sum(1 for v in results.values() if v is True)
    total = len(results)
    print(f"\nПройдено: {passed}/{total}")

    if passed == total:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
    else:
        print(f"\n⚠️ Некоторые тесты не прошли ({total - passed} failed)")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
