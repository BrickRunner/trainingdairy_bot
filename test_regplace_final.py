"""
Финальный тест reg.place через созданный парсер
"""

import asyncio
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from competitions.regplace_parser import fetch_competitions

async def test():
    print("\n" + "="*60)
    print("ТЕСТ ПАРСЕРА REG.PLACE")
    print("="*60 + "\n")

    # Получаем события
    comps = await fetch_competitions(sport="all", limit=20)

    print(f"\nПолучено событий: {len(comps)}")

    if comps:
        print("\nПримеры:")
        for i, comp in enumerate(comps[:5], 1):
            print(f"\n{i}. {comp.get('title', 'N/A')}")
            print(f"   Город: {comp.get('city', 'N/A')}")
            print(f"   Дата: {comp.get('date', 'N/A')}")
            print(f"   Спорт: {comp.get('sport_code', 'N/A')}")
            print(f"   Сервис: {comp.get('service', 'N/A')}")
            print(f"   URL: {comp.get('url', 'N/A')}")

            distances = comp.get('distances', [])
            if distances:
                print(f"   Дистанции: {len(distances)}")
                for d in distances[:3]:
                    print(f"     - {d}")
    else:
        print("\n⚠️ События не получены. Проверьте логи выше.")

    print("\n" + "="*60)
    print("ТЕСТ ЗАВЕРШЕН")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(test())
