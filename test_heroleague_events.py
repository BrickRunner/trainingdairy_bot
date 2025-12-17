"""
Тест различных endpoint'ов Лиги Героев для поиска событий
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

async def test_endpoints():
    """Тестируем различные endpoints"""

    base_url = "https://heroleague.ru"

    # Список возможных endpoints для событий
    endpoints = [
        "/api/event/list",
        "/api/events",
        "/api/events/list",
        "/api/calendar",
        "/api/calendar/events",
        "/api/competition/list",
        "/api/competitions",
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://heroleague.ru/calendar",
    }

    print("="*60)
    print("🔍 ПОИСК ENDPOINT ДЛЯ СОБЫТИЙ ЛИГИ ГЕРОЕВ")
    print("="*60)

    async with aiohttp.ClientSession(headers=headers) as session:
        for endpoint in endpoints:
            url = base_url + endpoint

            print(f"\n📡 Проверяю: {url}")

            try:
                # Пробуем GET
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    print(f"   GET Статус: {resp.status}")

                    if resp.status == 200:
                        content_type = resp.headers.get('Content-Type', '')

                        if 'json' in content_type:
                            data = await resp.json()
                            print(f"   ✅ НАЙДЕН JSON!")
                            print(f"   Тип данных: {type(data)}")

                            if isinstance(data, dict):
                                print(f"   Ключи: {list(data.keys())[:10]}")

                                # Ищем массивы с событиями
                                for key in ['events', 'values', 'data', 'items', 'list']:
                                    if key in data and isinstance(data[key], list):
                                        print(f"\n   🎯 Найден массив '{key}' с {len(data[key])} элементами")

                                        if len(data[key]) > 0:
                                            print(f"   Первый элемент:")
                                            print(f"   {json.dumps(data[key][0], ensure_ascii=False, indent=6)[:500]}")

                                            # Сохраняем
                                            filename = endpoint.replace('/', '_') + '_events.json'
                                            with open(f'heroleague{filename}', 'w', encoding='utf-8') as f:
                                                json.dump(data, f, ensure_ascii=False, indent=2)
                                            print(f"   💾 Сохранено в heroleague{filename}")

                                            return url, data

                            elif isinstance(data, list):
                                print(f"   📋 Массив с {len(data)} элементами")
                                if len(data) > 0:
                                    print(f"   Первый элемент:")
                                    print(f"   {json.dumps(data[0], ensure_ascii=False, indent=6)[:500]}")

                                    # Сохраняем
                                    filename = endpoint.replace('/', '_') + '_events.json'
                                    with open(f'heroleague{filename}', 'w', encoding='utf-8') as f:
                                        json.dump(data, f, ensure_ascii=False, indent=2)
                                    print(f"   💾 Сохранено в heroleague{filename}")

                                    return url, data
                        else:
                            print(f"   ⚠️ Не JSON: {content_type}")

                    elif resp.status == 404:
                        print(f"   ❌ 404 Not Found")
                    else:
                        print(f"   ⚠️ Статус {resp.status}")

            except asyncio.TimeoutError:
                print(f"   ⏱️ Timeout")
            except Exception as e:
                print(f"   ❌ Ошибка: {type(e).__name__}")

    print("\n" + "="*60)
    print("❌ Автоматически endpoint не найден")
    print("\n📝 Пожалуйста, проверьте в браузере:")
    print("1. Откройте https://heroleague.ru/calendar")
    print("2. F12 → Network → XHR/Fetch")
    print("3. Найдите запрос со списком соревнований")
    print("4. Скопируйте URL и пример ответа")
    print("="*60)

    return None, None

if __name__ == "__main__":
    asyncio.run(test_endpoints())
