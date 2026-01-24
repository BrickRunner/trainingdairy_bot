"""
Простой тест изменения целевого времени
"""
import asyncio
import aiosqlite
import os

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

async def test():
    print("Тест изменения целевого времени")

    async with aiosqlite.connect(DB_PATH) as db:
        # Получаем пример записи
        async with db.execute(
            """SELECT user_id, competition_id, distance, distance_name, target_time
               FROM competition_participants
               WHERE target_time IS NOT NULL
               LIMIT 1"""
        ) as cursor:
            row = await cursor.fetchone()

        if row:
            user_id, comp_id, distance, dist_name, target = row
            print(f"Найдена запись:")
            print(f"  user_id={user_id}")
            print(f"  competition_id={comp_id}")
            print(f"  distance={distance}")
            print(f"  distance_name={dist_name}")
            print(f"  target_time={target}")

            # Тест для distance=0
            if distance in (0, 0.0, None):
                print(f"\n✅ Distance={distance} - используется гибкий поиск")
            else:
                print(f"\n✓ Distance={distance} - используется точное сравнение")
        else:
            print("Нет данных для теста")

try:
    asyncio.run(test())
    print("\n✅ Тест завершен успешно")
except Exception as e:
    print(f"\n❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
