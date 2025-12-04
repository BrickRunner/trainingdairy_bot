"""
Тестирование /api/events/list с различными параметрами
"""

import asyncio
import aiohttp
import json
from datetime import datetime


async def test_events_list():
    """Пробуем различные варианты параметров для /api/events/list"""

    base_url = "https://reg.russiarunning.com"
    endpoint = "/api/events/list"

    # Различные варианты payload
    test_payloads = [
        # Пустой объект
        {},

        # Простые фильтры
        {"limit": 10},
        {"limit": 100},
        {"page": 1, "limit": 20},

        # Фильтры по статусу
        {"status": "upcoming"},
        {"status": "active"},
        {"status": "open"},

        # Фильтры по городу
        {"city": "Москва"},
        {"city": "Санкт-Петербург"},
        {"cityId": 1},

        # Фильтры по спорту
        {"sport": "Бег"},
        {"sport": "run"},
        {"sportId": 1},

        # Комбинированные
        {"city": "Москва", "sport": "Бег"},
        {"page": 1, "limit": 10, "status": "upcoming"},

        # С датами
        {"dateFrom": "2024-01-01"},
        {"dateTo": "2025-12-31"},
        {"dateFrom": "2024-01-01", "dateTo": "2025-12-31"},

        # Возможные поля из типичных API
        {
            "page": 1,
            "pageSize": 20,
            "filters": {},
            "sorting": []
        },
        {
            "pagination": {
                "page": 1,
                "size": 20
            },
            "filters": {}
        },

        # Поиск
        {"search": ""},
        {"query": ""},

        # Tenant
        {"tenant": "default"},
        {"organizedId": "default"},
    ]

    async with aiohttp.ClientSession() as session:
        print("=== ТЕСТИРОВАНИЕ /api/events/list ===\n")

        for i, payload in enumerate(test_payloads, 1):
            url = base_url + endpoint
            print(f"\n{i}. Тест с payload:")
            print(f"   {json.dumps(payload, ensure_ascii=False)}")

            try:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    status = response.status
                    content_type = response.headers.get('Content-Type', '')

                    print(f"   Статус: {status}")
                    print(f"   Content-Type: {content_type}")

                    if status == 200:
                        if 'json' in content_type:
                            data = await response.json()
                            print(f"   ✓✓✓ УСПЕХ! ✓✓✓")
                            print(f"   Тип: {type(data)}")

                            if isinstance(data, dict):
                                print(f"   Ключи: {list(data.keys())}")

                                # Если есть список событий
                                if 'events' in data or 'items' in data or 'data' in data:
                                    events_key = 'events' if 'events' in data else ('items' if 'items' in data else 'data')
                                    events = data[events_key]
                                    print(f"   Найдено событий: {len(events) if isinstance(events, list) else 'N/A'}")

                                    if isinstance(events, list) and events:
                                        print(f"\n   Первое событие:")
                                        print(f"   {json.dumps(events[0], indent=6, ensure_ascii=False)}")

                                print(f"\n   Полный ответ:")
                                print(f"   {json.dumps(data, indent=6, ensure_ascii=False)[:1000]}")

                            elif isinstance(data, list):
                                print(f"   Количество событий: {len(data)}")
                                if data:
                                    print(f"\n   Первое событие:")
                                    print(f"   {json.dumps(data[0], indent=6, ensure_ascii=False)}")

                            # Сохраняем успешный результат
                            filename = f"success_payload_{i}.json"
                            with open(filename, 'w', encoding='utf-8') as f:
                                json.dump({
                                    "payload": payload,
                                    "response": data
                                }, f, indent=2, ensure_ascii=False)
                            print(f"\n   Сохранено в {filename}")

                            # Если нашли успешный запрос, показываем его крупно
                            print("\n" + "="*60)
                            print("НАЙДЕН РАБОЧИЙ ENDPOINT!")
                            print("="*60)
                            print(f"URL: {url}")
                            print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
                            print("="*60 + "\n")

                        else:
                            text = await response.text()
                            print(f"   Не JSON: {text[:200]}")

                    elif status == 400:
                        try:
                            error = await response.json()
                            print(f"   ✗ Ошибка 400: {error}")
                        except:
                            text = await response.text()
                            print(f"   ✗ Ошибка 400: {text[:200]}")

                    elif status == 404:
                        print(f"   ✗ 404 Not Found")

                    elif status == 401:
                        print(f"   ✗ 401 Unauthorized")

            except asyncio.TimeoutError:
                print(f"   ✗ Таймаут")
            except Exception as e:
                print(f"   ✗ Ошибка: {e}")

        print("\n" + "="*60)
        print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
        print("="*60)


if __name__ == "__main__":
    asyncio.run(test_events_list())
