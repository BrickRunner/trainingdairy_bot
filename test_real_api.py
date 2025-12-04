"""
Тестирование реальных API endpoints
"""

import asyncio
import aiohttp
import json


async def test_endpoints():
    """Тестируем найденные endpoints и ищем endpoint для событий"""

    base_url = "https://reg.russiarunning.com"

    # Найденные endpoints
    known_endpoints = [
        "/api/events/live-count",
        "/api/events/tenants/getCurrent",
        "/api/users/getCurrent",
    ]

    # Пробуем различные варианты для получения событий
    test_endpoints = [
        "/api/events",
        "/api/events/list",
        "/api/events/upcoming",
        "/api/events/search",
        "/api/events/filter",
        "/api/events/all",
        "/api/event",
        "/api/event/list",
        *known_endpoints
    ]

    async with aiohttp.ClientSession() as session:
        print("=== ТЕСТИРОВАНИЕ ENDPOINTS ===\n")

        for endpoint in test_endpoints:
            url = base_url + endpoint
            print(f"Тестирую: {endpoint}")

            try:
                # GET запрос
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    status = response.status
                    content_type = response.headers.get('Content-Type', '')

                    print(f"  GET {status} - {content_type}")

                    if status == 200 and 'json' in content_type:
                        try:
                            data = await response.json()
                            print(f"  ✓ Успех! Тип: {type(data)}")

                            if isinstance(data, list):
                                print(f"  Список из {len(data)} элементов")
                                if data and len(data) > 0:
                                    print(f"  Первый элемент:")
                                    print(f"  {json.dumps(data[0], indent=4, ensure_ascii=False)[:300]}")
                            elif isinstance(data, dict):
                                print(f"  Объект с ключами: {list(data.keys())[:10]}")
                                print(f"  Данные:")
                                print(f"  {json.dumps(data, indent=4, ensure_ascii=False)[:300]}")

                            # Сохраняем успешный результат
                            filename = f"api_{endpoint.replace('/', '_')}.json"
                            with open(filename, 'w', encoding='utf-8') as f:
                                json.dump(data, f, indent=2, ensure_ascii=False)
                            print(f"  Сохранено: {filename}")

                        except Exception as e:
                            print(f"  Ошибка парсинга: {e}")

                    elif status == 404:
                        print(f"  ✗ Не найден")
                    elif status == 401:
                        print(f"  ✗ Требуется авторизация")
                    elif status == 403:
                        print(f"  ✗ Доступ запрещен")

            except asyncio.TimeoutError:
                print(f"  ✗ Таймаут")
            except Exception as e:
                print(f"  ✗ Ошибка: {e}")

            print()

        # Попробуем POST запросы с параметрами
        print("\n=== ТЕСТИРОВАНИЕ POST ЗАПРОСОВ ===\n")

        post_tests = [
            ("/api/events/search", {"city": "Москва"}),
            ("/api/events/filter", {"city": "Москва", "sport": "Бег"}),
            ("/api/events/list", {}),
        ]

        for endpoint, payload in post_tests:
            url = base_url + endpoint
            print(f"POST: {endpoint}")
            print(f"  Payload: {payload}")

            try:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    status = response.status
                    content_type = response.headers.get('Content-Type', '')

                    print(f"  {status} - {content_type}")

                    if status == 200 and 'json' in content_type:
                        data = await response.json()
                        print(f"  ✓ Успех!")
                        print(f"  {json.dumps(data, indent=4, ensure_ascii=False)[:300]}")

                        filename = f"api_post_{endpoint.replace('/', '_')}.json"
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        print(f"  Сохранено: {filename}")

            except Exception as e:
                print(f"  ✗ Ошибка: {e}")

            print()

        print("=== ТЕСТИРОВАНИЕ ЗАВЕРШЕНО ===")


if __name__ == "__main__":
    asyncio.run(test_endpoints())
