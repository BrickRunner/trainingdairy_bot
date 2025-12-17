"""
Поиск всех уникальных ключей в данных API Лиги Героев
"""

import json
import sys
import io

# Установка правильной кодировки для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def collect_all_keys(obj, path="", all_keys=None):
    """Рекурсивно собирает все ключи из вложенных объектов"""
    if all_keys is None:
        all_keys = set()

    if isinstance(obj, dict):
        for key, value in obj.items():
            full_path = f"{path}.{key}" if path else key
            all_keys.add(full_path)
            collect_all_keys(value, full_path, all_keys)
    elif isinstance(obj, list) and len(obj) > 0:
        # Проверяем первый элемент списка
        collect_all_keys(obj[0], f"{path}[0]", all_keys)

    return all_keys

with open('heroleague_api_event_list_events.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("="*60)
print("🔍 ВСЕ УНИКАЛЬНЫЕ КЛЮЧИ В API")
print("="*60)

all_keys = collect_all_keys(data)

# Фильтруем ключи, связанные с дистанциями
distance_keys = [k for k in all_keys if any(word in k.lower() for word in ['dist', 'categ', 'race', 'compet', 'ticket'])]

print("\n📋 Ключи, связанные с дистанциями/категориями/билетами:")
for key in sorted(distance_keys):
    print(f"   {key}")

print("\n\n📋 ВСЕ ключи event_city (первые 50):")
city_keys = [k for k in all_keys if k.startswith('values[0].event_city[0].')]
for key in sorted(city_keys)[:50]:
    print(f"   {key}")

# Проверим, есть ли в каком-то событии дистанции
print("\n\n🔍 Проверка каждого события на наличие дистанций...")

events = data.get('values', [])
for i, event in enumerate(events):
    title = event.get('title', 'N/A')
    event_type = event.get('event_type', {}).get('title', 'N/A')

    for j, city in enumerate(event.get('event_city', [])):
        city_name = city.get('city', {}).get('name_ru', 'N/A')
        start_time = city.get('start_time', 'N/A')

        # Собираем все ключи этого города
        city_keys = list(city.keys())

        # Ищем подозрительные ключи
        suspicious = [k for k in city_keys if any(word in k.lower() for word in ['dist', 'categ', 'race', 'ticket', 'compet'])]

        if suspicious:
            print(f"\n   ✅ {title} ({event_type})")
            print(f"      Город: {city_name}, Дата: {start_time}")
            print(f"      Найденные ключи: {suspicious}")
            for key in suspicious:
                value = city.get(key)
                print(f"         {key}: {type(value).__name__} = {str(value)[:100]}")
