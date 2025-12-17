"""
Тестирование API reg.place для поиска списка событий
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

BASE_URL = "https://api.reg.place/v1"

async def test_events_list():
    """Ищем endpoint для списка событий"""

    print("="*60)
    print("ПОИСК ENDPOINT ДЛЯ СПИСКА СОБЫТИЙ REG.PLACE")
    print("="*60)

    # Возможные endpoint'ы для списка событий
    endpoints = [
        "/events",
        "/events/list",
        "/events/upcoming",
        "/events/search",
        "/calendar",
        "/search/events",
    ]

    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints:
            url = BASE_URL + endpoint
            print(f"\n{'='*60}")
            print(f"Тестируем: {endpoint}")
            print('='*60)

            try:
                async with session.get(url, timeout=10) as response:
                    print(f"Статус: {response.status}")

                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        print(f"Content-Type: {content_type}")

                        if 'application/json' in content_type:
                            data = await response.json()
                            print(f"\n✅ УСПЕХ! Получен JSON")

                            if isinstance(data, list):
                                print(f"📋 Список из {len(data)} элементов")
                                if data:
                                    print(f"\nПример первого события:")
                                    print(json.dumps(data[0], indent=2, ensure_ascii=False)[:1000])
                                    print("\n...")
                            elif isinstance(data, dict):
                                print(f"📦 Объект с ключами: {list(data.keys())}")

                                # Ищем ключ с массивом событий
                                for key, value in data.items():
                                    if isinstance(value, list) and len(value) > 0:
                                        print(f"\n🔍 Найден массив в ключе '{key}': {len(value)} элементов")
                                        if isinstance(value[0], dict):
                                            print(f"   Ключи первого элемента: {list(value[0].keys())}")

                                print(f"\nПример структуры:")
                                print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
                                print("\n...")
                        else:
                            text = await response.text()
                            print(f"Не JSON. Первые 200 символов:")
                            print(text[:200])

                    elif response.status == 404:
                        print("❌ Не найден (404)")
                    else:
                        print(f"❌ Ошибка {response.status}")
                        text = await response.text()
                        print(text[:200])

            except asyncio.TimeoutError:
                print("⏱ Timeout")
            except Exception as e:
                print(f"❌ Ошибка: {e}")

    print("\n" + "="*60)
    print("ТЕСТ ЗАВЕРШЕН")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_events_list())
