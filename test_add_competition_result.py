"""
Тест добавления результата соревнования с расчетом разряда.
Проверяет, что разряды по плаванию и велоспорту корректно сохраняются в БД.
"""
import asyncio
import aiosqlite
import os
from competitions.competitions_queries import add_competition, add_competition_result
from database.queries import add_user


async def test_swimming_result():
    """Тест добавления результата по плаванию"""
    print("=" * 60)
    print("ТЕСТ: Добавление результата по плаванию")
    print("=" * 60)

    try:
        # Создаем тестовое соревнование по плаванию
        comp_data = {
            'name': 'Тестовое соревнование - Плавание',
            'date': '2026-03-01',
            'city': 'Москва',
            'sport_type': 'плавание',
            'distances': [0.05, 0.1, 0.2],
            'is_official': 0
        }
        comp_id = await add_competition(comp_data)
        print(f"Создано соревнование ID: {comp_id}")

        # Создаем тестового пользователя
        async with aiosqlite.connect('database.sqlite') as db:
            # Проверяем, есть ли тестовый пользователь
            async with db.execute("SELECT id FROM users WHERE id = 999999") as cursor:
                user = await cursor.fetchone()
                if not user:
                    await db.execute(
                        "INSERT INTO users (id, username) VALUES (?, ?)",
                        (999999, "test_swimmer")
                    )
                    await db.execute(
                        "INSERT INTO user_settings (user_id, gender) VALUES (?, ?)",
                        (999999, "male")
                    )
                    await db.commit()
                    print("Создан тестовый пользователь ID: 999999")

            # Регистрируем на дистанцию
            await db.execute(
                """
                INSERT INTO competition_participants (user_id, competition_id, distance, status)
                VALUES (?, ?, ?, 'registered')
                """,
                (999999, comp_id, 0.1)
            )
            await db.commit()
            print("Пользователь зарегистрирован на 100м")

        # Добавляем результат: 100м за 55.00 секунд (должен быть I разряд)
        success = await add_competition_result(
            user_id=999999,
            competition_id=comp_id,
            distance=0.1,
            finish_time="55.00",
            place_overall=15
        )

        if success:
            print("[OK] Результат добавлен")

            # Проверяем, что сохранилось в БД
            async with aiosqlite.connect('database.sqlite') as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    """
                    SELECT finish_time, qualification
                    FROM competition_participants
                    WHERE user_id = ? AND competition_id = ?
                    """,
                    (999999, comp_id)
                ) as cursor:
                    result = await cursor.fetchone()
                    if result:
                        print(f"\nСохраненные данные:")
                        print(f"  Время: {result['finish_time']}")
                        print(f"  Разряд: {result['qualification']}")

                        if result['qualification'] == 'I':
                            print("\n[OK] ТЕСТ ПРОЙДЕН: Разряд рассчитан и сохранен правильно!")
                        elif result['qualification'] in ['Нет разряда', None]:
                            print("\n[FAIL] ТЕСТ НЕ ПРОЙДЕН: Разряд не рассчитан!")
                        else:
                            print(f"\n[WARN] Разряд сохранен как: {result['qualification']}")
        else:
            print("[FAIL] Ошибка добавления результата")

        # Очистка тестовых данных
        async with aiosqlite.connect('database.sqlite') as db:
            await db.execute("DELETE FROM competition_participants WHERE user_id = 999999")
            await db.execute("DELETE FROM competitions WHERE id = ?", (comp_id,))
            await db.execute("DELETE FROM user_settings WHERE user_id = 999999")
            await db.execute("DELETE FROM users WHERE id = 999999")
            await db.commit()
            print("\nТестовые данные удалены")

    except Exception as e:
        print(f"\n[ERROR] Ошибка теста: {e}")
        import traceback
        traceback.print_exc()


async def test_cycling_result():
    """Тест добавления результата по велоспорту"""
    print("\n" + "=" * 60)
    print("ТЕСТ: Добавление результата по велоспорту")
    print("=" * 60)

    try:
        # Создаем тестовое соревнование по велоспорту
        comp_data = {
            'name': 'Тестовое соревнование - Велоспорт',
            'date': '2026-03-01',
            'city': 'Москва',
            'sport_type': 'велоспорт',
            'distances': [10.0, 20.0],
            'is_official': 0
        }
        comp_id = await add_competition(comp_data)
        print(f"Создано соревнование ID: {comp_id}")

        # Создаем тестового пользователя
        async with aiosqlite.connect('database.sqlite') as db:
            # Проверяем, есть ли тестовый пользователь
            async with db.execute("SELECT id FROM users WHERE id = 999998") as cursor:
                user = await cursor.fetchone()
                if not user:
                    await db.execute(
                        "INSERT INTO users (id, username) VALUES (?, ?)",
                        (999998, "test_cyclist")
                    )
                    await db.execute(
                        "INSERT INTO user_settings (user_id, gender) VALUES (?, ?)",
                        (999998, "male")
                    )
                    await db.commit()
                    print("Создан тестовый пользователь ID: 999998")

            # Регистрируем на дистанцию
            await db.execute(
                """
                INSERT INTO competition_participants (user_id, competition_id, distance, status)
                VALUES (?, ?, ?, 'registered')
                """,
                (999998, comp_id, 10.0)
            )
            await db.commit()
            print("Пользователь зарегистрирован на 10км")

        # Добавляем результат: 10км за 12:30 (должен быть КМС)
        success = await add_competition_result(
            user_id=999998,
            competition_id=comp_id,
            distance=10.0,
            finish_time="12:30",
            place_overall=5
        )

        if success:
            print("[OK] Результат добавлен")

            # Проверяем, что сохранилось в БД
            async with aiosqlite.connect('database.sqlite') as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    """
                    SELECT finish_time, qualification
                    FROM competition_participants
                    WHERE user_id = ? AND competition_id = ?
                    """,
                    (999998, comp_id)
                ) as cursor:
                    result = await cursor.fetchone()
                    if result:
                        print(f"\nСохраненные данные:")
                        print(f"  Время: {result['finish_time']}")
                        print(f"  Разряд: {result['qualification']}")

                        if result['qualification'] == 'КМС':
                            print("\n[OK] ТЕСТ ПРОЙДЕН: Разряд рассчитан и сохранен правильно!")
                        elif result['qualification'] in ['Нет разряда', None]:
                            print("\n[FAIL] ТЕСТ НЕ ПРОЙДЕН: Разряд не рассчитан!")
                        else:
                            print(f"\n[WARN] Разряд сохранен как: {result['qualification']}")
        else:
            print("[FAIL] Ошибка добавления результата")

        # Очистка тестовых данных
        async with aiosqlite.connect('database.sqlite') as db:
            await db.execute("DELETE FROM competition_participants WHERE user_id = 999998")
            await db.execute("DELETE FROM competitions WHERE id = ?", (comp_id,))
            await db.execute("DELETE FROM user_settings WHERE user_id = 999998")
            await db.execute("DELETE FROM users WHERE id = 999998")
            await db.commit()
            print("\nТестовые данные удалены")

    except Exception as e:
        print(f"\n[ERROR] Ошибка теста: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Запуск всех тестов"""
    await test_swimming_result()
    await test_cycling_result()

    print("\n" + "=" * 60)
    print("ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
