"""
Исследование API reg.place
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

async def test_endpoints():
    """Тестируем различные endpoint'ы"""

    print("="*60)
    print("ИССЛЕДОВАНИЕ API REG.PLACE")
    print("="*60)

    # Возможные endpoint'ы для событий
    endpoints = [
        "/events",
        "/competitions",
        "/races",
        "/calendar",
        "/event/list",
        "/event/search",
    ]

    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints:
            url = BASE_URL + endpoint
            print(f"\n\nПроверяем: {url}")
            print("-" * 60)

            try:
                async with session.get(url, timeout=10) as response:
                    print(f"Статус: {response.status}")

                    if response.status == 200:
                        try:
                            data = await response.json()
                            print(f"✅ УСПЕХ! Получен JSON")
                            print(f"Тип данных: {type(data)}")

                            if isinstance(data, list):
                                print(f"Список из {len(data)} элементов")
                                if data:
                                    print(f"\nПример первого элемента:")
                                    print(json.dumps(data[0], indent=2, ensure_ascii=False)[:500])
                            elif isinstance(data, dict):
                                print(f"Объект с ключами: {list(data.keys())}")
                                print(f"\nСодержимое:")
                                print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
                        except:
                            text = await response.text()
                            print(f"Ответ (не JSON): {text[:200]}")
                    else:
                        text = await response.text()
                        print(f"Ошибка: {text[:200]}")

            except asyncio.TimeoutError:
                print("⏱ Timeout")
            except Exception as e:
                print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(test_endpoints())
