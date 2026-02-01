"""
Тестовый скрипт для проверки расчета разрядов по плаванию и велоспорту.
"""
import asyncio
from utils.qualifications import get_qualification_async, time_to_seconds


async def test_swimming_qualifications():
    """Тестирование разрядов по плаванию (бассейн 50м)"""
    print("=" * 60)
    print("ТЕСТ: Разряды по плаванию (бассейн 50м)")
    print("=" * 60)

    test_cases = [
        # (дистанция, время, пол, ожидаемый разряд)
        (0.05, "25.00", "male", "КМС или лучше"),  # 50м мужчины
        (0.1, "55.00", "male", "КМС или лучше"),   # 100м мужчины
        (0.05, "28.00", "female", "I или лучше"),  # 50м женщины
        (1.5, "17:00.00", "male", "КМС или лучше"),  # 1500м мужчины
    ]

    for distance, time_str, gender, expected in test_cases:
        time_seconds = time_to_seconds(time_str)
        qualification = await get_qualification_async(
            'плавание',
            distance,
            time_seconds,
            gender,
            pool_length=50
        )
        print(f"\n{distance*1000}м, {gender}, {time_str}")
        print(f"  Результат: {qualification}")
        print(f"  Ожидалось: {expected}")


async def test_cycling_qualifications():
    """Тестирование разрядов по велоспорту (индивидуальная гонка)"""
    print("\n" + "=" * 60)
    print("ТЕСТ: Разряды по велоспорту (индивидуальная гонка)")
    print("=" * 60)

    test_cases = [
        # (дистанция, время, пол, ожидаемый разряд)
        (5.0, "7:00.00", "female", "КМС или лучше"),   # 5км женщины
        (10.0, "15:00.00", "female", "I или лучше"),   # 10км женщины
        (10.0, "12:30.00", "male", "КМС или лучше"),   # 10км мужчины
        (20.0, "26:00.00", "male", "КМС или лучше"),   # 20км мужчины
    ]

    for distance, time_str, gender, expected in test_cases:
        time_seconds = time_to_seconds(time_str)
        qualification = await get_qualification_async(
            'велоспорт',
            distance,
            time_seconds,
            gender,
            discipline='индивидуальная гонка'
        )
        print(f"\n{distance}км, {gender}, {time_str}")
        print(f"  Результат: {qualification}")
        print(f"  Ожидалось: {expected}")


async def test_running_qualifications():
    """Тестирование разрядов по бегу (для проверки, что не сломали)"""
    print("\n" + "=" * 60)
    print("ТЕСТ: Разряды по бегу (контрольная проверка)")
    print("=" * 60)

    test_cases = [
        # (дистанция, время, пол, ожидаемый разряд)
        (5.0, "15:00.00", "male", "КМС или лучше"),   # 5км мужчины
        (10.0, "32:00.00", "male", "КМС или лучше"),  # 10км мужчины
        (21.1, "1:15:00", "male", "КМС или лучше"),   # полумарафон мужчины
    ]

    for distance, time_str, gender, expected in test_cases:
        time_seconds = time_to_seconds(time_str)
        qualification = await get_qualification_async(
            'бег',
            distance,
            time_seconds,
            gender
        )
        print(f"\n{distance}км, {gender}, {time_str}")
        print(f"  Результат: {qualification}")
        print(f"  Ожидалось: {expected}")


async def main():
    """Запуск всех тестов"""
    await test_swimming_qualifications()
    await test_cycling_qualifications()
    await test_running_qualifications()

    print("\n" + "=" * 60)
    print("ТЕСТЫ ЗАВЕРШЕНЫ")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
