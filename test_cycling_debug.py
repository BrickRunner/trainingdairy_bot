"""
Тест для велоспорта
"""
import asyncio
import aiosqlite
from utils.qualifications import get_qualification_async, time_to_seconds

async def check_cycling_standards():
    """Проверяем нормативы велоспорта в БД"""
    async with aiosqlite.connect('database.sqlite') as db:
        db.row_factory = aiosqlite.Row

        # Проверяем все дистанции для мужчин
        cursor = await db.execute('''
            SELECT DISTINCT distance, discipline, gender
            FROM cycling_standards
            WHERE time_seconds IS NOT NULL
            ORDER BY distance, gender
        ''')
        rows = await cursor.fetchall()

        print('=== Дистанции велоспорта в БД ===')
        for row in rows:
            print(f'  {row["distance"]}km, {row["discipline"]}, {row["gender"]}')

        # Проверяем нормативы для 50км (индивидуальная гонка, мужчины)
        cursor = await db.execute('''
            SELECT rank, time_seconds
            FROM cycling_standards
            WHERE distance = 50.0
              AND discipline = 'индивидуальная гонка'
              AND gender = 'male'
              AND time_seconds IS NOT NULL
            ORDER BY time_seconds ASC
        ''')
        rows = await cursor.fetchall()

        print('\n=== Нормативы велоспорт 50км (индивидуальная гонка, мужчины) ===')
        for row in rows:
            print(f'  {row["rank"]}: {row["time_seconds"]}s ({row["time_seconds"]/60:.2f} мин)')

async def test_cycling_calculation():
    """Тест расчета разряда для велоспорта"""
    print('\n=== Тест расчета разряда ===')

    # Тест 1: 50км за 1:12:30
    distance_km = 50.0
    time_seconds = time_to_seconds("1:12:30")
    gender = 'male'

    print(f'Дистанция: {distance_km}km')
    print(f'Время: 1:12:30 ({time_seconds}s)')
    print(f'Пол: {gender}')

    qual = await get_qualification_async('велоспорт', distance_km, time_seconds, gender, discipline='индивидуальная гонка')
    print(f'Результат: "{qual}"')

    # Тест 2: проверим с разными названиями спорта
    print('\n=== Тест с разными названиями ===')
    for sport_name in ['велоспорт', 'вело', 'bike', 'cycling']:
        qual = await get_qualification_async(sport_name, distance_km, time_seconds, gender, discipline='индивидуальная гонка')
        print(f'{sport_name}: "{qual}"')

async def check_existing_results():
    """Проверяем существующие результаты по велоспорту"""
    async with aiosqlite.connect('database.sqlite') as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute('''
            SELECT
                c.name,
                c.sport_type,
                cp.distance,
                cp.finish_time,
                cp.qualification,
                us.gender
            FROM competition_participants cp
            JOIN competitions c ON c.id = cp.competition_id
            LEFT JOIN user_settings us ON us.user_id = cp.user_id
            WHERE c.sport_type LIKE '%вело%'
              AND cp.finish_time IS NOT NULL
            LIMIT 10
        ''')
        rows = await cursor.fetchall()

        print('\n=== Существующие результаты по велоспорту ===')
        for row in rows:
            print(f'{row["name"]}: {row["distance"]}km, {row["finish_time"]}, разряд: "{row["qualification"]}", sport_type: "{row["sport_type"]}"')

async def main():
    await check_cycling_standards()
    await test_cycling_calculation()
    await check_existing_results()

asyncio.run(main())
