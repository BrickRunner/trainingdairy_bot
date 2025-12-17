"""
Тест получения деталей конкретного события Лиги Героев
"""

import asyncio
import aiohttp
import json
import sys
import io

# Установка правильной кодировки для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

async def test_event_details():
    """Тестируем получение деталей события"""

    base_url = "https://heroleague.ru"

    # Public ID из первого события
    event_public_id = "skirun2025"
    city_public_id = "skirun2025_msc"

    # Возможные endpoints для деталей
    endpoints = [
        f"/api/event/{event_public_id}",
        f"/api/event/details/{event_public_id}",
        f"/api/event/{event_public_id}/distances",
        f"/api/event/{event_public_id}/categories",
        f"/api/event_city/{city_public_id}",
        f"/api/event_city/{city_public_id}/distances",
        f"/api/event_city/{city_public_id}/categories",
        f"/api/competition/{event_public_id}",
        f"/api/competition/{city_public_id}",
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://heroleague.ru/calendar",
    }

    print("="*60)
    print("🔍 ПОИСК ENDPOINT ДЛЯ ДЕТАЛЕЙ СОБЫТИЯ")
    print("="*60)
    print(f"\nEvent ID: {event_public_id}")
    print(f"City ID: {city_public_id}")

    async with aiohttp.ClientSession(headers=headers) as session:
        for endpoint in endpoints:
            url = base_url + endpoint

            print(f"\n📡 Проверяю: {endpoint}")

            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    print(f"   Статус: {resp.status}")

                    if resp.status == 200:
                        content_type = resp.headers.get('Content-Type', '')

                        if 'json' in content_type:
                            data = await resp.json()
                            print(f"   ✅ НАЙДЕН JSON!")
                            print(f"   Тип данных: {type(data)}")

                            if isinstance(data, dict):
                                print(f"   Ключи: {list(data.keys())[:10]}")

                                # Ищем дистанции
                                for key in ['distances', 'distance', 'categories', 'category', 'competitions', 'races']:
                                    if key in data:
                                        items = data[key]
                                        if isinstance(items, list):
                                            print(f"\n   🎯 Найден массив '{key}' с {len(items)} элементами")
                                            if len(items) > 0:
                                                print(f"   Первый элемент:")
                                                print(f"   {json.dumps(items[0], ensure_ascii=False, indent=6)[:500]}")

                                # Сохраняем
                                filename = endpoint.replace('/', '_') + '.json'
                                with open(f'heroleague{filename}', 'w', encoding='utf-8') as f:
                                    json.dump(data, f, ensure_ascii=False, indent=2)
                                print(f"   💾 Сохранено в heroleague{filename}")

                            elif isinstance(data, list):
                                print(f"   📋 Массив с {len(data)} элементами")
                                if len(data) > 0:
                                    print(f"   Первый элемент:")
                                    print(f"   {json.dumps(data[0], ensure_ascii=False, indent=6)[:500]}")

                    elif resp.status == 404:
                        print(f"   ❌ 404 Not Found")

            except asyncio.TimeoutError:
                print(f"   ⏱️ Timeout")
            except Exception as e:
                print(f"   ❌ Ошибка: {type(e).__name__}")

    print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(test_event_details())
