"""
Отладка API Timerman - проверка что именно возвращает API
"""

import asyncio
import aiohttp
import json
import sys
import io

# Установка правильной кодировки для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

async def test_api():
    print("="*60)
    print("🔍 ОТЛАДКА TIMERMAN API")
    print("="*60)

    url = "https://timerman.org/api/events/list/ru"

    payload = {
        "EventsLoaderType": 0,
        "UseTenantBeneficiaryCode": True,
        "Skip": 0,
        "Take": 10,
        "DisciplinesCodes": None,
        "DateFrom": None,
        "DateTo": None,
        "FromAge": 11,
        "HidePastEvents": False,
        "InSportmasterChampionship": False,
        "IntoRayRussiaRunnung": False,
        "NationalMovementOnly": False,
        "OnlyWithAdmissions": False,
        "OnlyWithOpenRegistration": False,
        "ResultsCalculated": False,
        "RrRecomended": False,
        "SortRule": {"Type": 0, "Direction": 1},
        "SportSeriesCode": None,
        "StarRaitings": [],
        "ToAge": None,
        "ApprovedStarRaitingOnly": False,
    }

    print(f"\n📡 URL: {url}")
    print(f"\n📦 Payload:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    async with aiohttp.ClientSession() as session:
        try:
            print("\n⏳ Отправка POST запроса...")
            async with session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                print(f"\n📊 Статус: {response.status}")
                print(f"📋 Content-Type: {response.headers.get('Content-Type')}")

                if response.status == 200:
                    text = await response.text()
                    print(f"\n📄 Размер ответа: {len(text)} символов")
                    print(f"\n📝 Первые 1000 символов ответа:")
                    print(text[:1000])
                    print("\n...")

                    try:
                        data = json.loads(text)
                        print(f"\n✅ JSON успешно распарсен!")
                        print(f"\n🔑 Тип данных: {type(data)}")

                        if isinstance(data, dict):
                            print(f"📋 Ключи верхнего уровня: {list(data.keys())}")

                            # Проверяем все возможные ключи
                            for key in data.keys():
                                value = data[key]
                                print(f"\n  '{key}': {type(value)}")
                                if isinstance(value, list):
                                    print(f"    Длина списка: {len(value)}")
                                    if len(value) > 0:
                                        print(f"    Первый элемент: {json.dumps(value[0], ensure_ascii=False, indent=6)[:500]}")
                                elif isinstance(value, (int, str, bool)):
                                    print(f"    Значение: {value}")

                        elif isinstance(data, list):
                            print(f"📋 Данные - это массив")
                            print(f"📏 Длина массива: {len(data)}")
                            if len(data) > 0:
                                print(f"\n📄 Первый элемент:")
                                print(json.dumps(data[0], ensure_ascii=False, indent=2))

                        # Сохраняем полный ответ
                        with open('timerman_debug_response.json', 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        print(f"\n💾 Полный ответ сохранен в timerman_debug_response.json")

                    except json.JSONDecodeError as e:
                        print(f"\n❌ Ошибка парсинга JSON: {e}")
                        print(f"\n📄 Полный текст ответа:")
                        print(text)

                else:
                    print(f"\n❌ Ошибка HTTP: {response.status}")
                    error_text = await response.text()
                    print(f"\n📄 Ответ сервера:")
                    print(error_text[:1000])

        except Exception as e:
            print(f"\n❌ Исключение: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)


if __name__ == "__main__":
    asyncio.run(test_api())
