"""
Тестовый скрипт для поиска API endpoints на reg.russiarunning.com
"""

import asyncio
import aiohttp
import json


async def test_api_endpoints():
    """Тестирование возможных API endpoints"""

    # Возможные API endpoints
    api_endpoints = [
        "https://reg.russiarunning.com/api/events",
        "https://reg.russiarunning.com/api/competitions",
        "https://reg.russiarunning.com/api/races",
        "https://reg.russiarunning.com/api/cities",
        "https://reg.russiarunning.com/api/sports",
        "https://reg.russiarunning.com/api/v1/events",
        "https://reg.russiarunning.com/api/v1/competitions",
        "https://api.russiarunning.com/events",
        "https://api.russiarunning.com/competitions",
    ]

    async with aiohttp.ClientSession() as session:
        print("=== ТЕСТИРОВАНИЕ API ENDPOINTS ===\n")

        for endpoint in api_endpoints:
            try:
                print(f"Проверяю: {endpoint}")
                async with session.get(endpoint, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    print(f"  Статус: {response.status}")

                    if response.status == 200:
                        content_type = response.headers.get('Content-Type', '')
                        print(f"  Content-Type: {content_type}")

                        if 'json' in content_type:
                            try:
                                data = await response.json()
                                print(f"  ✓ JSON получен!")
                                print(f"  Тип данных: {type(data)}")

                                if isinstance(data, list):
                                    print(f"  Количество элементов: {len(data)}")
                                    if data:
                                        print(f"  Пример первого элемента:")
                                        print(f"  {json.dumps(data[0], indent=2, ensure_ascii=False)[:500]}")
                                elif isinstance(data, dict):
                                    print(f"  Ключи: {list(data.keys())}")
                                    print(f"  Пример данных:")
                                    print(f"  {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")

                                # Сохраняем успешный результат
                                filename = endpoint.split('/')[-1] + '.json'
                                with open(filename, 'w', encoding='utf-8') as f:
                                    json.dump(data, f, indent=2, ensure_ascii=False)
                                print(f"  Сохранено в {filename}")

                            except Exception as e:
                                print(f"  Ошибка парсинга JSON: {e}")
                        else:
                            text = await response.text()
                            print(f"  Получен текст ({len(text)} символов)")
                            print(f"  Первые 200 символов: {text[:200]}")

                    elif response.status == 404:
                        print(f"  ✗ Не найден")
                    elif response.status == 403:
                        print(f"  ✗ Доступ запрещен")
                    else:
                        print(f"  ? Неожиданный статус")

            except asyncio.TimeoutError:
                print(f"  ✗ Таймаут")
            except Exception as e:
                print(f"  ✗ Ошибка: {e}")

            print()

        # Попробуем загрузить главный JavaScript файл и найти в нем API endpoints
        print("\n=== АНАЛИЗ JAVASCRIPT ФАЙЛА ===\n")
        js_url = "https://reg.russiarunning.com/assets/index-BXeUS8oC.js"

        try:
            print(f"Загружаю: {js_url}")
            async with session.get(js_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    js_content = await response.text()
                    print(f"Размер файла: {len(js_content)} символов")

                    # Ищем возможные API endpoints в JS коде
                    print("\nПоиск API endpoints в коде:")

                    keywords = ['/api/', 'api/', 'endpoint', 'baseURL', 'apiUrl', 'API_URL']
                    for keyword in keywords:
                        if keyword in js_content:
                            # Находим контекст вокруг keyword
                            idx = js_content.find(keyword)
                            context = js_content[max(0, idx-50):min(len(js_content), idx+200)]
                            print(f"\nНайдено '{keyword}':")
                            print(f"  ...{context}...")

                    # Сохраняем JS для дальнейшего анализа
                    with open('main_app.js', 'w', encoding='utf-8') as f:
                        f.write(js_content)
                    print("\nJavaScript сохранен в main_app.js")

        except Exception as e:
            print(f"Ошибка при загрузке JS: {e}")

        print("\n=== АНАЛИЗ ЗАВЕРШЕН ===")


if __name__ == "__main__":
    asyncio.run(test_api_endpoints())
