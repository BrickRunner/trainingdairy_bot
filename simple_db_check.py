import asyncio
import aiosqlite
import os

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

async def check():
    print(f"Проверка БД: {DB_PATH}")
    print(f"Файл существует: {os.path.exists(DB_PATH)}")

    try:
        async with aiosqlite.connect(DB_PATH) as db:
            # Проверяем количество пользователей
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                row = await cursor.fetchone()
                print(f"Пользователей в БД: {row[0]}")

            # Проверяем количество соревнований
            async with db.execute("SELECT COUNT(*) FROM competitions") as cursor:
                row = await cursor.fetchone()
                print(f"Соревнований в БД: {row[0]}")

            # Проверяем количество участников соревнований
            async with db.execute("SELECT COUNT(*) FROM competition_participants") as cursor:
                row = await cursor.fetchone()
                print(f"Записей в competition_participants: {row[0]}")

            # Получаем примеры записей
            async with db.execute("SELECT user_id, competition_id, distance, distance_name, status, proposal_status FROM competition_participants LIMIT 5") as cursor:
                rows = await cursor.fetchall()
                print("\nПримеры записей:")
                for row in rows:
                    print(f"  user={row[0]}, comp={row[1]}, dist={row[2]}, name={row[3]}, status={row[4]}, proposal={row[5]}")

    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(check())
