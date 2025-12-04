"""
Тестирование с EventsLoaderType как число (enum)
"""

import asyncio
import aiohttp
import json


async def test_with_enum():
    """EventsLoaderType как число"""

    base_url = "https://reg.russiarunning.com"
    endpoint = "/api/events/list"

    # Пробуем числа от 0 до 10
    test_payloads = []

    for enum_value in range(0, 11):
        test_payloads.append({
            "Page": {
                "Skip": 0,
                "Take": 50
            },
            "Filter": {
                "EventsLoaderType": enum_value
            },
            "Language": "ru"
        })

    # Также пробуем null
    test_payloads.append({
        "Page": {
            "Skip": 0,
            "Take": 50
        },
        "Filter": {
            "EventsLoaderType": None
        },
        "Language": "ru"
    })

    # Без EventsLoaderType вообще
    test_payloads.append({
        "Page": {
            "Skip": 0,
            "Take": 50
        },
        "Filter": {},
        "Language": "ru"
    })

    async with aiohttp.ClientSession() as session:
        print("=== ТЕСТИРОВАНИЕ С ENUM (ЧИСЛА) ===\n")

        for i, payload in enumerate(test_payloads, 1):
            url = base_url + endpoint
            loader_type = payload['Filter'].get('EventsLoaderType', 'не указан')

            print(f"\n{'='*70}")
            print(f"ТЕСТ #{i} - EventsLoaderType: {loader_type}")
            print(f"{'='*70}")

            try:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=20)
                ) as response:
                    status = response.status
                    content_type = response.headers.get('Content-Type', '')

                    print(f"Статус: {status}")

                    if status == 200:
                        if 'json' in content_type:
                            data = await response.json()
                            print(f"\n🎉🎉🎉 УСПЕХ! EventsLoaderType = {loader_type} 🎉🎉🎉\n")

                            # Анализируем ответ
                            if isinstance(data, dict):
                                print(f"Ключи ответа: {list(data.keys())}")

                                # Ищем события
                                for key in ['events', 'Events', 'items', 'Items', 'data', 'Data']:
                                    if key in data:
                                        events = data[key]
                                        if isinstance(events, list):
                                            print(f"\n📊 Найдено событий в '{key}': {len(events)}")

                                            if events:
                                                print(f"\n📋 ПЕРВОЕ СОБЫТИЕ:")
                                                print(json.dumps(events[0], indent=2, ensure_ascii=False)[:1500])
                                            break

                                # Полный ответ
                                print(f"\n📦 ПОЛНЫЙ ОТВЕТ:")
                                response_str = json.dumps(data, indent=2, ensure_ascii=False)
                                print(response_str[:2000])
                                if len(response_str) > 2000:
                                    print("... (обрезано)")

                            # Сохраняем
                            filename = f"SUCCESS_enum_{loader_type}.json"
                            with open(filename, 'w', encoding='utf-8') as f:
                                json.dump({
                                    "request": payload,
                                    "response": data
                                }, f, indent=2, ensure_ascii=False)
                            print(f"\n💾 Сохранено: {filename}")

                            print(f"\n{'='*70}")
                            print(f"✨ РАБОЧИЙ ВАРИАНТ: EventsLoaderType = {loader_type}")
                            print(f"{'='*70}\n")

                    elif status == 400:
                        try:
                            error = await response.json()
                            if 'errors' in error:
                                error_msg = list(error['errors'].values())[0][0] if error['errors'] else "Unknown"
                                print(f"❌ {error_msg[:100]}")
                        except:
                            print(f"❌ 400 Bad Request")

                    elif status == 404:
                        print(f"❌ 404")

            except Exception as e:
                print(f"❌ {type(e).__name__}: {str(e)[:100]}")

        print(f"\n{'='*70}")
        print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
        print(f"{'='*70}\n")


if __name__ == "__main__":
    asyncio.run(test_with_enum())
