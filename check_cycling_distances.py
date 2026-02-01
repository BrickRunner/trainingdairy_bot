import asyncio
import aiosqlite

async def check():
    async with aiosqlite.connect('database.sqlite') as db:
        db.row_factory = aiosqlite.Row

        # Проверим какие дистанции есть для велоспорта
        cursor = await db.execute('''
            SELECT DISTINCT distance, discipline, gender
            FROM cycling_standards
            WHERE time_seconds IS NOT NULL
            ORDER BY distance, discipline, gender
        ''')
        rows = await cursor.fetchall()
        print('Дистанции велоспорта в БД (с нормативами по времени):')
        for row in rows:
            print(f'  {row["distance"]}km, {row["discipline"]}, {row["gender"]}')

        # Проверим результаты соревнований по велоспорту с "Нет разряда"
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
              AND (cp.qualification IS NULL OR cp.qualification = 'Нет разряда' OR cp.qualification = '')
        ''')
        rows = await cursor.fetchall()
        print('\nВелоспорт с "Нет разряда" или NULL:')
        for row in rows:
            print(f'  {row["name"]}, {row["distance"]}km, время: {row["finish_time"]}, разряд: "{row["qualification"]}", пол: {row["gender"]}')

        # Проверим результаты соревнований по плаванию с "Нет разряда"
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
              AND (cp.qualification IS NULL OR cp.qualification = 'Нет разряда' OR cp.qualification = '')
        ''')
        rows = await cursor.fetchall()
        print('\nПлавание с "Нет разряда" или NULL:')
        for row in rows:
            print(f'  {row["name"]}, {row["distance"]}km, время: {row["finish_time"]}, разряд: "{row["qualification"]}", пол: {row["gender"]}')

asyncio.run(check())
