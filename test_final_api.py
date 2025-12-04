"""
Финальное тестирование с полной правильной структурой
"""

import asyncio
import aiohttp
import json


async def test_final_structure():
    """Тестируем с Page.Take и Filter.EventsLoaderType"""

    base_url = "https://reg.russiarunning.com"
    endpoint = "/api/events/list"

    # Возможные значения EventsLoaderType
    loader_types = [
        "All",
        "Upcoming",
        "Past",
        "Active",
        "Default",
        "Public",
        "0",
        "1",
        "2",
    ]

    test_payloads = []

    # Генерируем тесты с разными EventsLoaderType
    for loader_type in loader_types:
        # Базовый запрос
        test_payloads.append({
            "Page": {
                "Skip": 0,
                "Take": 20
            },
            "Filter": {
                "EventsLoaderType": loader_type
            },
            "Language": "ru"
        })

        # С фильтром по городу
        test_payloads.append({
            "Page": {
                "Skip": 0,
                "Take": 50
            },
            "Filter": {
                "EventsLoaderType": loader_type,
                "City": "Москва"
            },
            "Language": "ru"
        })

    async with aiohttp.ClientSession() as session:
        print("=== ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ ===\n")

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
                            print(f"\n  🎉🎉🎉 УСПЕХ! 🎉🎉🎉")
                            print(f"  Тип данных: {type(data)}")

                            if isinstance(data, dict):
                                print(f"  Ключи: {list(data.keys())}")

                                # Ищем события
                                events = None
                                events_key = None

                                for key in ['events', 'Events', 'items', 'Items', 'data', 'Data', 'results', 'Results', 'list', 'List']:
                                    if key in data:
                                        events = data[key]
                                        events_key = key
                                        break

                                if events and isinstance(events, list):
                                    print(f"\n  📊 Найдено событий: {len(events)}")

                                    if events:
                                        print(f"\n  📋 ПЕРВОЕ СОБЫТИЕ:")
                                        first_event = events[0]
                                        print(json.dumps(first_event, indent=4, ensure_ascii=False))

                                        if isinstance(first_event, dict):
                                            print(f"\n  🔑 Поля события:")
                                            for key in first_event.keys():
                                                value = first_event[key]
                                                value_type = type(value).__name__
                                                value_preview = str(value)[:50] if value else "null"
                                                print(f"      - {key}: ({value_type}) {value_preview}")

                                # Пагинация
                                if 'total' in data or 'Total' in data:
                                    total = data.get('total') or data.get('Total')
                                    print(f"\n  📈 Всего событий: {total}")

                                if 'totalPages' in data or 'TotalPages' in data:
                                    total_pages = data.get('totalPages') or data.get('TotalPages')
                                    print(f"  📄 Всего страниц: {total_pages}")

                                # Полная структура
                                print(f"\n  📦 ПОЛНАЯ СТРУКТУРА ОТВЕТА:")
                                full_response = json.dumps(data, indent=2, ensure_ascii=False)
                                if len(full_response) > 3000:
                                    print(full_response[:3000] + "\n  ... (обрезано)")
                                else:
                                    print(full_response)

                            elif isinstance(data, list):
                                print(f"  📊 Список из {len(data)} событий")
                                if data:
                                    print(f"\n  📋 Первое событие:")
                                    print(json.dumps(data[0], indent=4, ensure_ascii=False))

                            # Сохраняем
                            filename = f"SUCCESS_{i}_loader_{payload['Filter']['EventsLoaderType']}.json"
                            with open(filename, 'w', encoding='utf-8') as f:
                                json.dump({
                                    "request": payload,
                                    "response": data
                                }, f, indent=2, ensure_ascii=False)
                            print(f"\n  💾 Сохранено: {filename}")

                            print(f"\n{'='*70}")
                            print("✨ РАБОЧИЙ API НАЙДЕН! ✨")
                            print(f"{'='*70}")
                            print(f"POST {url}")
                            print("Структура:")
                            print(json.dumps(payload, indent=2, ensure_ascii=False))
                            print(f"{'='*70}\n")

                            # Не прерываем, продолжаем тестировать остальные

                        else:
                            text = await response.text()
                            print(f"  ⚠️  Не JSON: {text[:200]}")

                    elif status == 400:
                        try:
                            error = await response.json()
                            print(f"\n  ❌ Ошибка валидации:")
                            if 'errors' in error:
                                for field, messages in error['errors'].items():
                                    print(f"      {field}: {messages}")
                        except:
                            text = await response.text()
                            print(f"  ❌ {text[:200]}")

                    elif status == 404:
                        print(f"  ❌ 404 - Endpoint не найден")

                    elif status == 401:
                        print(f"  ❌ 401 - Требуется авторизация")

            except asyncio.TimeoutError:
                print(f"  ⏱️  Таймаут")
            except Exception as e:
                print(f"  ❌ {type(e).__name__}: {e}")

        print(f"\n{'='*70}")
        print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
        print(f"{'='*70}\n")


if __name__ == "__main__":
    asyncio.run(test_final_structure())
