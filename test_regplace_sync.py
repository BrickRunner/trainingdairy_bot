"""
Синхронный тест API reg.place с явным выводом
"""
import sys

print("Скрипт начал работу", flush=True)

try:
    import asyncio
    import aiohttp
    import json
    print("Импорты успешны", flush=True)

    BASE_URL = "https://api.reg.place/v1"

    async def test():
        print("\nНачинаем тест API", flush=True)
        print("="*60, flush=True)

        endpoints = ["/events", "/competitions", "/races"]

        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                url = BASE_URL + endpoint
                print(f"\nПроверяем: {url}", flush=True)

                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        print(f"Статус: {response.status}", flush=True)

                        if response.status == 200:
                            data = await response.json()
                            print(f"✅ Успех! Тип: {type(data).__name__}", flush=True)

                            if isinstance(data, list):
                                print(f"Список из {len(data)} элементов", flush=True)
                            elif isinstance(data, dict):
                                print(f"Объект с ключами: {list(data.keys())}", flush=True)
                        else:
                            text = await response.text()
                            print(f"Ошибка {response.status}: {text[:100]}", flush=True)

                except Exception as e:
                    print(f"Ошибка: {e}", flush=True)

        print("\n" + "="*60, flush=True)
        print("Тест завершен", flush=True)

    asyncio.run(test())

except Exception as e:
    print(f"Критическая ошибка: {e}", flush=True)
    import traceback
    traceback.print_exc()

print("Скрипт завершен", flush=True)
