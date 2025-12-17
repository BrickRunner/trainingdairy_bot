"""
Простой тест для поиска API timerman.org
"""

import requests
import json

print("🔍 Тестирование timerman.org API\n")

# Заголовки как в браузере
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    "Referer": "https://timerman.org/",
}

# Список возможных endpoints
endpoints_to_test = [
    ("GET", "https://timerman.org/api/events"),
    ("GET", "https://timerman.org/api/event"),
    ("GET", "https://timerman.org/api/calendar"),
    ("GET", "https://timerman.org/api/competitions"),
    ("GET", "https://api.timerman.org/events"),
    ("GET", "https://timerman.org/_nuxt/data"),
    ("POST", "https://timerman.org/api/events", {}),
    ("POST", "https://timerman.org/api/graphql", {"query": "{events{id name date}}"}),
]

for method, url, *payload in endpoints_to_test:
    try:
        print(f"\n{'='*60}")
        print(f"Тестирую: {method} {url}")

        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        else:
            response = requests.post(url, headers=headers, json=payload[0] if payload else {}, timeout=10)

        print(f"Статус: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")

        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')

            if 'application/json' in content_type:
                try:
                    data = response.json()
                    print(f"\n✅ НАЙДЕН JSON ответ!")
                    print(f"Структура данных:")
                    print(json.dumps(data, ensure_ascii=False, indent=2)[:1000])

                    # Сохраняем в файл для детального анализа
                    with open('timerman_response.json', 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    print(f"\n💾 Полный ответ сохранен в timerman_response.json")

                except Exception as e:
                    print(f"Ошибка парсинга JSON: {e}")
            else:
                print(f"Текст ответа (первые 500 символов):")
                print(response.text[:500])

        elif response.status_code == 404:
            print("❌ 404 Not Found")
        elif response.status_code == 405:
            print("❌ 405 Method Not Allowed")
        else:
            print(f"⚠️ Статус: {response.status_code}")
            print(f"Ответ: {response.text[:200]}")

    except requests.exceptions.Timeout:
        print("⏱️ Timeout")
    except requests.exceptions.ConnectionError as e:
        print(f"🔌 Connection Error: {e}")
    except Exception as e:
        print(f"❌ Ошибка: {type(e).__name__}: {e}")

print(f"\n{'='*60}")
print("\n📝 Рекомендации:")
print("1. Откройте https://timerman.org в браузере")
print("2. Откройте DevTools (F12) → вкладка Network")
print("3. Перейдите на страницу с календарем соревнований")
print("4. Найдите XHR/Fetch запросы, которые загружают данные о соревнованиях")
print("5. Скопируйте URL и структуру запроса")
