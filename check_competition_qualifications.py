import asyncio
import aiosqlite

async def check():
    async with aiosqlite.connect('database.sqlite') as db:
        db.row_factory = aiosqlite.Row

        # Проверяем результаты соревнований по плаванию
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
            WHERE c.sport_type LIKE '%плав%'
              AND cp.finish_time IS NOT NULL
            LIMIT 10
        ''')
        rows = await cursor.fetchall()
        print('Плавание:')
        for row in rows:
            print(f'  {row["name"]}, {row["distance"]}km, время: {row["finish_time"]}, разряд: {row["qualification"]}, пол: {row["gender"]}')

        # Проверяем результаты соревнований по велоспорту
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
            WHERE c.sport_type LIKE '%велос%'
              AND cp.finish_time IS NOT NULL
            LIMIT 10
        ''')
        rows = await cursor.fetchall()
        print('\nВелоспорт:')
        for row in rows:
            print(f'  {row["name"]}, {row["distance"]}km, время: {row["finish_time"]}, разряд: {row["qualification"]}, пол: {row["gender"]}')

        # Проверим нормативы для плавания на 0.05км (50м)
        cursor = await db.execute('''
            SELECT rank, time_seconds
            FROM swimming_standards
            WHERE distance = 0.05 AND pool_length = 50 AND gender = 'male'
            ORDER BY time_seconds ASC
        ''')
        rows = await cursor.fetchall()
        print('\nНормативы плавания 50м (50m бассейн, мужчины):')
        for row in rows:
            print(f'  {row["rank"]}: {row["time_seconds"]}s')

        # Проверим нормативы для велоспорта на 5км
        cursor = await db.execute('''
            SELECT discipline, rank, time_seconds
            FROM cycling_standards
            WHERE distance = 5.0 AND gender = 'male' AND time_seconds IS NOT NULL
            ORDER BY time_seconds ASC
        ''')
        rows = await cursor.fetchall()
        print('\nНормативы велоспорт 5км (мужчины):')
        for row in rows:
            print(f'  {row["discipline"]} - {row["rank"]}: {row["time_seconds"]}s')

asyncio.run(check())
