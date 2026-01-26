"""
Тестовый скрипт для проверки работы парсера RunC
"""

import asyncio
import sys
import logging

# Настройка кодировки для Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from competitions.runc_parser import fetch_competitions, get_competition_details


async def test_runc_parser():
    """Тестирование парсера RunC"""
    print("=" * 80)
    print("Тестирование парсера RunC")
    print("=" * 80)

    # Тест 1: Получение всех соревнований (без фильтров)
    print("\n[Тест 1] Получение соревнований без фильтров (лимит 10)")
    print("-" * 80)
    try:
        competitions = await fetch_competitions(limit=10)
        print(f"✅ Получено соревнований: {len(competitions)}")

        if competitions:
            print("\nПример первого соревнования:")
            comp = competitions[0]
            print(f"  ID: {comp.get('id')}")
            print(f"  Название: {comp.get('title')}")
            print(f"  Город: {comp.get('city')}")
            print(f"  Дата: {comp.get('formatted_date')}")
            print(f"  Спорт: {comp.get('sport_code')}")
            print(f"  Дистанции: {comp.get('distances_text')}")
            print(f"  URL: {comp.get('url')}")
        else:
            print("⚠️  Соревнования не найдены")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

    # Тест 2: Фильтрация по городу
    print("\n[Тест 2] Фильтрация по городу 'Москва'")
    print("-" * 80)
    try:
        moscow_comps = await fetch_competitions(city="Москва", limit=5)
        print(f"✅ Получено соревнований в Москве: {len(moscow_comps)}")

        for i, comp in enumerate(moscow_comps, 1):
            print(f"  {i}. {comp.get('title')} - {comp.get('formatted_date')}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

    # Тест 3: Фильтрация по виду спорта
    print("\n[Тест 3] Фильтрация по виду спорта 'run'")
    print("-" * 80)
    try:
        run_comps = await fetch_competitions(sport="run", limit=5)
        print(f"✅ Получено беговых соревнований: {len(run_comps)}")

        for i, comp in enumerate(run_comps, 1):
            print(f"  {i}. {comp.get('title')} ({comp.get('sport_code')})")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

    # Тест 4: Получение детальной информации о соревновании
    print("\n[Тест 4] Получение детальной информации о соревновании")
    print("-" * 80)
    try:
        # Получаем первое соревнование для теста
        competitions = await fetch_competitions(limit=1)
        if competitions:
            comp_url = competitions[0].get('url')
            comp_title = competitions[0].get('title')
            print(f"Получаем детали для: {comp_title}")
            print(f"URL: {comp_url}")

            details = await get_competition_details(comp_url)

            if details:
                print(f"✅ Детали получены:")
                print(f"  Название: {details.get('title')}")
                print(f"  Город: {details.get('city')}")
                print(f"  Дата: {details.get('formatted_date')}")
                print(f"  Дистанции ({len(details.get('distances', []))} шт):")
                for dist in details.get('distances', []):
                    print(f"    - {dist.get('name')} ({dist.get('distance')} км)")
            else:
                print("⚠️  Не удалось получить детальную информацию")
        else:
            print("⚠️  Нет соревнований для теста")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)
    print("Тестирование завершено!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_runc_parser())
