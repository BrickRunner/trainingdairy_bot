"""
Поиск API endpoint для reg.place
Сохраняет результаты в файл
"""

import asyncio
import aiohttp
import json

BASE_URL = "https://api.reg.place/v1"

async def test_endpoints():
    """Тестируем различные endpoint'ы"""

    results = []
    results.append("="*60)
    results.append("ИССЛЕДОВАНИЕ API REG.PLACE")
    results.append("="*60)

    # Возможные endpoint'ы
    endpoints = [
        "/events",
        "/competitions",
        "/races",
        "/calendar",
        "/event/list",
        "/event/search",
        "/search",
        "/public/events",
        "/api/events",
    ]

    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints:
            url = BASE_URL + endpoint
            results.append(f"\n\nПроверяем: {url}")
            results.append("-" * 60)

            try:
                async with session.get(url, timeout=10) as response:
                    results.append(f"Статус: {response.status}")

                    if response.status == 200:
                        try:
                            data = await response.json()
                            results.append(f"✅ УСПЕХ! Получен JSON")
                            results.append(f"Тип данных: {type(data).__name__}")

                            if isinstance(data, list):
                                results.append(f"Список из {len(data)} элементов")
                                if data:
                                    results.append(f"\nПример первого элемента:")
                                    results.append(json.dumps(data[0], indent=2, ensure_ascii=False)[:500])
                            elif isinstance(data, dict):
                                results.append(f"Объект с ключами: {list(data.keys())}")
                                results.append(f"\nСодержимое:")
                                results.append(json.dumps(data, indent=2, ensure_ascii=False)[:500])
                        except Exception as e:
                            text = await response.text()
                            results.append(f"Ответ (не JSON): {text[:200]}")
                    else:
                        text = await response.text()
                        results.append(f"Ошибка {response.status}: {text[:200]}")

            except asyncio.TimeoutError:
                results.append("⏱ Timeout")
            except Exception as e:
                results.append(f"❌ Ошибка: {str(e)}")

    # Сохраняем результаты
    with open('regplace_api_results.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(results))

    print("Результаты сохранены в regplace_api_results.txt")
    print('\n'.join(results))

if __name__ == "__main__":
    asyncio.run(test_endpoints())
