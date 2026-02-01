"""
Тест добавления результата с отладкой
"""
import asyncio
import aiosqlite
from utils.qualifications import get_qualification_async, time_to_seconds
import os

async def test_manual_calculation():
    """Проверяем расчет разряда вручную"""

    # Данные из последнего добавленного результата
    user_id = 1611441720
    competition_id = 22  # Плавание 100м

    async with aiosqlite.connect('database.sqlite') as db:
        db.row_factory = aiosqlite.Row

        # Получаем данные соревнования и результата
        cursor = await db.execute('''
            SELECT
                c.sport_type,
                cp.distance,
                cp.finish_time,
                cp.qualification,
                us.gender
            FROM competition_participants cp
            JOIN competitions c ON c.id = cp.competition_id
            LEFT JOIN user_settings us ON us.user_id = cp.user_id
            WHERE cp.user_id = ? AND cp.competition_id = ?
        ''', (user_id, competition_id))
        row = await cursor.fetchone()

        if not row:
            print("Результат не найден")
            return

        print("=== Данные из БД ===")
        print(f"Sport type: {row['sport_type']}")
        print(f"Distance: {row['distance']}km")
        print(f"Finish time: {row['finish_time']}")
        print(f"Gender: {row['gender']}")
        print(f"Сохраненный разряд: {row['qualification']}")

        # Пересчитываем разряд
        sport_type = row['sport_type'] or 'бег'
        distance = row['distance']
        gender = row['gender'] or 'male'
        finish_time = row['finish_time']

        print("\n=== Пересчет разряда ===")
        print(f"sport_type: '{sport_type}'")
        print(f"distance: {distance}")
        print(f"gender: '{gender}'")

        try:
            time_seconds = time_to_seconds(finish_time)
            print(f"time_seconds: {time_seconds}")

            kwargs = {}
            print(f"Проверка: sport_type='{sport_type}', lower='{sport_type.lower()}', starts with 'пла': {sport_type.lower().startswith('пла')}")
            if sport_type and sport_type.lower().startswith('пла'):
                kwargs['pool_length'] = 50
                print("  -> Добавлен параметр: pool_length=50")
            elif sport_type and (sport_type.lower().startswith('вело') or 'bike' in sport_type.lower()):
                kwargs['discipline'] = 'индивидуальная гонка'
                print("  -> Добавлен параметр: discipline='индивидуальная гонка'")
            else:
                print("  -> Параметры не добавлены (бег или неизвестный спорт)")

            print(f"\nВызов get_qualification_async('{sport_type}', {distance}, {time_seconds}, '{gender}', **{kwargs})")

            qualification = await get_qualification_async(sport_type, distance, time_seconds, gender, **kwargs)

            print(f"\nРезультат расчета: '{qualification}'")

            if qualification != row['qualification']:
                print(f"\nРАСХОЖДЕНИЕ!")
                print(f"  В БД: '{row['qualification']}'")
                print(f"  Пересчет: '{qualification}'")
        except Exception as e:
            print(f"\nОШИБКА при расчете: {e}")
            import traceback
            traceback.print_exc()

asyncio.run(test_manual_calculation())
