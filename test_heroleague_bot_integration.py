"""
Тест интеграции HeroLeague с ботом - проверка что обработчики работают корректно
"""

import asyncio
import sys
import io
from competitions.competitions_fetcher import fetch_all_competitions

# Установка правильной кодировки для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

async def test_fetch_heroleague():
    """Получаем соревнования только от HeroLeague"""
    print("\n" + "="*60)
    print("ТЕСТ 1: Получение соревнований HeroLeague")
    print("="*60)

    comps = await fetch_all_competitions(
        city="Москва",
        service="HeroLeague",
        limit=3
    )

    print(f"\nПолучено соревнований: {len(comps)}")

    for i, comp in enumerate(comps, 1):
        print(f"\n{i}. {comp['title']}")
        print(f"   ID: {comp['id']}")
        print(f"   Сервис: {comp['service']}")
        print(f"   Город: {comp['city']}")
        print(f"   Дата: {comp.get('formatted_date', 'N/A')}")
        print(f"   begin_date: {comp.get('begin_date', 'N/A')}")
        print(f"   end_date: {comp.get('end_date', 'N/A')}")
        print(f"   distances: {comp.get('distances', 'N/A')}")
        print(f"   distances_text: {comp.get('distances_text', 'N/A')[:60]}...")
        print(f"   url: {comp.get('url', 'N/A')}")

    return len(comps) > 0

async def test_all_services_mixed():
    """Получаем соревнования от всех сервисов и проверяем что HeroLeague включен"""
    print("\n" + "="*60)
    print("ТЕСТ 2: Все сервисы вместе")
    print("="*60)

    comps = await fetch_all_competitions(
        city="Москва",
        service="all",
        limit=15
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

    # Проверяем что HeroLeague присутствует
    has_heroleague = 'HeroLeague' in by_service
    if has_heroleague:
        print("\n✅ HeroLeague соревнования присутствуют в общем списке")

        # Показываем примеры
        print("\nПримеры от HeroLeague:")
        for comp in by_service['HeroLeague'][:2]:
            print(f"  • {comp['title']} ({comp.get('formatted_date', 'N/A')})")
    else:
        print("\n❌ HeroLeague соревнования НЕ найдены в общем списке")

    return has_heroleague

async def test_field_compatibility():
    """Проверяем что все соревнования имеют необходимые поля"""
    print("\n" + "="*60)
    print("ТЕСТ 3: Совместимость полей")
    print("="*60)

    comps = await fetch_all_competitions(
        service="all",
        limit=20
    )

    required_fields = ['id', 'title', 'city', 'begin_date', 'end_date', 'distances', 'url', 'service']

    print(f"\nПроверяем {len(comps)} соревнований...\n")

    all_ok = True
    for comp in comps:
        service = comp.get('service', 'Unknown')
        missing = []

        for field in required_fields:
            if field not in comp:
                missing.append(field)

        if missing:
            print(f"❌ {service}: {comp.get('title', 'N/A')[:40]}")
            print(f"   Отсутствуют поля: {', '.join(missing)}")
            all_ok = False

    if all_ok:
        print("✅ Все соревнования имеют необходимые поля")
    else:
        print("\n❌ Некоторые соревнования имеют отсутствующие поля")

    return all_ok

async def run_all_tests():
    """Запустить все тесты"""
    print("\n" + "="*80)
    print("ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ HEROLEAGUE С БОТОМ")
    print("="*80)

    results = {
        "Получение HeroLeague": await test_fetch_heroleague(),
        "Все сервисы вместе": await test_all_services_mixed(),
        "Совместимость полей": await test_field_compatibility(),
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
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! HeroLeague готов к работе в боте.")
    else:
        print(f"\n⚠️ Некоторые тесты не прошли ({total - passed} failed)")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
