"""
Скрипт для диагностики проблемы с запросом целевого времени
"""
import asyncio
import aiosqlite
import os

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

async def test_target_time_check(user_id: int, comp_id: int):
    """Проверить логику has_target_time"""

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        print(f"\n{'='*80}")
        print(f"ТЕСТ: Проверка целевого времени")
        print(f"User ID: {user_id}, Competition ID: {comp_id}")
        print(f"{'='*80}\n")

        # Получаем все регистрации на это соревнование
        async with db.execute(
            """
            SELECT id, distance, distance_name, target_time, proposal_status, status
            FROM competition_participants
            WHERE user_id = ? AND competition_id = ?
            """,
            (user_id, comp_id)
        ) as cursor:
            rows = await cursor.fetchall()

            if not rows:
                print("❌ НЕТ РЕГИСТРАЦИЙ на это соревнование!")
                return

            for row in rows:
                print(f"Регистрация ID: {row[0]}")
                print(f"  Distance: {row[1]} km")
                print(f"  Distance Name: '{row[2]}'")
                print(f"  Target Time: '{row[3]}'")
                print(f"  Proposal Status: '{row[4]}'")
                print(f"  Status: '{row[5]}'")
                print()

                # Эмуляция проверки has_target_time
                target_time_value = row[3]

                # Старая проверка
                old_check = target_time_value is not None and target_time_value != ''
                print(f"  Старая проверка: has_target_time = {old_check}")

                # Новая проверка
                new_check = (
                    target_time_value is not None
                    and target_time_value != ''
                    and str(target_time_value).lower() != 'none'
                )
                print(f"  Новая проверка: has_target_time = {new_check}")

                # Детали
                print(f"\n  Детали:")
                print(f"    target_time_value is not None: {target_time_value is not None}")
                print(f"    target_time_value != '': {target_time_value != ''}")
                print(f"    str(target_time_value).lower(): '{str(target_time_value).lower()}'")
                print(f"    != 'none': {str(target_time_value).lower() != 'none'}")
                print()

                # Вывод
                if new_check:
                    print(f"  ✅ Тренер УКАЗАЛ целевое время → НЕ запрашивать у ученика")
                else:
                    print(f"  ❌ Тренер НЕ указал целевое время → ЗАПРОСИТЬ у ученика")
                print()

async def main():
    import sys

    if len(sys.argv) < 3:
        print("Usage: python test_target_time_debug.py <user_id> <competition_id>")
        print("\nПример: python test_target_time_debug.py 123456789 42")
        sys.exit(1)

    user_id = int(sys.argv[1])
    comp_id = int(sys.argv[2])

    await test_target_time_check(user_id, comp_id)

if __name__ == "__main__":
    asyncio.run(main())
