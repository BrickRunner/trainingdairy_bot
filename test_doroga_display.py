"""
Проверка отображения марафона "Дорога жизни"
"""

import asyncio
import sys
import io
from competitions.heroleague_parser import fetch_competitions

# Установка правильной кодировки для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Импортируем SPORT_NAMES из parser
from competitions.parser import SPORT_NAMES

async def test_doroga_display():
    """Проверяем как будет отображаться марафон Дорога жизни"""

    print("="*60)
    print("ТЕСТ ОТОБРАЖЕНИЯ МАРАФОНА 'ДОРОГА ЖИЗНИ'")
    print("="*60)

    # Получаем все соревнования
    comps = await fetch_competitions(limit=100)

    # Ищем марафон
    doroga = next((c for c in comps if 'дорога' in c.get('title', '').lower()), None)

    if not doroga:
        print("❌ Марафон 'Дорога жизни' не найден")
        return False

    print("\nНайден марафон:")
    print(f"  Название: {doroga['title']}")
    print(f"  sport_code: {doroga['sport_code']}")
    print(f"  Город: {doroga['city']}")
    print(f"  Дата: {doroga.get('formatted_date', 'N/A')}")

    # Проверяем sport_code
    sport_code = doroga['sport_code']
    sport_name_ru = SPORT_NAMES.get(sport_code, sport_code)

    print(f"\n✅ sport_code нормализован: '{sport_code}' → '{sport_name_ru}'")

    # Проверяем дистанции
    has_distances = bool(doroga.get('distances'))
    has_distances_text = bool(doroga.get('distances_text'))

    print(f"\nДистанции:")
    print(f"  distances (структурированные): {len(doroga.get('distances', []))} шт.")
    print(f"  distances_text (текстовые): {'Да' if has_distances_text else 'Нет'}")

    if has_distances_text:
        print(f"\nТекст дистанций:")
        print(f"  {doroga['distances_text'][:150]}...")

    # Симуляция отображения в боте
    print("\n" + "="*60)
    print("КАК БУДЕТ ОТОБРАЖАТЬСЯ В БОТЕ:")
    print("="*60)

    text = (
        f"🏆 <b>{doroga['title']}</b>\n\n"
        f"📅 Дата: {doroga.get('formatted_date', 'N/A')}\n"
        f"📍 Место: {doroga['place']}\n"
        f"🏃 Вид спорта: {sport_name_ru}\n"
    )

    # Дистанции (как в обработчике)
    if doroga.get('distances'):
        text += f"\n<b>📏 Дистанции:</b>\n"
        for dist in doroga['distances'][:10]:
            text += f"  • {dist.get('name', 'Дистанция')}\n"
    elif doroga.get('distances_text'):
        text += f"\n<b>📏 Дистанции:</b>\n{doroga['distances_text']}\n"

    if doroga.get('url'):
        text += f"\n🔗 <a href=\"{doroga['url']}\">Подробнее на сайте</a>"

    # Убираем HTML теги для вывода
    display_text = text.replace('<b>', '').replace('</b>', '')
    display_text = display_text.replace('<a href="', '').replace('">', ' - ').replace('</a>', '')

    print(display_text)

    print("\n" + "="*60)

    # Проверки
    checks = {
        "sport_code нормализован": sport_code == "run",
        "sport_name корректный": sport_name_ru == "Бег",
        "distances_text присутствует": has_distances_text,
        "url присутствует": bool(doroga.get('url')),
    }

    print("РЕЗУЛЬТАТЫ ПРОВЕРОК:")
    all_ok = True
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check}")
        all_ok = all_ok and result

    print("\n" + "="*60)
    if all_ok:
        print("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ")
    else:
        print("❌ НЕКОТОРЫЕ ПРОВЕРКИ НЕ ПРОШЛИ")
    print("="*60)

    return all_ok

if __name__ == "__main__":
    asyncio.run(test_doroga_display())
