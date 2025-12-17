"""
Проверка данных марафона "Дорога жизни"
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

async def check_doroga():
    """Ищем марафон Дорога жизни"""

    print("Получаем все соревнования от HeroLeague...")
    comps = await fetch_competitions(limit=100)

    print(f"\nВсего соревнований: {len(comps)}")

    # Ищем "Дорога жизни"
    doroga_comps = [c for c in comps if 'дорога' in c.get('title', '').lower()]

    print(f"Найдено соревнований 'Дорога жизни': {len(doroga_comps)}")

    for comp in doroga_comps:
        print("\n" + "="*60)
        print("МАРАФОН ДОРОГА ЖИЗНИ")
        print("="*60)
        print(json.dumps(comp, ensure_ascii=False, indent=2))

    # Также проверим все sport_code
    print("\n" + "="*60)
    print("ВСЕ УНИКАЛЬНЫЕ SPORT_CODES")
    print("="*60)

    sport_codes = set(c.get('sport_code', 'unknown') for c in comps)
    for code in sorted(sport_codes):
        count = sum(1 for c in comps if c.get('sport_code') == code)
        print(f"  {code}: {count} соревнований")

if __name__ == "__main__":
    asyncio.run(check_doroga())
