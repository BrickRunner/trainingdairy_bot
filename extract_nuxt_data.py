"""
Извлечение данных из Nuxt.js приложения timerman.org
"""

import requests
import re
import json

print("🔍 Извлечение данных из Nuxt.js приложения\n")

# Пробуем получить страницу с событиями
urls_to_check = [
    "https://timerman.org/events",
    "https://timerman.org/",
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9",
}

for url in urls_to_check:
    try:
        print(f"\n{'='*60}")
        print(f"Проверяю: {url}")

        response = requests.get(url, headers=headers, timeout=15)
        html = response.text

        print(f"Статус: {response.status_code}")
        print(f"Размер HTML: {len(html)} байт")

        # Ищем встроенные данные Nuxt
        patterns = [
            (r'window\.__NUXT__\s*=\s*({.+?});', '__NUXT__'),
            (r'window\.__NUXT_DATA__\s*=\s*({.+?});', '__NUXT_DATA__'),
            (r'"__NUXT_JSONP__"[^{]*({.+?})\)', '__NUXT_JSONP__'),
        ]

        found_data = False

        for pattern, name in patterns:
            matches = re.findall(pattern, html, re.DOTALL)
            if matches:
                print(f"\n✅ Найдены данные {name}!")
                for i, match in enumerate(matches[:1]):  # Берем первое совпадение
                    print(f"\nДанные (первые 1000 символов):")
                    print(match[:1000])

                    # Пробуем распарсить как JSON
                    try:
                        data = json.loads(match)
                        print(f"\n✅ Успешно распарсено как JSON!")
                        print(f"Ключи верхнего уровня: {list(data.keys())[:10]}")

                        # Сохраняем в файл
                        filename = f"nuxt_data_{name.lower()}.json"
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        print(f"💾 Сохранено в {filename}")

                        # Ищем события в данных
                        def find_events(obj, path=""):
                            """Рекурсивно ищем массивы с событиями"""
                            if isinstance(obj, dict):
                                for key, value in obj.items():
                                    if key in ['events', 'competitions', 'items', 'data', 'list']:
                                        if isinstance(value, list) and len(value) > 0:
                                            print(f"\n🎯 Найден массив '{key}' по пути: {path}.{key}")
                                            print(f"   Элементов: {len(value)}")
                                            if len(value) > 0:
                                                print(f"   Первый элемент: {json.dumps(value[0], ensure_ascii=False, indent=2)[:500]}")
                                    find_events(value, f"{path}.{key}")
                            elif isinstance(obj, list):
                                for i, item in enumerate(obj[:3]):  # Проверяем первые 3 элемента
                                    find_events(item, f"{path}[{i}]")

                        find_events(data)
                        found_data = True

                    except json.JSONDecodeError as e:
                        print(f"⚠️ Не удалось распарсить как JSON: {e}")

        # Ищем упоминания API endpoints
        api_patterns = [
            r'["\'](/api/[^"\']+)["\']',
            r'https://timerman\.org/api/[^\s"\']+',
            r'https://api\.timerman\.org/[^\s"\']+',
        ]

        print(f"\n🔍 Поиск API endpoints в HTML...")
        for pattern in api_patterns:
            endpoints = re.findall(pattern, html)
            if endpoints:
                unique_endpoints = list(set(endpoints))[:10]
                print(f"\nНайденные endpoints (паттерн: {pattern}):")
                for ep in unique_endpoints:
                    print(f"  - {ep}")

        if not found_data:
            print("\n⚠️ Не найдены встроенные данные Nuxt")
            print("Возможно сайт загружает данные через отдельный API запрос")

    except Exception as e:
        print(f"❌ Ошибка: {e}")

print("\n" + "="*60)
print("\n📝 Следующие шаги:")
print("1. Если найдены данные - отлично! Проверьте JSON файлы")
print("2. Если найдены API endpoints - попробуйте их запросить")
print("3. Если ничего не найдено - проверьте Network в браузере")
