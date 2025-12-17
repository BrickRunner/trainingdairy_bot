"""
Тест парсера reg.place
"""

import asyncio
import sys
import io

# Установка правильной кодировки для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from competitions.regplace_parser import fetch_competitions

async def test_parser():
    """Тестируем парсер reg.place"""

    print("="*60)
    print("ТЕСТ ПАРСЕРА REG.PLACE")
    print("="*60)

    # Получаем все соревнования
    print("\n1. Получаем ВСЕ события:")
    all_comps = await fetch_competitions(sport="all", limit=100)
    print(f"   Получено: {len(all_comps)} событий")

    if all_comps:
        print(f"\n   Примеры событий:")
        for comp in all_comps[:5]:
            print(f"   - {comp.get('title', 'Unknown')}")
            print(f"     Город: {comp.get('city', 'N/A')}")
            print(f"     Дата: {comp.get('date', 'N/A')}")
            print(f"     Спорт: {comp.get('sport_code', 'N/A')}")
            print(f"     Дистанций: {len(comp.get('distances', []))}")
            print(f"     URL: {comp.get('url', 'N/A')}")
            print()
    else:
        print("   ⚠️ Не удалось получить события")

    # Группируем по спорту
    if all_comps:
        by_sport = {}
        for comp in all_comps:
            sport = comp.get('sport_code', 'unknown')
            by_sport.setdefault(sport, []).append(comp)

        print("\n2. Распределение по типам:")
        for sport, items in sorted(by_sport.items()):
            print(f"   - {sport}: {len(items)} событий")

    # Проверяем бег
    print("\n3. Получаем только БЕГ:")
    run_comps = await fetch_competitions(sport="run", limit=50)
    print(f"   Получено: {len(run_comps)} событий")

    if run_comps:
        print(f"\n   Примеры:")
        for comp in run_comps[:3]:
            print(f"   - {comp.get('title', 'Unknown')}")

    print("\n" + "="*60)
    print("ТЕСТ ЗАВЕРШЕН")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_parser())
