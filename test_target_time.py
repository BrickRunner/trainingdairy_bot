#!/usr/bin/env python3
"""Тест функции update_target_time"""

import asyncio
import sys

async def test():
    from competitions.competitions_queries import update_target_time
    import aiosqlite
    import os

    DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

    # Найдем любую регистрацию для теста
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """SELECT user_id, competition_id, distance, target_time
               FROM competition_participants
               LIMIT 1"""
        ) as cursor:
            row = await cursor.fetchone()

    if not row:
        print("❌ Нет данных для теста")
        return

    user_id, comp_id, distance, old_target = row
    print(f"Тестируем на записи:")
    print(f"  user_id: {user_id}")
    print(f"  competition_id: {comp_id}")
    print(f"  distance: {distance}")
    print(f"  Старое целевое время: {old_target}")

    # Тестируем обновление
    test_time = "01:30:00"
    print(f"\nВызываем update_target_time с новым временем: {test_time}")

    result = await update_target_time(user_id, comp_id, distance, test_time)
    print(f"Результат функции: {result} (тип: {type(result)})")

    # Проверяем что записалось
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """SELECT target_time
               FROM competition_participants
               WHERE user_id=? AND competition_id=? AND distance=?""",
            (user_id, comp_id, distance)
        ) as cursor:
            new_row = await cursor.fetchone()

    if new_row:
        new_target = new_row[0]
        print(f"\nЧто записалось в БД: '{new_target}' (тип: {type(new_target)})")

        if new_target == test_time:
            print("✅ ВСЁ ПРАВИЛЬНО! Записалось корректное время")
        elif new_target == "True" or new_target == "true" or new_target == str(result):
            print(f"❌ ОШИБКА! Записался результат функции ({result}) вместо времени ({test_time})")
        else:
            print(f"❌ ОШИБКА! Записалось что-то неожиданное: {new_target}")
    else:
        print("❌ Запись не найдена после обновления")

if __name__ == "__main__":
    asyncio.run(test())
