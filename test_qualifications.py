"""
Тестовый скрипт для проверки работы модуля определения разрядов
"""

import sys
import io

# Устанавливаем UTF-8 кодировку для вывода на Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from utils.qualifications import get_qualification, time_to_seconds, format_qualification


def test_running():
    """Тест для бега"""
    print("=" * 60)
    print("ТЕСТ: Легкая атлетика (бег)")
    print("=" * 60)

    # Тестовые случаи для бега (мужчины)
    test_cases = [
        # (дистанция_км, время, пол, ожидаемый_разряд)
        (5.0, "14:30", "male", "МСМК"),
        (5.0, "16:00", "male", "КМС"),
        (5.0, "18:00", "male", "I"),
        (5.0, "22:00", "male", None),
        (21.1, "1:02:00", "male", "МСМК"),
        (21.1, "1:10:00", "male", "КМС"),
        (42.2, "2:10:00", "male", "МСМК"),
        (42.2, "2:20:00", "male", "МС"),
        (42.2, "2:30:00", "male", "КМС"),

        # Женщины
        (5.0, "18:00", "female", "МС"),
        (5.0, "20:00", "female", "КМС"),
        (21.1, "1:12:00", "female", "МСМК"),
        (42.2, "2:35:00", "female", "МС"),
    ]

    for distance, time_str, gender, expected in test_cases:
        time_sec = time_to_seconds(time_str)
        result = get_qualification("бег", distance, time_sec, gender)
        status = "✓" if result == expected else "✗"
        gender_str = "М" if gender == "male" else "Ж"
        print(f"{status} {distance} км, {time_str} ({gender_str}): {result or 'нет разряда'} (ожидалось: {expected or 'нет разряда'})")


def test_swimming():
    """Тест для плавания"""
    print("\n" + "=" * 60)
    print("ТЕСТ: Плавание (вольный стиль, бассейн 50м)")
    print("=" * 60)

    test_cases = [
        # (дистанция_км, время, пол, ожидаемый_разряд)
        (0.05, "22.00", "male", "МСМК"),
        (0.05, "23.50", "male", "МС"),
        (0.1, "50.00", "male", "МС"),
        (0.1, "55.00", "male", "КМС"),
        (0.2, "1:50.00", "male", "МС"),
        (1.5, "15:00.00", "male", "МСМК"),

        # Женщины
        (0.05, "25.00", "female", "МСМК"),
        (0.05, "27.00", "female", "КМС"),
        (0.1, "56.00", "female", "МС"),
    ]

    for distance, time_str, gender, expected in test_cases:
        time_sec = time_to_seconds(time_str)
        result = get_qualification("плавание", distance, time_sec, gender, pool_length=50)
        status = "✓" if result == expected else "✗"
        gender_str = "М" if gender == "male" else "Ж"
        dist_m = int(distance * 1000)
        print(f"{status} {dist_m}м, {time_str} ({gender_str}): {result or 'нет разряда'} (ожидалось: {expected or 'нет разряда'})")


def test_time_conversion():
    """Тест конвертации времени"""
    print("\n" + "=" * 60)
    print("ТЕСТ: Конвертация времени в секунды")
    print("=" * 60)

    test_cases = [
        ("23.95", 23.95),
        ("1:05.34", 65.34),
        ("15:30", 930.0),
        ("1:15:30", 4530.0),
        ("2:12:00", 7920.0),
    ]

    for time_str, expected in test_cases:
        result = time_to_seconds(time_str)
        status = "✓" if abs(result - expected) < 0.01 else "✗"
        print(f"{status} {time_str} = {result} сек (ожидалось: {expected})")


def test_format():
    """Тест форматирования разрядов"""
    print("\n" + "=" * 60)
    print("ТЕСТ: Форматирование разрядов")
    print("=" * 60)

    ranks = ["МСМК", "МС", "КМС", "I", "II", "III"]
    for rank in ranks:
        formatted = format_qualification(rank)
        print(f"{rank} -> {formatted}")


if __name__ == "__main__":
    test_time_conversion()
    test_running()
    test_swimming()
    test_format()

    print("\n" + "=" * 60)
    print("Тестирование завершено")
    print("=" * 60)
