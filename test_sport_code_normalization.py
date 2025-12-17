"""
Тест нормализации sport_code для HeroLeague
"""

import asyncio
import sys
import io
from competitions.heroleague_parser import fetch_competitions, normalize_sport_code

# Установка правильной кодировки для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

async def test_normalization():
    """Проверяем нормализацию sport_code"""

    print("="*60)
    print("ТЕСТ НОРМАЛИЗАЦИИ SPORT_CODE")
    print("="*60)

    # Тестовые случаи
    test_cases = [
        ("gonka", "run"),
        ("gonka_zima", "run"),
        ("zabeg", "run"),
        ("doroga", "run"),
        ("arcticmarathon", "run"),
        ("marathon", "run"),
        ("skirun", "ski"),
        ("snowrun", "ski"),
        ("bike", "bike"),
        ("swim", "swim"),
        ("triathlon", "triathlon"),
        ("camp", "camp"),  # Не спортивное - должен остаться как есть
    ]

    print("\nТестирование функции normalize_sport_code:")
    all_ok = True
    for original, expected in test_cases:
        result = normalize_sport_code(original)
        status = "✅" if result == expected else "❌"
        if result != expected:
            all_ok = False
        print(f"{status} {original} → {result} (ожидалось: {expected})")

    print("\n" + "="*60)
    print("ПРОВЕРКА РЕАЛЬНЫХ ДАННЫХ")
    print("="*60)

    # Получаем реальные данные
    comps = await fetch_competitions(limit=100)

    # Группируем по sport_code
    by_sport = {}
    for comp in comps:
        sport = comp.get('sport_code', 'unknown')
        by_sport.setdefault(sport, []).append(comp)

    print("\nРаспределение соревнований по нормализованным sport_code:")
    for sport, items in sorted(by_sport.items()):
        print(f"\n{sport}: {len(items)} соревнований")
        # Показываем примеры
        for comp in items[:2]:
            print(f"  • {comp['title'][:50]}")

    # Проверяем что нет нестандартных кодов
    standard_codes = ["run", "ski", "bike", "swim", "triathlon", "camp"]
    non_standard = [code for code in by_sport.keys() if code not in standard_codes]

    if non_standard:
        print(f"\n⚠️ Найдены нестандартные коды: {non_standard}")
        all_ok = False
    else:
        print("\n✅ Все коды нормализованы к стандартным")

    print("\n" + "="*60)
    if all_ok:
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ")
    else:
        print("❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ")
    print("="*60)

    return all_ok

if __name__ == "__main__":
    asyncio.run(test_normalization())
