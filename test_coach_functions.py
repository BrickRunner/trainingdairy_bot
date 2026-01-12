"""
Тестирование функций режима тренера
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from coach.coach_queries import (
    set_coach_mode,
    is_user_coach,
    get_coach_link_code,
    find_coach_by_code,
    add_student_to_coach,
    get_coach_students,
    remove_student_from_coach,
    get_student_coach,
    remove_coach_from_student
)
from coach.coach_training_queries import (
    add_training_for_student,
    get_student_trainings,
    get_training_with_comments,
    add_comment_to_training,
    set_student_nickname,
    get_student_display_name,
    can_coach_access_student
)
from database.queries import init_db, add_user, init_user_settings


async def test_coach_functions():
    """Тестирование всех функций тренерского модуля"""

    print("=" * 60)
    print("ТЕСТИРОВАНИЕ ФУНКЦИЙ РЕЖИМА ТРЕНЕРА")
    print("=" * 60)

    # Инициализация БД
    await init_db()
    print("✓ База данных инициализирована")

    # Тестовые ID - используем случайные для избежания конфликтов
    import random
    coach_id = 900000 + random.randint(1, 99999)
    student_id = 900000 + random.randint(100000, 199999)

    # Регистрируем тестовых пользователей
    await add_user(coach_id, "test_coach")
    await init_user_settings(coach_id)
    await add_user(student_id, "test_student")
    await init_user_settings(student_id)
    print("✓ Тестовые пользователи созданы")

    # --- ТЕСТ 1: Включение режима тренера ---
    print("\n--- Тест 1: Включение режима тренера ---")
    link_code = await set_coach_mode(coach_id, True)
    print(f"  Код для учеников: {link_code}")

    is_coach = await is_user_coach(coach_id)
    print(f"  is_user_coach: {is_coach}")
    assert is_coach, "Пользователь должен быть тренером"
    print("  ✓ Режим тренера включён")

    # --- ТЕСТ 2: Получение кода тренера ---
    print("\n--- Тест 2: Получение кода тренера ---")
    stored_code = await get_coach_link_code(coach_id)
    print(f"  Сохранённый код: {stored_code}")
    assert stored_code == link_code, "Коды должны совпадать"
    print("  ✓ Код сохранён корректно")

    # --- ТЕСТ 3: Поиск тренера по коду ---
    print("\n--- Тест 3: Поиск тренера по коду ---")
    found_coach_id = await find_coach_by_code(link_code)
    print(f"  Найден тренер ID: {found_coach_id}")
    assert found_coach_id == coach_id, "Должен найтись правильный тренер"
    print("  ✓ Тренер найден по коду")

    # --- ТЕСТ 4: Добавление ученика ---
    print("\n--- Тест 4: Добавление ученика ---")
    success = await add_student_to_coach(coach_id, student_id)
    print(f"  Результат добавления: {success}")
    assert success, "Ученик должен быть добавлен"
    print("  ✓ Ученик добавлен")

    # Повторное добавление
    success2 = await add_student_to_coach(coach_id, student_id)
    print(f"  Повторное добавление: {success2}")
    assert not success2, "Повторное добавление должно вернуть False"
    print("  ✓ Повторное добавление корректно отклонено")

    # --- ТЕСТ 5: Получение списка учеников ---
    print("\n--- Тест 5: Получение списка учеников ---")
    students = await get_coach_students(coach_id)
    print(f"  Количество учеников: {len(students)}")
    assert len(students) == 1, "Должен быть 1 ученик"
    assert students[0]['id'] == student_id, "ID ученика должен совпадать"
    print("  ✓ Список учеников получен")

    # --- ТЕСТ 6: Проверка доступа тренера к ученику ---
    print("\n--- Тест 6: Проверка доступа тренера ---")
    has_access = await can_coach_access_student(coach_id, student_id)
    print(f"  Доступ к ученику: {has_access}")
    assert has_access, "Тренер должен иметь доступ"
    print("  ✓ Доступ есть")

    # --- ТЕСТ 7: Установка псевдонима ---
    print("\n--- Тест 7: Установка псевдонима ---")
    await set_student_nickname(coach_id, student_id, "Иван Тестовый")
    display_name = await get_student_display_name(coach_id, student_id)
    print(f"  Отображаемое имя: {display_name}")
    assert display_name == "Иван Тестовый", "Псевдоним должен отображаться"
    print("  ✓ Псевдоним установлен")

    # --- ТЕСТ 8: Добавление тренировки для ученика ---
    print("\n--- Тест 8: Добавление тренировки ---")
    training_data = {
        'type': 'кросс',
        'date': '2025-01-04',
        'time': '10:00',
        'duration': 60,
        'distance': 10.0,
        'avg_pace': '06:00',
        'pace_unit': 'мин/км',
        'fatigue_level': 5
    }
    training_id = await add_training_for_student(coach_id, student_id, training_data)
    print(f"  ID тренировки: {training_id}")
    assert training_id > 0, "Тренировка должна быть создана"
    print("  ✓ Тренировка добавлена")

    # --- ТЕСТ 9: Получение тренировок ученика ---
    print("\n--- Тест 9: Получение тренировок ученика ---")
    trainings = await get_student_trainings(student_id)
    print(f"  Количество тренировок: {len(trainings)}")
    assert len(trainings) >= 1, "Должна быть минимум 1 тренировка"
    print("  ✓ Тренировки получены")

    # --- ТЕСТ 10: Добавление комментария к тренировке ---
    print("\n--- Тест 10: Добавление комментария ---")
    comment_id = await add_comment_to_training(training_id, coach_id, "Отлично поработали!")
    print(f"  ID комментария: {comment_id}")
    assert comment_id > 0, "Комментарий должен быть создан"
    print("  ✓ Комментарий добавлен")

    # --- ТЕСТ 11: Получение тренировки с комментариями ---
    print("\n--- Тест 11: Получение тренировки с комментариями ---")
    training_with_comments = await get_training_with_comments(training_id)
    print(f"  Количество комментариев: {len(training_with_comments.get('comments', []))}")
    assert len(training_with_comments.get('comments', [])) == 1, "Должен быть 1 комментарий"
    print("  ✓ Тренировка с комментариями получена")

    # --- ТЕСТ 12: Получение тренера ученика ---
    print("\n--- Тест 12: Получение тренера ученика ---")
    coach = await get_student_coach(student_id)
    print(f"  Тренер: {coach}")
    assert coach is not None, "Тренер должен быть найден"
    assert coach['id'] == coach_id, "ID тренера должен совпадать"
    print("  ✓ Тренер ученика найден")

    # --- ТЕСТ 13: Удаление ученика тренером ---
    print("\n--- Тест 13: Удаление ученика тренером ---")
    await remove_student_from_coach(coach_id, student_id)
    students_after = await get_coach_students(coach_id)
    print(f"  Учеников после удаления: {len(students_after)}")
    assert len(students_after) == 0, "Учеников быть не должно"
    print("  ✓ Ученик удалён")

    # --- ТЕСТ 14: Повторное добавление и отключение учеником ---
    print("\n--- Тест 14: Отключение от тренера учеником ---")
    await add_student_to_coach(coach_id, student_id)
    await remove_coach_from_student(student_id)
    coach_after = await get_student_coach(student_id)
    print(f"  Тренер после отключения: {coach_after}")
    assert coach_after is None, "Тренера быть не должно"
    print("  ✓ Ученик отключился от тренера")

    # --- ТЕСТ 15: Выключение режима тренера ---
    print("\n--- Тест 15: Выключение режима тренера ---")
    await set_coach_mode(coach_id, False)
    is_coach_after = await is_user_coach(coach_id)
    print(f"  is_user_coach после выключения: {is_coach_after}")
    assert not is_coach_after, "Пользователь не должен быть тренером"
    print("  ✓ Режим тренера выключен")

    print("\n" + "=" * 60)
    print("ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_coach_functions())
