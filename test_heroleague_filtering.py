"""
Тест фильтрации событий от HeroLeague
Проверяем что события корректно фильтруются по типу
"""

import asyncio
import sys
import io
from competitions.heroleague_parser import fetch_competitions

# Установка правильной кодировки для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

async def test_filtering():
    """Проверяем фильтрацию событий"""

    print("="*60)
    print("ТЕСТ ФИЛЬТРАЦИИ СОБЫТИЙ ОТ HEROLEAGUE")
    print("="*60)

    # Получаем все соревнования без фильтра
    print("\n1. Получаем ВСЕ события (sport='all'):")
    all_comps = await fetch_competitions(sport="all", limit=100)
    print(f"   Получено: {len(all_comps)} событий")

    # Группируем по sport_code
    by_sport = {}
    for comp in all_comps:
        sport = comp.get('sport_code', 'unknown')
        by_sport.setdefault(sport, []).append(comp)

    print("\n   Распределение по типам:")
    for sport, items in sorted(by_sport.items()):
        print(f"   - {sport}: {len(items)} событий")

    # Получаем только бег
    print("\n2. Получаем только БЕГ (sport='run'):")
    run_comps = await fetch_competitions(sport="run", limit=100)
    print(f"   Получено: {len(run_comps)} событий")

    # Проверяем что все run
    non_run = [c for c in run_comps if c.get('sport_code') != 'run']
    if non_run:
        print(f"   ⚠️ ВНИМАНИЕ: Найдены не-run события: {[c.get('sport_code') for c in non_run]}")
    else:
        print("   ✅ Все события имеют sport_code='run'")

    # Проверяем что camp исключен из all
    print("\n3. Проверяем исключение 'camp' из фильтра 'all':")
    camp_in_all = [c for c in all_comps if c.get('sport_code') == 'camp']
    print(f"   События 'camp' в фильтре 'all': {len(camp_in_all)}")
    if camp_in_all:
        print("   ❌ ОШИБКА: 'camp' не должен быть в фильтре 'all'")
        for c in camp_in_all[:3]:
            print(f"      - {c.get('title', 'Unknown')}")
    else:
        print("   ✅ 'camp' правильно исключен из 'all'")

    # Сравниваем количество
    print("\n4. Проверяем потерю данных:")
    total_sport = sum(len(items) for sport, items in by_sport.items() if sport != 'camp')
    print(f"   Всего спортивных событий (без camp): {total_sport}")
    print(f"   В фильтре 'all': {len(all_comps)}")

    if total_sport == len(all_comps):
        print("   ✅ Данные не теряются")
    else:
        diff = total_sport - len(all_comps)
        print(f"   ⚠️ Разница: {diff} событий")

    # Примеры событий каждого типа
    print("\n5. Примеры событий по типам:")
    for sport in sorted(by_sport.keys()):
        items = by_sport[sport]
        print(f"\n   {sport.upper()} ({len(items)} событий):")
        for comp in items[:2]:
            title = comp.get('title', 'Unknown')
            print(f"   - {title[:60]}")

    print("\n" + "="*60)
    print("ТЕСТ ЗАВЕРШЕН")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_filtering())
