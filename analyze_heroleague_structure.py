"""
Анализ структуры данных API Лиги Героев
"""

import json
import sys
import io
from datetime import datetime

# Установка правильной кодировки для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def analyze_structure():
    """Детальный анализ структуры данных"""

    with open('heroleague_api_event_list_events.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("="*60)
    print("🔍 АНАЛИЗ СТРУКТУРЫ API ЛИГА ГЕРОЕВ")
    print("="*60)

    events = data.get('values', [])
    print(f"\nВсего типов событий: {len(events)}")

    # Анализ первого события
    if events:
        event = events[0]
        print("\n📋 Структура первого события:")
        print(f"   Title: {event.get('title')}")
        print(f"   Event Type: {event['event_type']['title']}")
        print(f"   Public ID: {event.get('public_id')}")
        print(f"   Description: {event.get('description', '')[:100]}...")
        print(f"   Cancel: {event.get('cancel')}")
        print(f"   Created: {event.get('created_date')}")

        # Города
        cities = event.get('event_city', [])
        print(f"\n🏙️ Количество городов: {len(cities)}")

        if cities:
            city = cities[0]
            print(f"\n📍 Первый город:")
            print(f"   City: {city['city']['name_ru']}")
            print(f"   Address: {city.get('address')}")
            print(f"   Start Time: {city.get('start_time')}")
            print(f"   Registration Open: {city.get('registration_open')}")
            print(f"   Registration Close: {city.get('registration_close')}")
            print(f"   Public ID: {city.get('public_id')}")
            print(f"   Timezone: {city.get('timezone')}")

            # Проверяем наличие дистанций
            print(f"\n   Ключи в city: {list(city.keys())}")

    # Ищем события с дистанциями
    print("\n\n" + "="*60)
    print("🔍 ПОИСК ДИСТАНЦИЙ В СОБЫТИЯХ")
    print("="*60)

    for i, event in enumerate(events):
        print(f"\n{i+1}. {event.get('title')} ({event['event_type']['title']})")
        print(f"   Description: {event.get('description', 'N/A')}")

        # Проверяем каждый город
        for city in event.get('event_city', []):
            city_name = city['city']['name_ru']

            # Ищем дистанции во всех возможных местах
            distances = []

            if 'distances' in city:
                distances = city['distances']
                print(f"   ✅ {city_name}: найдено {len(distances)} дистанций в 'distances'")
            elif 'distance' in city:
                distances = city['distance'] if isinstance(city['distance'], list) else [city['distance']]
                print(f"   ✅ {city_name}: найдено {len(distances)} дистанций в 'distance'")
            elif 'categories' in city:
                distances = city['categories']
                print(f"   ✅ {city_name}: найдено {len(distances)} категорий в 'categories'")

            if distances and len(distances) > 0:
                print(f"      Первая дистанция/категория: {json.dumps(distances[0], ensure_ascii=False)[:200]}")

if __name__ == "__main__":
    analyze_structure()
