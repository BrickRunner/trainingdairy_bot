"""
Тест парсера Timerman для проверки корректности работы с реальным API
"""

import asyncio
import logging
from competitions.timerman_parser import fetch_competitions
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
    print("🔍 ТЕСТ 1: Базовое получение соревнований")
    print("="*60)

    try:
        competitions = await fetch_competitions(limit=10)

        print(f"\n✅ Получено {len(competitions)} соревнований")

        if competitions:
            print("\n📋 Первое соревнование:")
            first = competitions[0]
            print(json.dumps(first, ensure_ascii=False, indent=2, default=str))

            print("\n📊 Структура данных:")
            print(f"  - ID: {first.get('id')}")
            print(f"  - Название: {first.get('title')}")
            print(f"  - Город: {first.get('city')}")
            print(f"  - Дата начала: {first.get('begin_date')}")
            print(f"  - Дата окончания: {first.get('end_date')}")
            print(f"  - Спорт: {first.get('sport_code')}")
            print(f"  - Сервис: {first.get('service')}")
            print(f"  - Организатор: {first.get('organizer')}")
            print(f"  - Участников: {first.get('participants_count')}")
            print(f"  - URL: {first.get('url')}")
            print(f"  - Дистанций: {len(first.get('distances', []))}")

            if first.get('distances'):
                print(f"\n  Первая дистанция:")
                dist = first['distances'][0]
                print(f"    - Название: {dist.get('name')}")
                print(f"    - Дистанция: {dist.get('distance')}")
                print(f"    - Спорт: {dist.get('sport')}")
                print(f"    - Участников: {dist.get('participants_count')}")
        else:
            print("⚠️ Не получено соревнований")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


async def test_sport_filter():
    """Тест фильтрации по виду спорта"""
    print("\n" + "="*60)
    print("🏃 ТЕСТ 2: Фильтрация по виду спорта")
    print("="*60)

    sports = ["run", "swim", "bike"]

    for sport in sports:
        try:
            competitions = await fetch_competitions(sport=sport, limit=5)
            print(f"\n{sport.upper()}: найдено {len(competitions)} соревнований")

            if competitions:
                for i, comp in enumerate(competitions[:3], 1):
                    print(f"  {i}. {comp.get('title')} - {comp.get('sport_code')}")

        except Exception as e:
            print(f"❌ Ошибка для {sport}: {e}")


async def test_city_filter():
    """Тест фильтрации по городу"""
    print("\n" + "="*60)
    print("🏙️ ТЕСТ 3: Фильтрация по городу")
    print("="*60)

    cities = ["Москва", "Санкт-Петербург", "Казань"]

    for city in cities:
        try:
            competitions = await fetch_competitions(city=city, limit=5)
            print(f"\n{city}: найдено {len(competitions)} соревнований")

            if competitions:
                for i, comp in enumerate(competitions[:3], 1):
                    print(f"  {i}. {comp.get('title')} - {comp.get('city')}")

        except Exception as e:
            print(f"❌ Ошибка для {city}: {e}")


async def test_period_filter():
    """Тест фильтрации по периоду"""
    print("\n" + "="*60)
    print("📅 ТЕСТ 4: Фильтрация по периоду")
    print("="*60)

    periods = [
        (1, "Текущий месяц"),
        (12, "Текущий год"),
        (None, "Ближайшие 6 месяцев")
    ]

    for period_months, description in periods:
        try:
            competitions = await fetch_competitions(period_months=period_months, limit=10)
            print(f"\n{description}: найдено {len(competitions)} соревнований")

            if competitions:
                dates = [comp.get('begin_date') for comp in competitions[:5] if comp.get('begin_date')]
                if dates:
                    print(f"  Диапазон дат: {min(dates)} - {max(dates)}")

        except Exception as e:
            print(f"❌ Ошибка для периода {description}: {e}")


async def test_combined_filters():
    """Тест комбинированных фильтров"""
    print("\n" + "="*60)
    print("🔧 ТЕСТ 5: Комбинированные фильтры")
    print("="*60)

    test_cases = [
        {"city": "Москва", "sport": "run", "period_months": 1},
        {"sport": "swim", "period_months": 12},
        {"city": "Санкт-Петербург", "period_months": 1},
    ]

    for i, filters in enumerate(test_cases, 1):
        try:
            print(f"\nТест {i}: {filters}")
            competitions = await fetch_competitions(**filters, limit=5)
            print(f"  Найдено: {len(competitions)} соревнований")

            if competitions:
                for comp in competitions[:2]:
                    print(f"  - {comp.get('title')} ({comp.get('city')}, {comp.get('begin_date')})")

        except Exception as e:
            print(f"❌ Ошибка: {e}")


async def test_service_field():
    """Проверка что все соревнования имеют service='Timerman'"""
    print("\n" + "="*60)
    print("🏷️ ТЕСТ 6: Проверка поля 'service'")
    print("="*60)

    try:
        competitions = await fetch_competitions(limit=20)

        services = [comp.get('service') for comp in competitions]
        timerman_count = services.count('Timerman')

        print(f"\nПроверено соревнований: {len(competitions)}")
        print(f"С service='Timerman': {timerman_count}")

        if timerman_count == len(competitions):
            print("✅ Все соревнования имеют корректное поле service='Timerman'")
        else:
            print("⚠️ Некоторые соревнования не имеют service='Timerman'")
            for i, comp in enumerate(competitions):
                if comp.get('service') != 'Timerman':
                    print(f"  {i+1}. {comp.get('title')}: service={comp.get('service')}")

    except Exception as e:
        print(f"❌ Ошибка: {e}")


async def main():
    print("="*60)
    print("🧪 ТЕСТИРОВАНИЕ ПАРСЕРА TIMERMAN")
    print("="*60)
    print(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Запускаем все тесты последовательно
    await test_basic_fetch()
    await test_sport_filter()
    await test_city_filter()
    await test_period_filter()
    await test_combined_filters()
    await test_service_field()

    print("\n" + "="*60)
    print("✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
