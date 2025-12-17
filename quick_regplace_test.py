"""
Быстрый тест API reg.place
"""

import requests
import json

BASE_URL = "https://api.reg.place/v1"

# Тестируем различные endpoint'ы
endpoints = [
    "/events",
    "/events/list",
    "/competitions",
    "/races",
    "/calendar",
]

print("="*60)
print("ТЕСТ API REG.PLACE")
print("="*60)

for endpoint in endpoints:
    url = BASE_URL + endpoint
    print(f"\nТестируем: {url}")
    print("-"*60)

    try:
        response = requests.get(url, timeout=10)
        print(f"Статус: {response.status_code}")

        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Получен JSON")
                print(f"Тип: {type(data).__name__}")

                if isinstance(data, list):
                    print(f"Список из {len(data)} элементов")
                    if data:
                        print(f"\nПервый элемент:")
                        print(json.dumps(data[0], indent=2, ensure_ascii=False)[:500])
                elif isinstance(data, dict):
                    print(f"Объект с ключами: {list(data.keys())}")
                    print(f"\nСодержимое:")
                    print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
            except:
                print(f"Ответ (не JSON): {response.text[:200]}")
        else:
            print(f"Ошибка: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

print("\n" + "="*60)
print("ТЕСТ ЗАВЕРШЕН")
print("="*60)
