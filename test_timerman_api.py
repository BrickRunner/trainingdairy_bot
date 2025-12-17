"""
Тестовый скрипт для исследования API timerman.org
"""

import asyncio
import aiohttp
import json


async def test_api_endpoints():
    """Тестируем различные возможные API endpoints"""

    base_urls = [
        "https://timerman.org",
        "https://api.timerman.org",
    ]

    possible_endpoints = [
        "/api/events",
        "/api/events/list",
        "/api/v1/events",
        "/api/calendar",
        "/api/competitions",
        "/events",
        "/events/list",
        "/graphql",
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        print("=== Тестирование GET запросов ===\n")

        for base_url in base_urls:
            for endpoint in possible_endpoints:
                url = base_url + endpoint
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        print(f"✓ {url}")
                        print(f"  Status: {response.status}")
                        print(f"  Content-Type: {response.headers.get('Content-Type', 'N/A')}")

                        if response.status == 200:
                            content_type = response.headers.get('Content-Type', '')
                            if 'application/json' in content_type:
                                data = await response.json()
                                print(f"  JSON Response (first 500 chars):")
                                print(f"  {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
                            else:
                                text = await response.text()
                                print(f"  Response (first 200 chars): {text[:200]}")
                        print()

                except asyncio.TimeoutError:
                    print(f"✗ {url} - TIMEOUT")
                    print()
                except Exception as e:
                    print(f"✗ {url} - ERROR: {type(e).__name__}: {str(e)[:100]}")
                    print()

        print("\n=== Тестирование POST запросов ===\n")

        # Пробуем POST запросы с разными payload
        test_payloads = [
            {},
            {"limit": 10},
            {"take": 10, "skip": 0},
            {"page": {"skip": 0, "take": 10}},
        ]

        for base_url in base_urls:
            for endpoint in ["/api/events", "/api/events/list"]:
                url = base_url + endpoint
                for payload in test_payloads:
                    try:
                        async with session.post(
                            url,
                            json=payload,
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as response:
                            print(f"✓ POST {url}")
                            print(f"  Payload: {payload}")
                            print(f"  Status: {response.status}")
                            print(f"  Content-Type: {response.headers.get('Content-Type', 'N/A')}")

                            if response.status == 200:
                                content_type = response.headers.get('Content-Type', '')
                                if 'application/json' in content_type:
                                    data = await response.json()
                                    print(f"  JSON Response (first 500 chars):")
                                    print(f"  {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
                            print()

                    except Exception as e:
                        print(f"✗ POST {url} - ERROR: {type(e).__name__}")
                        print()


async def test_main_page():
    """Проверяем главную страницу на наличие данных о событиях"""
    print("\n=== Анализ главной страницы ===\n")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get("https://timerman.org/", timeout=aiohttp.ClientTimeout(total=15)) as response:
                print(f"Status: {response.status}")
                html = await response.text()

                # Ищем упоминания о API
                if "__NUXT__" in html or "__NEXT_DATA__" in html:
                    print("✓ Обнаружен SSR фреймворк (Nuxt/Next)")

                    # Ищем встроенные данные
                    if "__NUXT__" in html:
                        start = html.find("__NUXT__")
                        end = html.find("</script>", start)
                        if start != -1 and end != -1:
                            nuxt_data = html[start:end]
                            print(f"\nНайдены данные __NUXT__ (первые 1000 символов):")
                            print(nuxt_data[:1000])

                    if "__NEXT_DATA__" in html:
                        start = html.find("__NEXT_DATA__")
                        end = html.find("</script>", start)
                        if start != -1 and end != -1:
                            next_data = html[start:end]
                            print(f"\nНайдены данные __NEXT_DATA__ (первые 1000 символов):")
                            print(next_data[:1000])

                # Ищем упоминания API endpoints в скриптах
                if "api/" in html or "/api/" in html:
                    print("\n✓ Найдены упоминания '/api/' в HTML")

                    import re
                    api_urls = re.findall(r'["\'](/api/[^"\']+)["\']', html)
                    if api_urls:
                        print("  Найденные API URLs:")
                        for url in set(api_urls[:10]):  # Показываем первые 10 уникальных
                            print(f"    - {url}")

        except Exception as e:
            print(f"Ошибка при загрузке главной страницы: {e}")


if __name__ == "__main__":
    print("🔍 Исследование API timerman.org\n")
    print("=" * 60)

    asyncio.run(test_main_page())
    asyncio.run(test_api_endpoints())

    print("\n" + "=" * 60)
    print("Исследование завершено!")
