#!/usr/bin/env python3
"""
Тест исправления UUID ошибки при предложении соревнований тренером
"""

import asyncio
import sys
import os

# Добавляем путь к модулям проекта
sys.path.insert(0, os.path.dirname(__file__))

from competitions.competitions_queries import get_or_create_competition_from_api, get_competition


async def test_uuid_fix():
    """Тест функции get_or_create_competition_from_api"""

    print("=" * 70)
    print("ТЕСТ: Исправление UUID ошибки")
    print("=" * 70)

    # Тестовые данные соревнования из API (с UUID)
    api_comp_1 = {
        'id': '78f22026-60f0-48de-90ff-14f356e61fc9',  # UUID из API
        'title': 'Тестовый Марафон Москвы',
        'date': '2026-04-20T10:00:00Z',
        'city': 'Москва',
        'place': 'Лужники',
        'sport_code': 'run',
        'distances': [
            {'name': '42.195 км', 'distance': 42.195},
            {'name': '21.1 км', 'distance': 21.1},
            {'name': '10 км', 'distance': 10.0}
        ],
        'url': 'https://test.russiarunning.com/event/test-marathon-2026',
        'organizer': 'Russia Running'
    }

    # Тест 1: Создание нового соревнования
    print("\n1. Создание нового соревнования из API данных...")
    try:
        db_id_1 = await get_or_create_competition_from_api(api_comp_1)
        print(f"   ✅ Соревнование создано с БД ID: {db_id_1}")
        print(f"   ✅ Тип ID: {type(db_id_1).__name__} (должен быть int)")

        # Проверяем что ID действительно integer
        assert isinstance(db_id_1, int), f"❌ ID должен быть int, а не {type(db_id_1)}"

        # Проверяем что соревнование в БД
        comp_from_db = await get_competition(db_id_1)
        assert comp_from_db is not None, "❌ Соревнование не найдено в БД"
        print(f"   ✅ Соревнование найдено в БД: {comp_from_db['name']}")

    except Exception as e:
        print(f"   ❌ ОШИБКА при создании: {e}")
        return False

    # Тест 2: Повторный вызов с тем же URL (должен вернуть существующий ID)
    print("\n2. Повторный вызов с тем же source_url...")
    try:
        db_id_2 = await get_or_create_competition_from_api(api_comp_1)
        print(f"   ✅ Возвращен существующий БД ID: {db_id_2}")

        # Проверяем что ID тот же
        assert db_id_1 == db_id_2, f"❌ ID должны совпадать: {db_id_1} != {db_id_2}"
        print(f"   ✅ ID совпадают (дубликаты не создаются)")

    except Exception as e:
        print(f"   ❌ ОШИБКА при повторном вызове: {e}")
        return False

    # Тест 3: Новое соревнование с другим UUID и URL
    print("\n3. Создание второго соревнования...")
    api_comp_2 = {
        'id': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',  # Другой UUID
        'title': 'Тестовый Полумарафон СПб',
        'date': '2026-05-15T09:00:00Z',
        'city': 'Санкт-Петербург',
        'place': 'Дворцовая площадь',
        'sport_code': 'run',
        'distances': [
            {'name': '21.1 км', 'distance': 21.1},
            {'name': '10 км', 'distance': 10.0}
        ],
        'url': 'https://test.russiarunning.com/event/test-halfmarathon-spb-2026',
        'organizer': 'Russia Running'
    }

    try:
        db_id_3 = await get_or_create_competition_from_api(api_comp_2)
        print(f"   ✅ Второе соревнование создано с БД ID: {db_id_3}")

        # Проверяем что ID разные
        assert db_id_1 != db_id_3, f"❌ ID должны отличаться: {db_id_1} == {db_id_3}"
        print(f"   ✅ ID отличаются (разные соревнования)")

        comp_from_db = await get_competition(db_id_3)
        assert comp_from_db is not None, "❌ Второе соревнование не найдено в БД"
        print(f"   ✅ Второе соревнование в БД: {comp_from_db['name']}")

    except Exception as e:
        print(f"   ❌ ОШИБКА при создании второго: {e}")
        return False

    # Тест 4: Проверка преобразования в int (как в обработчике)
    print("\n4. Проверка преобразования в int (как в callback)...")
    try:
        # Симулируем callback: f"coach:sel_comp:{student_id}:{comp_db_id}"
        callback_data = f"coach:sel_comp:123456789:{db_id_1}"
        print(f"   Callback: {callback_data}")

        # Симулируем обработчик
        parts = callback_data.split(":")
        student_id = int(parts[2])
        comp_id = int(parts[3])  # Это должно работать теперь!

        print(f"   ✅ student_id: {student_id} (type: {type(student_id).__name__})")
        print(f"   ✅ comp_id: {comp_id} (type: {type(comp_id).__name__})")
        print(f"   ✅ Преобразование в int работает корректно!")

    except ValueError as e:
        print(f"   ❌ ОШИБКА при преобразовании в int: {e}")
        return False

    print("\n" + "=" * 70)
    print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    print("=" * 70)

    return True


if __name__ == "__main__":
    result = asyncio.run(test_uuid_fix())
    sys.exit(0 if result else 1)
