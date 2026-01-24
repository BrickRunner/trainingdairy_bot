"""
Тестирование логики изменения целевого времени
"""
import asyncio
import aiosqlite
import os
from datetime import datetime, timedelta

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

async def test_edit_target_time_logic():
    """Тест логики изменения целевого времени"""

    print("="*80)
    print("ТЕСТ: Изменение целевого времени")
    print("="*80)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Получаем пользователя с соревнованиями
        async with db.execute(
            "SELECT DISTINCT user_id FROM competition_participants LIMIT 1"
        ) as cursor:
            user_row = await cursor.fetchone()

        if not user_row:
            print("❌ Нет пользователей с соревнованиями")
            return

        user_id = user_row[0]
        print(f"\n✓ Используем user_id: {user_id}")

        # Получаем соревнования этого пользователя
        async with db.execute(
            """
            SELECT cp.*, c.name, c.date
            FROM competition_participants cp
            JOIN competitions c ON c.id = cp.competition_id
            WHERE cp.user_id = ? AND c.date >= date('now')
            LIMIT 3
            """,
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()

        print(f"\n✓ Найдено соревнований: {len(rows)}\n")

        for i, row in enumerate(rows, 1):
            comp = dict(row)
            print(f"{i}. {comp['name']}")
            print(f"   Competition ID: {comp['competition_id']}")
            print(f"   Distance: {comp['distance']}")
            print(f"   Distance name: {comp['distance_name']}")
            print(f"   Target time: {comp['target_time']}")
            print(f"   Proposed by coach: {comp['proposed_by_coach']}")
            print(f"   Proposed by coach ID: {comp['proposed_by_coach_id']}")

            # Тестируем логику поиска тренера
            distance = comp['distance']
            competition_id = comp['competition_id']

            print(f"\n   Тестируем поиск тренера для distance={distance}...")

            # Старая логика (с ошибкой)
            async with db.execute(
                """
                SELECT proposed_by_coach_id FROM competition_participants
                WHERE user_id = ? AND competition_id = ? AND distance = ? AND proposed_by_coach = 1
                """,
                (user_id, competition_id, distance)
            ) as cursor:
                old_result = await cursor.fetchone()

            # Новая логика (исправленная)
            if distance in (0, 0.0, None):
                async with db.execute(
                    """
                    SELECT proposed_by_coach_id FROM competition_participants
                    WHERE user_id = ? AND competition_id = ?
                      AND (distance = 0 OR distance IS NULL)
                      AND proposed_by_coach = 1
                    """,
                    (user_id, competition_id)
                ) as cursor:
                    new_result = await cursor.fetchone()
            else:
                async with db.execute(
                    """
                    SELECT proposed_by_coach_id FROM competition_participants
                    WHERE user_id = ? AND competition_id = ? AND distance = ? AND proposed_by_coach = 1
                    """,
                    (user_id, competition_id, distance)
                ) as cursor:
                    new_result = await cursor.fetchone()

            print(f"   Старая логика: {old_result}")
            print(f"   Новая логика: {new_result}")

            if distance in (0, 0.0, None) and old_result != new_result:
                print(f"   ⚠️  ПРОБЛЕМА НАЙДЕНА! Для distance=0 старая логика не работала")
            elif old_result == new_result:
                print(f"   ✅ Обе логики работают одинаково")

            print()

        # Тестируем update_target_time
        from competitions.competitions_queries import update_target_time

        if rows:
            test_comp = dict(rows[0])
            test_distance = test_comp['distance']
            test_comp_id = test_comp['competition_id']

            print(f"\n{'='*80}")
            print(f"ТЕСТ: Обновление целевого времени")
            print(f"{'='*80}")
            print(f"Competition ID: {test_comp_id}")
            print(f"Distance: {test_distance}")
            print(f"User ID: {user_id}")

            # Пробуем обновить целевое время
            new_target = "01:30:00"
            success = await update_target_time(user_id, test_comp_id, test_distance, new_target)

            if success:
                print(f"✅ Целевое время успешно обновлено на {new_target}")

                # Проверяем, что оно действительно обновилось
                async with db.execute(
                    """
                    SELECT target_time FROM competition_participants
                    WHERE user_id = ? AND competition_id = ?
                    """,
                    (user_id, test_comp_id)
                ) as cursor:
                    check_row = await cursor.fetchone()
                    if check_row:
                        print(f"✅ Проверка: target_time = {check_row[0]}")
            else:
                print(f"❌ Не удалось обновить целевое время")

        # Тестируем get_user_competition_registration
        from competitions.competitions_queries import get_user_competition_registration

        if rows:
            test_comp = dict(rows[0])
            test_distance = test_comp['distance']
            test_comp_id = test_comp['competition_id']

            print(f"\n{'='*80}")
            print(f"ТЕСТ: get_user_competition_registration")
            print(f"{'='*80}")

            participant = await get_user_competition_registration(user_id, test_comp_id, test_distance)

            if participant:
                print(f"✅ Регистрация найдена:")
                print(f"   Distance: {participant.get('distance')}")
                print(f"   Distance name: {participant.get('distance_name')}")
                print(f"   Target time: {participant.get('target_time')}")
            else:
                print(f"❌ Регистрация НЕ найдена")

        print(f"\n{'='*80}")
        print("ТЕСТЫ ЗАВЕРШЕНЫ")
        print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(test_edit_target_time_logic())
