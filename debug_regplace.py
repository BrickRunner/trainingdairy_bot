"""
Отладка reg.place - смотрим реальную структуру данных
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

async def debug_api():
    """Получаем реальные данные от API и смотрим структуру"""

    print("="*60)
    print("ОТЛАДКА REG.PLACE API")
    print("="*60)

    BASE_URL = "https://api.reg.place/v1"
    endpoints = [
        f"{BASE_URL}/events",
        f"{BASE_URL}/event/list",
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        for endpoint in endpoints:
            print(f"\n{'='*60}")
            print(f"Проверяем: {endpoint}")
            print('='*60)

            try:
                async with session.get(endpoint, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    print(f"Статус: {response.status}")

                    if response.status == 200:
                        data = await response.json()
                        print(f"\n✅ УСПЕХ!")
                        print(f"Тип данных: {type(data).__name__}")

                        if isinstance(data, list):
                            print(f"Список из {len(data)} элементов")
                            if data:
                                print(f"\n📋 Первое событие:")
                                first = data[0]
                                print(json.dumps(first, indent=2, ensure_ascii=False))

                                print(f"\n🔑 Доступные ключи:")
                                for key in first.keys():
                                    value = first[key]
                                    value_type = type(value).__name__
                                    if isinstance(value, (list, dict)):
                                        print(f"  - {key}: {value_type} (длина/ключи: {len(value)})")
                                    else:
                                        print(f"  - {key}: {value_type} = {value}")

                        elif isinstance(data, dict):
                            print(f"Объект с ключами: {list(data.keys())}")

                            # Ищем массив событий
                            for key, value in data.items():
                                if isinstance(value, list):
                                    print(f"\n🔍 Найден массив в ключе '{key}': {len(value)} элементов")
                                    if value and isinstance(value[0], dict):
                                        print(f"\n📋 Первое событие из '{key}':")
                                        print(json.dumps(value[0], indent=2, ensure_ascii=False))
                                    break

                        # Сохраняем в файл
                        filename = f"regplace_debug_{endpoint.split('/')[-1]}.json"
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        print(f"\n💾 Данные сохранены в {filename}")

                        break  # Нашли рабочий endpoint

                    else:
                        print(f"❌ Ошибка {response.status}")

            except asyncio.TimeoutError:
                print("⏱ Timeout")
            except Exception as e:
                print(f"❌ Ошибка: {e}")

    print("\n" + "="*60)
    print("ОТЛАДКА ЗАВЕРШЕНА")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(debug_api())
