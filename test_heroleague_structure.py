"""
Проверка структуры данных от HeroLeague парсера
"""

import asyncio
import json
import sys
import io
from competitions.heroleague_parser import fetch_competitions

# Установка правильной кодировки для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

async def test_structure():
    """Проверяем, что все необходимые поля присутствуют"""

    print("Получаем 1 соревнование от HeroLeague...")
    comps = await fetch_competitions(limit=1)

    if not comps:
        print("❌ Не получено ни одного соревнования")
        return

    comp = comps[0]

    print("\n" + "="*60)
    print("СТРУКТУРА СОРЕВНОВАНИЯ ОТ HEROLEAGUE")
    print("="*60)

    required_fields = [
        'id', 'title', 'code', 'city', 'place', 'sport_code',
        'organizer', 'service', 'begin_date', 'end_date',
        'formatted_date', 'url', 'distances'
    ]

    print("\nПроверка обязательных полей:")
    all_ok = True
    for field in required_fields:
        present = field in comp
        value = comp.get(field, "ОТСУТСТВУЕТ")
        status = "✅" if present else "❌"
        print(f"{status} {field}: {value}")
        all_ok = all_ok and present

    print("\nДополнительные поля:")
    extra_fields = ['description', 'event_type', 'registration_open',
                    'registration_close', 'distances_text']
    for field in extra_fields:
        if field in comp:
            value = comp[field]
            if isinstance(value, str) and len(value) > 50:
                value = value[:50] + "..."
            print(f"  • {field}: {value}")

    print("\n" + "="*60)
    print("ПОЛНАЯ СТРУКТУРА (JSON):")
    print("="*60)
    print(json.dumps(comp, ensure_ascii=False, indent=2))

    print("\n" + "="*60)
    if all_ok:
        print("✅ ВСЕ ОБЯЗАТЕЛЬНЫЕ ПОЛЯ ПРИСУТСТВУЮТ")
    else:
        print("❌ ОТСУТСТВУЮТ НЕКОТОРЫЕ ПОЛЯ")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_structure())
