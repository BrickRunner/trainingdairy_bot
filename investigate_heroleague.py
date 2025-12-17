"""
Исследование API сайта Лига Героев (heroleague.ru)
"""

import asyncio
import aiohttp
import sys
import io
import json
import re

# Установка правильной кодировки для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

async def investigate_heroleague():
    """Исследуем API Лиги Героев"""

    print("="*60)
    print("🔍 ИССЛЕДОВАНИЕ API ЛИГА ГЕРОЕВ")
    print("="*60)

    base_url = "https://heroleague.ru"
    calendar_url = f"{base_url}/calendar"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        # 1. Проверяем основную страницу календаря
        print(f"\n📄 Шаг 1: Загружаем страницу {calendar_url}")
        try:
            async with session.get(calendar_url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                print(f"   Статус: {response.status}")

                if response.status == 200:
                    html = await response.text()
                    print(f"   Размер HTML: {len(html)} байт")

                    # Сохраняем HTML для анализа
                    with open('heroleague_calendar.html', 'w', encoding='utf-8') as f:
                        f.write(html)
                    print("   💾 Сохранено в heroleague_calendar.html")

                    # Ищем API endpoints в HTML
                    print("\n🔍 Шаг 2: Поиск API endpoints в HTML...")

                    # Паттерны для поиска
                    patterns = {
                        "API URLs": r'(?:https?://)?(?:api\.)?heroleague\.ru/[^\s"\'<>]+',
                        "JSON data": r'<script[^>]*>\s*(?:window\.|const |var |let )?\w+\s*=\s*(\{.+?\})\s*[;<]',
                        "fetch/axios": r'(?:fetch|axios)(?:\.[a-z]+)?\(["\']([^"\']+)["\']',
                    }

                    found_urls = set()

                    for name, pattern in patterns.items():
                        matches = re.findall(pattern, html, re.IGNORECASE)
                        if matches:
                            print(f"\n   ✅ {name}:")
                            unique = list(set([str(m)[:100] for m in matches[:10]]))
                            for match in unique[:5]:
                                print(f"      - {match}")
                                if 'heroleague.ru' in match:
                                    found_urls.add(match)

                    # 3. Пробуем популярные API endpoints
                    print("\n🌐 Шаг 3: Проверка возможных API endpoints...")

                    possible_endpoints = [
                        "/api/events",
                        "/api/calendar",
                        "/api/competitions",
                        "/api/races",
                        "/calendar/data",
                        "/calendar/events",
                        "/_next/data/events.json",
                    ]

                    for endpoint in possible_endpoints:
                        url = base_url + endpoint
                        try:
                            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                                if resp.status == 200:
                                    content_type = resp.headers.get('Content-Type', '')
                                    print(f"\n   ✅ НАЙДЕН: {url}")
                                    print(f"      Content-Type: {content_type}")

                                    if 'json' in content_type:
                                        data = await resp.json()
                                        print(f"      📦 JSON данные:")
                                        print(f"      Тип: {type(data)}")

                                        if isinstance(data, dict):
                                            print(f"      Ключи: {list(data.keys())[:10]}")
                                        elif isinstance(data, list):
                                            print(f"      Элементов: {len(data)}")
                                            if len(data) > 0:
                                                print(f"      Первый элемент: {json.dumps(data[0], ensure_ascii=False)[:200]}")

                                        # Сохраняем
                                        filename = endpoint.replace('/', '_') + '.json'
                                        with open(f'heroleague{filename}', 'w', encoding='utf-8') as f:
                                            json.dump(data, f, ensure_ascii=False, indent=2)
                                        print(f"      💾 Сохранено в heroleague{filename}")

                        except asyncio.TimeoutError:
                            pass
                        except Exception:
                            pass

                    # 4. Проверяем GraphQL
                    print("\n🔍 Шаг 4: Проверка GraphQL...")
                    graphql_url = f"{base_url}/graphql"

                    try:
                        # Простой GraphQL запрос для получения событий
                        graphql_query = {
                            "query": "{ events { id name date } }"
                        }

                        async with session.post(
                            graphql_url,
                            json=graphql_query,
                            timeout=aiohttp.ClientTimeout(total=5)
                        ) as resp:
                            if resp.status == 200:
                                print(f"   ✅ GraphQL endpoint найден!")
                                data = await resp.json()
                                print(f"   Ответ: {json.dumps(data, ensure_ascii=False)[:500]}")
                    except Exception:
                        print("   ❌ GraphQL endpoint не найден")

        except Exception as e:
            print(f"   ❌ Ошибка: {e}")

    print("\n" + "="*60)
    print("📝 ИНСТРУКЦИЯ:")
    print("1. Откройте https://heroleague.ru/calendar в браузере")
    print("2. Нажмите F12 → вкладка Network → фильтр XHR/Fetch")
    print("3. Обновите страницу или прокрутите список событий")
    print("4. Найдите запрос который загружает события")
    print("5. Скопируйте:")
    print("   - URL запроса")
    print("   - Метод (GET/POST)")
    print("   - Request Payload (если POST)")
    print("   - Пример Response")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(investigate_heroleague())
