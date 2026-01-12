"""
Тест: Просмотр тренировок ученика тренером
"""

import asyncio
import random
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from database.queries import init_db, add_user, init_user_settings
from coach.coach_queries import set_coach_mode, add_student_to_coach
from coach.coach_training_queries import (
    add_training_for_student,
    get_student_trainings,
    get_training_with_comments,
    add_comment_to_training
)


async def test_coach_trainings():
    """Тест просмотра тренировок ученика"""

    print("=" * 60)
    print("ТЕСТ: ПРОСМОТР ТРЕНИРОВОК УЧЕНИКА ТРЕНЕРОМ")
    print("=" * 60)

    await init_db()
    print("✓ База данных инициализирована")

    # Случайные ID
    coach_id = 700000 + random.randint(1, 99999)
    student_id = 700000 + random.randint(100000, 199999)

    # Создаём пользователей
    await add_user(coach_id, "test_coach_tr")
    await init_user_settings(coach_id)
    await add_user(student_id, "test_student_tr")
    await init_user_settings(student_id)
    print("✓ Пользователи созданы")

    # Связываем тренера и ученика
    await set_coach_mode(coach_id, True)
    await add_student_to_coach(coach_id, student_id)
    print("✓ Тренер и ученик связаны")

    # Добавляем тренировку для ученика
    training_data = {
        'type': 'кросс',
        'date': '2025-01-04',
        'time': '10:00',
        'duration': 60,
        'distance': 10.0,
        'avg_pace': '06:00',
        'pace_unit': 'мин/км',
        'avg_pulse': 145,
        'fatigue_level': 5
    }
    training_id = await add_training_for_student(coach_id, student_id, training_data)
    print(f"✓ Тренировка добавлена (ID: {training_id})")

    # Получаем тренировки ученика
    trainings = await get_student_trainings(student_id)
    print(f"\n--- Тренировки ученика ({len(trainings)}) ---")

    for t in trainings:
        print(f"  ID: {t['id']}")
        print(f"  Тип: {t['type']}")
        print(f"  Дата: {t['date']}")
        print(f"  Длительность: {t['duration']} мин")
        print(f"  Дистанция: {t.get('distance', '-')} км")
        print(f"  Добавлено тренером: {t.get('added_by_coach_id', 'нет')}")
        print()

    if trainings:
        print("✓ Тренировки отображаются корректно")
    else:
        print("❌ Тренировки не найдены!")
        return

    # Получаем тренировку с комментариями
    training = await get_training_with_comments(training_id)
    print(f"\n--- Тренировка с комментариями ---")
    print(f"  ID: {training['id']}")
    print(f"  Комментариев: {len(training.get('comments', []))}")

    # Добавляем комментарий
    comment_id = await add_comment_to_training(training_id, coach_id, "Отличная работа!")
    print(f"✓ Комментарий добавлен (ID: {comment_id})")

    # Проверяем комментарий
    training = await get_training_with_comments(training_id)
    comments = training.get('comments', [])
    print(f"  Комментариев после добавления: {len(comments)}")

    if comments:
        print(f"  Текст комментария: {comments[0]['comment']}")
        print("✓ Комментарии работают")
    else:
        print("❌ Комментарий не найден!")

    print("\n" + "=" * 60)
    print("ТЕСТ ЗАВЕРШЁН УСПЕШНО!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_coach_trainings())
