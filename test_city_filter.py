"""
Тестирование фильтра по городу
"""

import asyncio
import aiohttp
import json


async def test_city_filter():
    """Тестируем различные варианты фильтра по городу"""

    base_url = "https://reg.russiarunning.com"
    endpoint = "/api/events/list"

    # Различные варианты параметра города
    city_params = [
        ("CityName", "Москва"),
        ("CityName", "Moscow"),
        ("cityName", "Москва"),
        ("City", "Москва"),
        ("city", "Москва"),
        ("CityId", "1"),
        ("cityId", "1"),
    ]

    async with aiohttp.ClientSession() as session:
        print("=== ТЕСТИРОВАНИЕ ФИЛЬТРА ПО ГОРОДУ ===\n")

        for param_name, param_value in city_params:
            print(f"\nТест: {param_name} = {param_value}")

            payload = {
                "Page": {
                    "Skip": 0,
                    "Take": 10
                },
                "Filter": {
                    "EventsLoaderType": 0,
                    param_name: param_value
                },
                "Language": "ru"
            }

            try:
                async with session.post(
                    base_url + endpoint,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=20)
                ) as response:
                    status = response.status
                    print(f"  Статус: {status}")

                    if status == 200:
                        data = await response.json()
                        events = data.get("list", [])
                        print(f"  ✓ Получено событий: {len(events)}")

                        if events:
                            # Показываем города первых 5 событий
                            print(f"  Города событий:")
                            for i, event in enumerate(events[:5], 1):
                                city = event.get('cityName') or event.get('place', 'N/A')
                                title = event['title'][:40]
                                print(f"    {i}. {city} - {title}")

                    elif status == 400:
                        error = await response.json()
                        if 'errors' in error:
                            print(f"  ✗ Ошибка: {error['errors']}")

            except Exception as e:
                print(f"  ✗ Ошибка: {e}")

        # Тест без фильтра
        print(f"\n\nТест БЕЗ фильтра по городу:")
        payload = {
            "Page": {
                "Skip": 0,
                "Take": 10
            },
            "Filter": {
                "EventsLoaderType": 0
            },
            "Language": "ru"
        }

        try:
            async with session.post(
                base_url + endpoint,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=20)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    events = data.get("list", [])
                    print(f"  Всего событий: {len(events)}")
                    print(f"  Города:")
                    for event in events[:10]:
                        city = event.get('cityName') or event.get('place', 'N/A')
                        print(f"    - {city}")

        except Exception as e:
            print(f"  Ошибка: {e}")

        print("\n=== ТЕСТИРОВАНИЕ ЗАВЕРШЕНО ===")


if __name__ == "__main__":
    asyncio.run(test_city_filter())
