"""
Проверка данных по велоспорту для мужчин на 5км.
"""
import asyncio
import aiosqlite


async def check_cycling_5km_male():
    """Проверка наличия данных для мужчин на 5км"""
    try:
        async with aiosqlite.connect('database.sqlite') as db:
            db.row_factory = aiosqlite.Row

            # Проверяем данные для мужчин 5км индивидуальная гонка
            print("Данные для мужчин, 5км, индивидуальная гонка:")
            async with db.execute(
                """
                SELECT distance, gender, discipline, rank, time_seconds
                FROM cycling_standards
                WHERE gender = 'male' AND discipline = 'индивидуальная гонка' AND distance = 5.0
                ORDER BY time_seconds ASC
                """
            ) as cursor:
                rows = await cursor.fetchall()
                if rows:
                    print(f"Найдено {len(rows)} записей:")
                    for row in rows:
                        minutes = int(row['time_seconds'] // 60)
                        seconds = row['time_seconds'] % 60
                        print(f"  {row['rank']}: {minutes}:{seconds:05.2f} ({row['time_seconds']} сек)")
                else:
                    print("  НЕТ ДАННЫХ!")

            # Проверяем все дистанции для мужчин
            print("\nВсе доступные дистанции для мужчин (индивидуальная гонка):")
            async with db.execute(
                """
                SELECT DISTINCT distance
                FROM cycling_standards
                WHERE gender = 'male' AND discipline = 'индивидуальная гонка'
                ORDER BY distance
                """
            ) as cursor:
                rows = await cursor.fetchall()
                for row in rows:
                    print(f"  - {row[0]} км")

    except Exception as e:
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(check_cycling_5km_male())
