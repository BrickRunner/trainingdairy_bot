"""
Тест плавания 100м за 50 секунд
"""
import asyncio
from utils.qualifications import get_qualification_async, time_to_seconds
import aiosqlite

async def test():
    # Проверяем нормативы для плавания 100м (мужчины, 50м бассейн)
    async with aiosqlite.connect('database.sqlite') as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute('''
            SELECT rank, time_seconds
            FROM swimming_standards
            WHERE distance = 0.1 AND pool_length = 50 AND gender = 'male'
            ORDER BY time_seconds ASC
        ''')
        rows = await cursor.fetchall()

        print("Нормативы плавания 100м (50м бассейн, мужчины):")
        for row in rows:
            print(f"  {row['rank']}: {row['time_seconds']}s")

    print("\n=== Тест: плавание 100м за 50 секунд ===")
    distance_km = 0.1
    time_seconds = time_to_seconds("0:50.00")
    gender = 'male'

    print(f"Distance: {distance_km}km")
    print(f"Time: 50.00s ({time_seconds}s)")
    print(f"Gender: {gender}")

    qual = await get_qualification_async('плавание', distance_km, time_seconds, gender, pool_length=50)
    print(f"\nРезультат: '{qual}'")

    # Ожидаем МС (51.50) или КМС (54.90)
    if time_seconds <= 51.50:
        print("Ожидается: МС")
    elif time_seconds <= 54.90:
        print("Ожидается: КМС")

asyncio.run(test())
