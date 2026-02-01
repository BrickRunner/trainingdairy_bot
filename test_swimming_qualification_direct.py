"""
Прямой тест расчета разряда по плаванию
"""
import asyncio
from utils.qualifications import get_qualification_async, time_to_seconds


async def test_swimming_100m():
    """Тест расчета разряда для плавания 100м"""
    print("=" * 60)
    print("ПРЯМОЙ ТЕСТ: Плавание 100м, мужчины")
    print("=" * 60)

    # Параметры
    distance = 0.1  # 100м
    time_str = "55.00"
    gender = "male"
    pool_length = 50

    print(f"\nПараметры:")
    print(f"  Дистанция: {distance} км ({distance*1000} м)")
    print(f"  Время: {time_str}")
    print(f"  Пол: {gender}")
    print(f"  Бассейн: {pool_length}м")

    # Преобразуем время
    time_seconds = time_to_seconds(time_str)
    print(f"  Время в секундах: {time_seconds}")

    # Вызываем функцию расчета разряда
    qualification = await get_qualification_async(
        'плавание',
        distance,
        time_seconds,
        gender,
        pool_length=pool_length
    )

    print(f"\n  Результат: {qualification}")

    if qualification == 'I':
        print("\n[OK] Разряд рассчитан правильно!")
    elif qualification == 'Б/р':
        print("\n[WARN] Возвращен 'Б/р' - время медленнее нормативов")
    elif qualification is None:
        print("\n[FAIL] Возвращен None - нет данных в БД")
    else:
        print(f"\n[INFO] Разряд: {qualification}")

    # Проверим данные в БД
    print("\n" + "=" * 60)
    print("Проверка данных в БД для 100м, мужчины, бассейн 50м:")
    print("=" * 60)

    import aiosqlite
    async with aiosqlite.connect('database.sqlite') as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT rank, time_seconds
            FROM swimming_standards
            WHERE distance = 0.1 AND gender = 'male' AND pool_length = 50
            ORDER BY time_seconds ASC
            """
        ) as cursor:
            rows = await cursor.fetchall()
            if rows:
                print(f"\nНайдено {len(rows)} нормативов:")
                for row in rows:
                    print(f"  {row['rank']}: {row['time_seconds']} сек")
                    if time_seconds <= row['time_seconds']:
                        print(f"    ^ Наш результат {time_seconds} сек соответствует этому разряду")
            else:
                print("\n[FAIL] Данных нет в БД!")


if __name__ == "__main__":
    asyncio.run(test_swimming_100m())
