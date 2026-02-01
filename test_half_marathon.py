"""
Тест для полумарафона (21.1 vs 21.0975)
"""
import asyncio
from utils.qualifications import get_qualification_async, time_to_seconds
import aiosqlite

async def check():
    # Проверим дистанцию полумарафона в БД
    async with aiosqlite.connect('database.sqlite') as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute('''
            SELECT DISTINCT distance
            FROM running_standards
            WHERE distance > 20 AND distance < 25
        ''')
        rows = await cursor.fetchall()
        print('Дистанции полумарафона в БД:')
        for row in rows:
            print(f'  {row["distance"]}km')

    print('\n=== Тест: полумарафон 21.1км vs 21.0975км ===')

    # Тест 1: 21.1 км (то, что обычно вводят пользователи)
    distance_km = 21.1
    time_seconds = time_to_seconds("1:20:00")
    gender = 'male'

    qual = await get_qualification_async('бег', distance_km, time_seconds, gender)
    print(f'21.1км, 1:20:00, male: {qual}')

    # Тест 2: 21.0975 км (точное значение)
    distance_km = 21.0975
    time_seconds = time_to_seconds("1:20:00")

    qual = await get_qualification_async('бег', distance_km, time_seconds, gender)
    print(f'21.0975км, 1:20:00, male: {qual}')

    # Тест 3: Марафон 42.2 vs 42.195
    print('\n=== Тест: марафон 42.2км vs 42.195км ===')

    distance_km = 42.2
    time_seconds = time_to_seconds("2:35:00")

    qual = await get_qualification_async('бег', distance_km, time_seconds, gender)
    print(f'42.2км, 2:35:00, male: {qual}')

    distance_km = 42.195
    time_seconds = time_to_seconds("2:35:00")

    qual = await get_qualification_async('бег', distance_km, time_seconds, gender)
    print(f'42.195км, 2:35:00, male: {qual}')

asyncio.run(check())
