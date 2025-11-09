"""Проверка целевого времени в БД"""
import asyncio
import aiosqlite

async def check_target_times():
    async with aiosqlite.connect('database.sqlite') as db:
        db.row_factory = aiosqlite.Row

        print("=== Проверка таблицы competition_participants ===\n")

        # Получаем структуру таблицы
        cursor = await db.execute("PRAGMA table_info(competition_participants)")
        columns = await cursor.fetchall()
        print("Структура таблицы competition_participants:")
        for col in columns:
            print(f"  {col['name']}: {col['type']}")
        print()

        # Получаем записи с целевым временем
        cursor = await db.execute("""
            SELECT
                cp.id,
                cp.user_id,
                cp.competition_id,
                c.name as comp_name,
                cp.distance,
                cp.target_time,
                c.date
            FROM competition_participants cp
            LEFT JOIN competitions c ON c.id = cp.competition_id
            ORDER BY cp.id DESC
            LIMIT 10
        """)

        records = await cursor.fetchall()

        if records:
            print(f"Последние 10 регистраций на соревнования:\n")
            for rec in records:
                print(f"ID: {rec['id']}")
                print(f"  User ID: {rec['user_id']}")
                print(f"  Соревнование: {rec['comp_name']}")
                print(f"  Дата: {rec['date']}")
                print(f"  Дистанция: {rec['distance']} км")
                print(f"  Целевое время: {rec['target_time']}")
                print()
        else:
            print("Нет регистраций на соревнования")

if __name__ == "__main__":
    asyncio.run(check_target_times())
