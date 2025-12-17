"""
Тест нормализации видов спорта в парсере Timerman
"""

import asyncio
import json
import sys
import io
from competitions.timerman_parser import TimmermanParser, matches_sport_type

# Установка правильной кодировки для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

async def main():
    print("="*60)
    print("🔍 ТЕСТ ВИДОВ СПОРТА TIMERMAN")
    print("="*60)

    async with TimmermanParser() as parser:
        # Получаем первые 10 соревнований
        data = await parser.get_events(skip=0, take=10)
        events = data.get("list", [])

        print(f"\n📊 Найдено {len(events)} соревнований")

        # Собираем статистику по видам спорта
        sports_info = []
        for event in events:
            info = {
                "title": event.get("t", ""),
                "discipline_code": event.get("dc", ""),
                "discipline_name": event.get("dn", ""),
                "race_items": []
            }

            # Проверяем дистанции
            for race in event.get("ri", []):
                info["race_items"].append({
                    "name": race.get("n", ""),
                    "discipline_code": race.get("dc", ""),
                    "discipline_name": race.get("dn", "")
                })

            sports_info.append(info)

        # Показываем результаты
        print("\n📋 ВИДЫ СПОРТА В СОРЕВНОВАНИЯХ:")
        print("-" * 60)
        for i, info in enumerate(sports_info, 1):
            print(f"\n{i}. {info['title']}")
            print(f"   Основная дисциплина: code='{info['discipline_code']}', name='{info['discipline_name']}'")

            if info['race_items']:
                print(f"   Дистанции:")
                for race in info['race_items']:
                    print(f"     - {race['name']}: code='{race['discipline_code']}', name='{race['discipline_name']}'")

        # Тестируем фильтрацию
        print("\n" + "="*60)
        print("🧪 ТЕСТИРОВАНИЕ ФИЛЬТРАЦИИ")
        print("="*60)

        for sport in ["run", "swim", "bike", "all"]:
            print(f"\n🔍 Фильтр: {sport}")
            matches = []
            for event in events:
                if matches_sport_type(event, sport):
                    matches.append(event.get("t", ""))

            print(f"   Найдено: {len(matches)} соревнований")
            if matches:
                for title in matches[:5]:
                    print(f"     - {title}")

    print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(main())
