"""
Проверка расчета разряда для бега на 50км
"""
import asyncio
from utils.qualifications import get_qualification_async, time_to_seconds

async def check():
    # Проверим, есть ли нормативы для бега на 50км
    import aiosqlite
    async with aiosqlite.connect('database.sqlite') as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute('''
            SELECT DISTINCT distance
            FROM running_standards
            ORDER BY distance
        ''')
        rows = await cursor.fetchall()
        print('Дистанции для бега в БД:')
        for row in rows:
            print(f'  {row["distance"]}km')

    print('\n=== Тест: бег 50км ===')
    distance_km = 50.0
    time_seconds = time_to_seconds("1:15:38")
    gender = 'male'

    qual = await get_qualification_async('бег', distance_km, time_seconds, gender)
    print(f'Результат для бега 50км, 1:15:38: "{qual}"')

    # Проверим ближайшую дистанцию - 42.2км
    print('\n=== Тест: бег 42.2км (марафон) ===')
    distance_km = 42.2
    time_seconds = time_to_seconds("2:25:00")

    qual = await get_qualification_async('бег', distance_km, time_seconds, gender)
    print(f'Результат для бега 42.2км, 2:25:00: "{qual}"')

    # Проверим 100км
    print('\n=== Тест: бег 100км ===')
    distance_km = 100.0
    time_seconds = time_to_seconds("7:00:00")

    qual = await get_qualification_async('бег', distance_km, time_seconds, gender)
    print(f'Результат для бега 100км, 7:00:00: "{qual}"')

asyncio.run(check())
