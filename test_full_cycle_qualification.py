"""
Тест полного цикла сохранения разрядов
"""
import asyncio
from competitions.competitions_queries import add_competition_result
from utils.qualifications import get_qualification_async, time_to_seconds
import aiosqlite

async def test_add_result():
    """Тест добавления результата с разрядом"""

    # Тестовые данные
    user_id = 1611441720  # Из логов
    competition_id = 1  # Первое соревнование
    distance = 42.2  # Марафон
    finish_time = "2:25:00"
    gender = 'male'

    print("=== Тест добавления результата марафона ===")
    print(f"User ID: {user_id}")
    print(f"Competition ID: {competition_id}")
    print(f"Distance: {distance}km")
    print(f"Finish time: {finish_time}")

    # Проверим, что разряд рассчитывается правильно
    time_sec = time_to_seconds(finish_time)
    qual = await get_qualification_async('бег', distance, time_sec, gender)
    print(f"Ожидаемый разряд: {qual}")

    # Добавим результат
    print("\nДобавление результата в БД...")
    success = await add_competition_result(
        user_id=user_id,
        competition_id=competition_id,
        distance=distance,
        finish_time=finish_time,
        place_overall=100,
        place_age_category=10,
        age_category="M30-34"
    )

    if success:
        print("Результат добавлен успешно!")

        # Проверим, что разряд сохранился
        async with aiosqlite.connect('database.sqlite') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT qualification, finish_time
                FROM competition_participants
                WHERE user_id = ? AND competition_id = ? AND distance = ?
            ''', (user_id, competition_id, distance))
            row = await cursor.fetchone()

            if row:
                print(f"\nСохраненный разряд в БД: {row['qualification']}")
                print(f"Финишное время: {row['finish_time']}")

                if row['qualification'] == qual:
                    print("OK: Разряд сохранился правильно!")
                else:
                    print(f"ОШИБКА: Ожидался '{qual}', а сохранился '{row['qualification']}'")
            else:
                print("ОШИБКА: Результат не найден в БД")
    else:
        print("ОШИБКА: Не удалось добавить результат")

asyncio.run(test_add_result())
