"""
Прямой тест timerman.org - проверка разных URL
"""

import requests

print("🔍 Тестирование прямых URL timerman.org\n")

urls_to_test = [
    "https://timerman.org/api/events",
    "https://timerman.org/api/events/list",
    "https://timerman.org/api/calendar",
    "https://timerman.org/events.json",
    "https://timerman.org/_nuxt/state.js",
    "https://timerman.org/api/v1/events",
]

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}

for url in urls_to_test:
    try:
        print(f"\nПроверяю: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        print(f"  Статус: {response.status_code}")

        if response.status_code == 200:
            print(f"  ✅ УСПЕХ!")
            print(f"  Content-Type: {response.headers.get('Content-Type')}")
            print(f"  Первые 500 символов ответа:")
            print(f"  {response.text[:500]}")

            # Сохраняем успешный ответ
            filename = url.split('/')[-1] or 'response'
            with open(f"timerman_{filename}.txt", 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"  💾 Сохранено в timerman_{filename}.txt")
        else:
            print(f"  ❌ Статус {response.status_code}")

    except Exception as e:
        print(f"  ⚠️ Ошибка: {e}")

print("\n" + "="*60)
print("Если ничего не найдено - пожалуйста:")
print("1. Откройте https://timerman.org/events в браузере")
print("2. В DevTools → Network → фильтр 'Fetch/XHR'")
print("3. Найдите запрос который загружает список событий")
print("4. Скопируйте мне URL и пример ответа")
