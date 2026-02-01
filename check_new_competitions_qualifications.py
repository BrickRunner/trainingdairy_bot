"""
Проверка разрядов в новых соревнованиях
"""
import asyncio
import aiosqlite
from datetime import datetime, timedelta

async def check():
    async with aiosqlite.connect('database.sqlite') as db:
        db.row_factory = aiosqlite.Row

        # Проверим последние добавленные результаты
        cursor = await db.execute('''
            SELECT
                c.id,
                c.name,
                c.sport_type,
                cp.distance,
                cp.finish_time,
                cp.qualification,
                cp.result_added_at,
                us.gender
            FROM competition_participants cp
            JOIN competitions c ON c.id = cp.competition_id
            LEFT JOIN user_settings us ON us.user_id = cp.user_id
            WHERE cp.finish_time IS NOT NULL
            ORDER BY cp.result_added_at DESC
            LIMIT 20
        ''')
        rows = await cursor.fetchall()

        print('=== Последние 20 результатов соревнований ===')
        for row in rows:
            qual_display = row["qualification"] if row["qualification"] else "NULL/Нет"
            print(f'{row["result_added_at"]}: {row["name"]} ({row["sport_type"]}), {row["distance"]}km, время: {row["finish_time"]}, разряд: "{qual_display}", пол: {row["gender"]}')

        print('\n=== Результаты с NULL/пустым разрядом за последние 7 дней ===')
        cursor = await db.execute('''
            SELECT
                c.id,
                c.name,
                c.sport_type,
                cp.distance,
                cp.finish_time,
                cp.qualification,
                cp.result_added_at,
                us.gender,
                cp.user_id
            FROM competition_participants cp
            JOIN competitions c ON c.id = cp.competition_id
            LEFT JOIN user_settings us ON us.user_id = cp.user_id
            WHERE cp.finish_time IS NOT NULL
              AND (cp.qualification IS NULL OR cp.qualification = '' OR cp.qualification = 'Нет разряда')
              AND cp.result_added_at > datetime('now', '-7 days')
            ORDER BY cp.result_added_at DESC
        ''')
        rows = await cursor.fetchall()

        for row in rows:
            print(f'{row["result_added_at"]}: {row["name"]} ({row["sport_type"]}), {row["distance"]}km, время: {row["finish_time"]}, пол: {row["gender"]}, user_id: {row["user_id"]}')

            # Попробуем рассчитать разряд вручную
            from utils.qualifications import get_qualification_async, time_to_seconds
            try:
                time_sec = time_to_seconds(row["finish_time"])
                sport_type = row["sport_type"] or 'бег'
                gender = row["gender"] or 'male'

                kwargs = {}
                if sport_type and 'плав' in sport_type.lower():
                    kwargs['pool_length'] = 50
                elif sport_type and 'велос' in sport_type.lower():
                    kwargs['discipline'] = 'индивидуальная гонка'

                qual = await get_qualification_async(sport_type, row["distance"], time_sec, gender, **kwargs)
                print(f'  → Расчет разряда: {qual}')
            except Exception as e:
                print(f'  → Ошибка расчета: {e}')

asyncio.run(check())
