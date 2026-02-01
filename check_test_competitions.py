"""
Проверка тестовых соревнований в БД.
"""
import asyncio
import aiosqlite


async def check():
    async with aiosqlite.connect('database.sqlite') as db:
        db.row_factory = aiosqlite.Row

        print("Последние 5 соревнований в БД:")
        async with db.execute(
            "SELECT id, name, sport_type, date FROM competitions ORDER BY id DESC LIMIT 5"
        ) as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                print(f"ID {row['id']}: {row['name']}, sport_type='{row['sport_type']}', date={row['date']}")


if __name__ == "__main__":
    asyncio.run(check())
