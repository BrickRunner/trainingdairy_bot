"""
Тест подключения ученика к тренеру через deep link
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from database.queries import init_db, add_user, init_user_settings, get_user_settings
from coach.coach_queries import (
    set_coach_mode,
    get_coach_link_code,
    find_coach_by_code,
    add_student_to_coach,
    get_coach_students,
    get_student_coach
)


async def test_coach_link():
    """Тестирование подключения ученика к тренеру через deep link"""

    print("=" * 60)
    print("ТЕСТ: ПОДКЛЮЧЕНИЕ УЧЕНИКА К ТРЕНЕРУ ЧЕРЕЗ DEEP LINK")
    print("=" * 60)

    # Инициализация БД
    await init_db()
    print("✓ База данных инициализирована")

    # Тестовые ID - используем случайные для избежания конфликтов
    import random
    coach_id = 800000 + random.randint(1, 99999)
    student_id = 800000 + random.randint(100000, 199999)

    # Регистрируем тестовых пользователей
    await add_user(coach_id, "test_coach_link")
    await init_user_settings(coach_id)
    await add_user(student_id, "test_student_link")
    await init_user_settings(student_id)
    print("✓ Тестовые пользователи созданы")

    # --- Шаг 1: Тренер включает режим тренера ---
    print("\n--- Шаг 1: Тренер включает режим тренера ---")
    link_code = await set_coach_mode(coach_id, True)
    print(f"  Код тренера: {link_code}")

    # --- Шаг 2: Проверяем что код можно получить ---
    print("\n--- Шаг 2: Проверка кода тренера ---")
    stored_code = await get_coach_link_code(coach_id)
    print(f"  Сохранённый код: {stored_code}")
    assert stored_code == link_code, "Коды должны совпадать"
    print("  ✓ Код сохранён корректно")

    # --- Шаг 3: Симуляция deep link - находим тренера по коду ---
    print("\n--- Шаг 3: Поиск тренера по коду (симуляция deep link) ---")

    # Симулируем получение кода из deep link: t.me/bot?start=coach_XXXXXXXX
    deep_link_param = f"coach_{link_code}"
    print(f"  Deep link параметр: {deep_link_param}")

    # Извлекаем код как в handlers.py
    extracted_code = deep_link_param.replace("coach_", "").upper()
    print(f"  Извлечённый код: {extracted_code}")

    found_coach_id = await find_coach_by_code(extracted_code)
    print(f"  Найден тренер ID: {found_coach_id}")
    assert found_coach_id == coach_id, "Должен найтись правильный тренер"
    print("  ✓ Тренер найден по коду из deep link")

    # --- Шаг 4: Добавляем ученика к тренеру ---
    print("\n--- Шаг 4: Добавление ученика к тренеру ---")
    success = await add_student_to_coach(found_coach_id, student_id)
    print(f"  Результат: {success}")
    assert success, "Ученик должен быть добавлен"
    print("  ✓ Ученик успешно подключён к тренеру")

    # --- Шаг 5: Проверяем связь со стороны тренера ---
    print("\n--- Шаг 5: Проверка списка учеников тренера ---")
    students = await get_coach_students(coach_id)
    print(f"  Количество учеников: {len(students)}")
    assert len(students) == 1, "Должен быть 1 ученик"
    assert students[0]['id'] == student_id, "ID ученика должен совпадать"
    print("  ✓ Ученик есть в списке тренера")

    # --- Шаг 6: Проверяем связь со стороны ученика ---
    print("\n--- Шаг 6: Проверка тренера ученика ---")
    coach = await get_student_coach(student_id)
    print(f"  Тренер ученика: {coach}")
    assert coach is not None, "Тренер должен быть найден"
    assert coach['id'] == coach_id, "ID тренера должен совпадать"
    print("  ✓ Тренер найден у ученика")

    # --- Шаг 7: Повторное добавление должно вернуть False ---
    print("\n--- Шаг 7: Проверка защиты от дублирования ---")
    success2 = await add_student_to_coach(found_coach_id, student_id)
    print(f"  Повторное добавление: {success2}")
    assert not success2, "Повторное добавление должно вернуть False"
    print("  ✓ Защита от дублирования работает")

    print("\n" + "=" * 60)
    print("ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    print("=" * 60)
    print("\nСоединение тренера и ученика через deep link работает корректно.")
    print(f"Формат ссылки: https://t.me/YOUR_BOT?start=coach_{link_code}")


if __name__ == "__main__":
    asyncio.run(test_coach_link())
