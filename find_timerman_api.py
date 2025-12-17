"""
Поиск API timerman.org через анализ загрузки страницы
"""

import asyncio
import aiohttp
import re
import json

async def check_possible_api_urls():
    """Проверяем возможные API URL на основе паттернов Nuxt.js"""

    # Базовые URL которые использует Nuxt.js
    possible_urls = [
        # Nuxt.js обычно использует эти паттерны
        "https://timerman.org/_nuxt/data/events.json",
        "https://timerman.org/_nuxt/payload.js",
        "https://timerman.org/api/events",
        "https://timerman.org/api/events/list",
        "https://timerman.org/api/v1/events",
        "https://timerman.org/api/competitions",

        # С параметрами как на странице
        "https://timerman.org/api/events?sportType=all&season=all",
        "https://timerman.org/api/events?sportType=all",

        # GraphQL возможно
        "https://timerman.org/graphql",
        "https://timerman.org/api/graphql",
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "ru-RU,ru;q=0.9",
        "Referer": "https://timerman.org/events",
    }

    print("🔍 Проверка возможных API endpoints...\n")

    async with aiohttp.ClientSession(headers=headers) as session:
        for url in possible_urls:
            try:
                print(f"Проверяю: {url}")
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    print(f"  Статус: {response.status}")

                    if response.status == 200:
                        content_type = response.headers.get('Content-Type', '')
                        print(f"  ✅ Content-Type: {content_type}")

                        if 'application/json' in content_type:
                            data = await response.json()
                            print(f"  🎯 НАЙДЕН JSON!")
                            print(f"  Ключи: {list(data.keys())[:10]}")

                            # Сохраняем
                            filename = url.split('/')[-1].split('?')[0] or 'response'
                            with open(f"timerman_api_{filename}.json", 'w', encoding='utf-8') as f:
                                json.dump(data, f, ensure_ascii=False, indent=2)
                            print(f"  💾 Сохранено в timerman_api_{filename}.json")

                            # Показываем превью
                            print(f"  Превью (500 символов):")
                            print(f"  {json.dumps(data, ensure_ascii=False)[:500]}")
                            return url, data
                        else:
                            text = await response.text()
                            print(f"  Текст (200 символов): {text[:200]}")

                    elif response.status == 404:
                        print(f"  ❌ 404 Not Found")
                    else:
                        print(f"  ⚠️ Статус {response.status}")

            except asyncio.TimeoutError:
                print(f"  ⏱️ Timeout")
            except Exception as e:
                print(f"  ❌ {type(e).__name__}")

            print()

    return None, None


async def analyze_page_source():
    """Анализируем исходный код страницы на предмет данных"""

    print("\n" + "="*60)
    print("📄 Анализ исходного кода страницы...\n")

    url = "https://timerman.org/events?sportType=all&season=all"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html",
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
            html = await response.text()

            print(f"Размер страницы: {len(html)} байт")

            # Ищем возможные паттерны
            patterns = {
                "API endpoints": r'["\']((?:https?://)?(?:api\.)?timerman\.org/[^"\']+)["\']',
                "JSON data": r'<script[^>]*>\s*(?:window\.|const |var |let )?(\w+)\s*=\s*({.+?})\s*[;<]',
                "__NUXT__": r'window\.__NUXT__\s*=\s*(.+?);',
                "fetch/axios calls": r'(?:fetch|axios)(?:\.[a-z]+)?\(["\']([^"\']+)["\']',
            }

            for name, pattern in patterns.items():
                matches = re.findall(pattern, html, re.DOTALL)
                if matches:
                    print(f"\n✅ Найдено: {name}")
                    unique_matches = list(set([str(m)[:100] for m in matches[:10]]))
                    for match in unique_matches[:5]:
                        print(f"  - {match}")

            # Сохраняем HTML для ручного анализа
            with open("timerman_events_page.html", 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"\n💾 HTML сохранен в timerman_events_page.html")


async def main():
    print("="*60)
    print("🔍 ПОИСК API TIMERMAN.ORG")
    print("="*60 + "\n")

    # Сначала проверяем возможные API URLs
    api_url, api_data = await check_possible_api_urls()

    if api_url:
        print("\n" + "="*60)
        print(f"✅ УСПЕХ! Найден API endpoint:")
        print(f"   {api_url}")
        print("="*60)
        return api_url, api_data

    # Если не нашли - анализируем исходный код
    await analyze_page_source()

    print("\n" + "="*60)
    print("❌ Автоматически найти API не удалось")
    print("="*60)
    print("\n📝 Следующие шаги:")
    print("1. Откройте timerman_events_page.html и поищите упоминания 'api'")
    print("2. В браузере: DevTools → Network → фильтр XHR/Fetch")
    print("3. Обновите страницу timerman.org/events")
    print("4. Найдите запрос который загружает список событий")
    print("5. Сообщите мне URL этого запроса")


if __name__ == "__main__":
    result = asyncio.run(main())
