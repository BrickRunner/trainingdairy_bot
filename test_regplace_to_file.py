"""
Тест reg.place с сохранением в файл
"""

import asyncio
import logging
import json

# Настройка логирования в файл
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('regplace_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

from competitions.regplace_parser import fetch_competitions

async def test():
    result_lines = []
    result_lines.append("="*60)
    result_lines.append("ТЕСТ ПАРСЕРА REG.PLACE")
    result_lines.append("="*60)

    # Получаем события
    comps = await fetch_competitions(sport="all", limit=20)

    result_lines.append(f"\nПолучено событий: {len(comps)}")

    if comps:
        result_lines.append("\nПримеры:")
        for i, comp in enumerate(comps[:5], 1):
            result_lines.append(f"\n{i}. {comp.get('title', 'N/A')}")
            result_lines.append(f"   Город: {comp.get('city', 'N/A')}")
            result_lines.append(f"   Дата: {comp.get('date', 'N/A')}")
            result_lines.append(f"   Спорт: {comp.get('sport_code', 'N/A')}")
            result_lines.append(f"   Сервис: {comp.get('service', 'N/A')}")
            result_lines.append(f"   URL: {comp.get('url', 'N/A')}")

            distances = comp.get('distances', [])
            if distances:
                result_lines.append(f"   Дистанции: {len(distances)}")
                for d in distances[:3]:
                    result_lines.append(f"     - {d}")
    else:
        result_lines.append("\n⚠️ События не получены. Проверьте логи.")

    result_lines.append("\n" + "="*60)
    result_lines.append("ТЕСТ ЗАВЕРШЕН")
    result_lines.append("="*60)

    # Сохраняем в файл
    with open('regplace_test_results.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(result_lines))

    print("Результаты сохранены в regplace_test_results.txt")

if __name__ == "__main__":
    asyncio.run(test())
