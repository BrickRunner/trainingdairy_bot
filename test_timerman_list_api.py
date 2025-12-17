"""
Тест реального API timerman.org/api/events/list/ru
"""

import requests
import json

print("🔍 Тестирование API: https://timerman.org/api/events/list/ru\n")

url = "https://timerman.org/api/events/list/ru"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://timerman.org/events",
}

print(f"Запрос к: {url}\n")

try:
    # Пробуем GET
    print("Попытка GET запроса...")
    response = requests.get(url, headers=headers, timeout=15)

    print(f"Статус: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")

    if response.status_code == 200:
        data = response.json()

        print(f"\n✅ Успешно получены данные!")
        print(f"\nТип данных: {type(data)}")

        # Анализируем структуру
        if isinstance(data, dict):
            print(f"Ключи верхнего уровня: {list(data.keys())}")

            # Ищем массив событий
            for key in ['events', 'list', 'items', 'data', 'results']:
                if key in data:
                    events = data[key]
                    if isinstance(events, list):
                        print(f"\n🎯 Найден массив событий в ключе '{key}'")
                        print(f"Количество событий: {len(events)}")

                        if len(events) > 0:
                            print(f"\n📋 Структура первого события:")
                            first_event = events[0]
                            print(json.dumps(first_event, ensure_ascii=False, indent=2))

                            print(f"\n📋 Ключи события:")
                            print(list(first_event.keys()))
                        break

        elif isinstance(data, list):
            print(f"Данные - это массив")
            print(f"Количество событий: {len(data)}")

            if len(data) > 0:
                print(f"\n📋 Структура первого события:")
                first_event = data[0]
                print(json.dumps(first_event, ensure_ascii=False, indent=2))

                print(f"\n📋 Ключи события:")
                print(list(first_event.keys()))

        # Сохраняем полный ответ
        with open('timerman_events_response.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"\n💾 Полный ответ сохранен в timerman_events_response.json")

    else:
        print(f"\n❌ Ошибка: статус {response.status_code}")
        print(f"Ответ: {response.text[:500]}")

except Exception as e:
    print(f"\n❌ Ошибка: {type(e).__name__}: {e}")

print("\n" + "="*60)

# Пробуем также POST если GET не сработал
print("\nПопытка POST запроса...")

try:
    response = requests.post(url, headers=headers, json={}, timeout=15)
    print(f"Статус POST: {response.status_code}")

    if response.status_code == 200:
        print("✅ POST запрос успешен")
        data = response.json()
        print(f"Получено событий: {len(data) if isinstance(data, list) else 'N/A'}")

except Exception as e:
    print(f"POST ошибка: {type(e).__name__}")
