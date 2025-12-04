"""
Тестирование с правильной структурой запроса
"""

import asyncio
import aiohttp
import json


async def test_correct_structure():
    """Тестируем с правильной структурой Page, Filter, Language"""

    base_url = "https://reg.russiarunning.com"
    endpoint = "/api/events/list"

    # Правильная структура согласно ошибкам валидации
    test_payloads = [
        # Минимальный запрос
        {
            "Page": {
                "Number": 1,
                "Size": 20
            },
            "Filter": {},
            "Language": "ru"
        },

        # С фильтром по городу
        {
            "Page": {
                "Number": 1,
                "Size": 50
            },
            "Filter": {
                "City": "Москва"
            },
            "Language": "ru"
        },

        # С фильтром по виду спорта
        {
            "Page": {
                "Number": 1,
                "Size": 50
            },
            "Filter": {
                "Sport": "Бег"
            },
            "Language": "ru"
        },

        # С обоими фильтрами
        {
            "Page": {
                "Number": 1,
                "Size": 50
            },
            "Filter": {
                "City": "Москва",
                "Sport": "Бег"
            },
            "Language": "ru"
        },

        # Другие возможные поля фильтра
        {
            "Page": {
                "Number": 1,
                "Size": 50
            },
            "Filter": {
                "Status": "upcoming",
                "DateFrom": "2024-01-01",
                "DateTo": "2025-12-31"
            },
            "Language": "ru"
        },

        # С cityId
        {
            "Page": {
                "Number": 1,
                "Size": 50
            },
            "Filter": {
                "CityId": 1
            },
            "Language": "ru"
        },

        # С sportId
        {
            "Page": {
                "Number": 1,
                "Size": 50
            },
            "Filter": {
                "SportId": 1
            },
            "Language": "ru"
        },

        # English language
        {
            "Page": {
                "Number": 1,
                "Size": 20
            },
            "Filter": {},
            "Language": "en"
        },

        # Больше событий
        {
            "Page": {
                "Number": 1,
                "Size": 100
            },
            "Filter": {},
            "Language": "ru"
        },
    ]

    async with aiohttp.ClientSession() as session:
        print("=== ТЕСТИРОВАНИЕ С ПРАВИЛЬНОЙ СТРУКТУРОЙ ===\n")

        for i, payload in enumerate(test_payloads, 1):
            url = base_url + endpoint
            print(f"\n{'='*70}")
            print(f"ТЕСТ #{i}")
            print(f"{'='*70}")
            print(f"Payload:")
            print(json.dumps(payload, indent=2, ensure_ascii=False))

            try:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=20)
                ) as response:
                    status = response.status
                    content_type = response.headers.get('Content-Type', '')

                    print(f"\nОтвет:")
                    print(f"  Статус: {status}")
                    print(f"  Content-Type: {content_type}")

                    if status == 200:
                        if 'json' in content_type:
                            data = await response.json()
                            print(f"\n  ✓✓✓ УСПЕХ! ✓✓✓")
                            print(f"  Тип данных: {type(data)}")

                            if isinstance(data, dict):
                                print(f"  Ключи верхнего уровня: {list(data.keys())}")

                                # Ищем события в разных возможных ключах
                                events = None
                                events_key = None

                                for key in ['events', 'Events', 'items', 'Items', 'data', 'Data', 'results', 'Results']:
                                    if key in data:
                                        events = data[key]
                                        events_key = key
                                        break

                                if events and isinstance(events, list):
                                    print(f"\n  Найдено событий в '{events_key}': {len(events)}")

                                    if events:
                                        print(f"\n  Пример первого события:")
                                        first_event = events[0]
                                        print(json.dumps(first_event, indent=4, ensure_ascii=False))

                                        print(f"\n  Поля события: {list(first_event.keys()) if isinstance(first_event, dict) else 'N/A'}")

                                # Показываем полный ответ (обрезанный)
                                print(f"\n  Полная структура ответа:")
                                full_response = json.dumps(data, indent=4, ensure_ascii=False)
                                if len(full_response) > 2000:
                                    print(full_response[:2000] + "\n  ... (обрезано)")
                                else:
                                    print(full_response)

                            elif isinstance(data, list):
                                print(f"  Ответ - список из {len(data)} элементов")
                                if data:
                                    print(f"\n  Первый элемент:")
                                    print(json.dumps(data[0], indent=4, ensure_ascii=False))

                            # Сохраняем успешный результат
                            filename = f"working_api_{i}.json"
                            with open(filename, 'w', encoding='utf-8') as f:
                                json.dump({
                                    "request": payload,
                                    "response": data
                                }, f, indent=2, ensure_ascii=False)
                            print(f"\n  💾 Сохранено в {filename}")

                            print(f"\n{'='*70}")
                            print("🎉 РАБОЧИЙ API ENDPOINT НАЙДЕН! 🎉")
                            print(f"{'='*70}")
                            print(f"URL: POST {url}")
                            print(f"Структура запроса:")
                            print(json.dumps(payload, indent=2, ensure_ascii=False))
                            print(f"{'='*70}\n")

                        else:
                            text = await response.text()
                            print(f"  Не JSON: {text[:300]}")

                    elif status == 400:
                        try:
                            error = await response.json()
                            print(f"\n  ✗ Ошибка валидации:")
                            print(json.dumps(error, indent=4, ensure_ascii=False))
                        except:
                            text = await response.text()
                            print(f"  ✗ Ошибка 400: {text[:300]}")

                    elif status == 404:
                        print(f"  ✗ 404 - Endpoint не найден")

                    elif status == 401:
                        print(f"  ✗ 401 - Требуется авторизация")

                    elif status == 403:
                        print(f"  ✗ 403 - Доступ запрещен")

            except asyncio.TimeoutError:
                print(f"  ✗ Таймаут запроса")
            except Exception as e:
                print(f"  ✗ Ошибка: {type(e).__name__}: {e}")

        print(f"\n{'='*70}")
        print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
        print(f"{'='*70}\n")


if __name__ == "__main__":
    asyncio.run(test_correct_structure())
