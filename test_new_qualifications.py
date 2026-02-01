"""
Тестирование системы расчета разрядов с новыми данными frs24.ru
"""
import asyncio
import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.qualifications import (
    get_qualification_running_from_db,
    get_qualification_swimming_from_db,
    get_qualification_cycling_from_db
)


async def test_running():
    """Тестирование расчета разрядов по бегу"""
    print("\n" + "="*70)
    print("TESTING RUNNING QUALIFICATIONS (frs24.ru)")
    print("="*70)

    test_cases = [
        # (дистанция_км, время_секунды, пол, ожидаемый_разряд)
        (21.0975, 3690, 'male', 'МСМК'),      # 1:01:30 - МСМК
        (21.0975, 3900, 'male', 'МС'),        # 1:05:00 - МС
        (21.0975, 4140, 'male', 'КМС'),       # 1:09:00 - КМС
        (21.0975, 4350, 'male', 'I'),         # 1:12:30 - I разряд
        (21.0975, 4665, 'male', 'II'),        # 1:17:45 - II разряд
        (21.0975, 5040, 'male', 'III'),       # 1:24:00 - III разряд

        (10.0, 1680, 'male', 'МСМК'),         # 28:00 - МСМК
        (10.0, 1760, 'male', 'МС'),           # 29:20 - МС
        (10.0, 1850, 'male', 'КМС'),          # 30:50 - КМС

        (5.0, 805, 'male', 'МСМК'),           # 13:25 - МСМК
        (5.0, 834, 'male', 'МС'),             # 13:54 - МС
        (5.0, 880, 'male', 'КМС'),            # 14:40 - КМС

        # Женщины
        (21.0975, 4260, 'female', 'МСМК'),    # 1:11:00 - МСМК
        (21.0975, 4540, 'female', 'МС'),      # 1:15:40 - МС
        (21.0975, 4920, 'female', 'КМС'),     # 1:22:00 - КМС

        (10.0, 1910, 'female', 'МСМК'),       # 31:50 - МСМК
        (10.0, 2028, 'female', 'МС'),         # 33:48 - МС
        (10.0, 2170, 'female', 'КМС'),        # 36:10 - КМС
    ]

    results = []
    for distance, time, gender, expected_rank in test_cases:
        result = await get_qualification_running_from_db(distance, time, gender)
        status = "[OK]" if result == expected_rank else "[FAIL]"
        gender_str = "M" if gender == 'male' else "F"

        minutes = int(time // 60)
        seconds = int(time % 60)

        print(f"{status} {distance:7.4f}km, {gender_str}, {minutes:02d}:{seconds:02d} -> {result or 'N/A':6s} (expected: {expected_rank})")
        results.append(result == expected_rank)

    success_rate = sum(results) / len(results) * 100
    print(f"\n[SUCCESS] Passed: {sum(results)}/{len(results)} ({success_rate:.1f}%)")
    return success_rate == 100.0


async def test_swimming():
    """Тестирование расчета разрядов по плаванию"""
    print("\n" + "="*70)
    print("TESTING SWIMMING QUALIFICATIONS (frs24.ru)")
    print("="*70)

    test_cases = [
        # (дистанция_км, время_секунды, пол, бассейн, ожидаемый_разряд)
        # Мужчины - бассейн 50м
        (0.05, 21.91, 'male', 50, 'МСМК'),      # 50м вольный стиль МСМК
        (0.05, 22.34, 'male', 50, 'МС'),        # 50м МС
        (0.05, 23.24, 'male', 50, 'КМС'),       # 50м КМС
        (0.05, 24.24, 'male', 50, 'I'),         # 50м I

        (0.1, 48.25, 'male', 50, 'МСМК'),       # 100м МСМК
        (0.1, 50.54, 'male', 50, 'МС'),         # 100м МС
        (0.1, 52.84, 'male', 50, 'КМС'),        # 100м КМС

        (0.2, 106.50, 'male', 50, 'МСМК'),      # 200м МСМК
        (0.2, 112.84, 'male', 50, 'МС'),        # 200м МС
        (0.2, 118.84, 'male', 50, 'КМС'),       # 200м КМС

        # Женщины - бассейн 50м
        (0.05, 24.82, 'female', 50, 'МСМК'),    # 50м МСМК
        (0.05, 25.64, 'female', 50, 'МС'),      # 50м МС
        (0.05, 26.84, 'female', 50, 'КМС'),     # 50м КМС

        (0.1, 53.99, 'female', 50, 'МСМК'),     # 100м МСМК
        (0.1, 56.84, 'female', 50, 'МС'),       # 100м МС
        (0.1, 60.24, 'female', 50, 'КМС'),      # 100м КМС

        # Бассейн 25м
        (0.05, 21.18, 'male', 25, 'МСМК'),      # 50м МСМК бассейн 25м
        (0.05, 21.84, 'male', 25, 'МС'),        # 50м МС бассейн 25м
        (0.05, 22.84, 'male', 25, 'КМС'),       # 50м КМС бассейн 25м
    ]

    results = []
    for distance, time, gender, pool, expected_rank in test_cases:
        result = await get_qualification_swimming_from_db(distance, time, gender, pool)
        status = "[OK]" if result == expected_rank else "[FAIL]"
        gender_str = "M" if gender == 'male' else "F"

        distance_m = int(distance * 1000)

        print(f"{status} {distance_m:4d}m, {gender_str}, {pool}m, {time:6.2f}s -> {result or 'N/A':6s} (expected: {expected_rank})")
        results.append(result == expected_rank)

    success_rate = sum(results) / len(results) * 100
    print(f"\n[SUCCESS] Passed: {sum(results)}/{len(results)} ({success_rate:.1f}%)")
    return success_rate == 100.0


async def test_cycling():
    """Тестирование расчета разрядов по велоспорту"""
    print("\n" + "="*70)
    print("TESTING CYCLING QUALIFICATIONS (frs24.ru)")
    print("="*70)

    test_cases = [
        # (дистанция_км, время_секунды, пол, дисциплина, ожидаемый_разряд)
        # Мужчины - индивидуальная гонка
        (25, 1923, 'male', 'индивидуальная гонка', 'МС'),       # 32:03
        (25, 2042, 'male', 'индивидуальная гонка', 'КМС'),      # 34:02
        (25, 2205, 'male', 'индивидуальная гонка', 'I'),        # 36:45
        (25, 2310, 'male', 'индивидуальная гонка', 'II'),       # 38:30
        (25, 2490, 'male', 'индивидуальная гонка', 'III'),      # 41:30

        (50, 3965, 'male', 'индивидуальная гонка', 'МС'),       # 1:06:05
        (50, 4170, 'male', 'индивидуальная гонка', 'КМС'),      # 1:09:30
        (50, 4539, 'male', 'индивидуальная гонка', 'I'),        # 1:15:39

        # Женщины - индивидуальная гонка
        (25, 2190, 'female', 'индивидуальная гонка', 'МС'),     # 36:30
        (25, 2330, 'female', 'индивидуальная гонка', 'КМС'),    # 38:50
        (25, 2515, 'female', 'индивидуальная гонка', 'I'),      # 41:55

        (10, 844, 'female', 'индивидуальная гонка', 'МС'),      # 14:04
        (10, 897, 'female', 'индивидуальная гонка', 'КМС'),     # 14:57
        (10, 967, 'female', 'индивидуальная гонка', 'I'),       # 16:07

        # Мужчины - парная гонка
        (50, 3775, 'male', 'парная гонка', 'МС'),               # 1:02:55
        (50, 4010, 'male', 'парная гонка', 'КМС'),              # 1:06:50
        (50, 4350, 'male', 'парная гонка', 'I'),                # 1:12:30

        # Женщины - парная гонка
        (50, 4310, 'female', 'парная гонка', 'МС'),             # 1:11:50
        (50, 4580, 'female', 'парная гонка', 'КМС'),            # 1:16:20
        (50, 4935, 'female', 'парная гонка', 'I'),              # 1:22:15
    ]

    results = []
    for distance, time, gender, discipline, expected_rank in test_cases:
        result = await get_qualification_cycling_from_db(distance, time, gender, discipline)
        status = "[OK]" if result == expected_rank else "[FAIL]"
        gender_str = "M" if gender == 'male' else "F"
        disc_short = "ind." if discipline == 'индивидуальная гонка' else "team"

        minutes = int(time // 60)
        seconds = int(time % 60)

        print(f"{status} {distance:3.0f}km, {gender_str}, {disc_short:5s}, {minutes:02d}:{seconds:02d} -> {result or 'N/A':6s} (expected: {expected_rank})")
        results.append(result == expected_rank)

    success_rate = sum(results) / len(results) * 100
    print(f"\n[SUCCESS] Passed: {sum(results)}/{len(results)} ({success_rate:.1f}%)")
    return success_rate == 100.0


async def main():
    """Основная функция тестирования"""
    print("\n" + "="*70)
    print("COMPREHENSIVE QUALIFICATION SYSTEM TESTING")
    print("Data source: frs24.ru")
    print("="*70)

    # Запускаем тесты
    running_ok = await test_running()
    swimming_ok = await test_swimming()
    cycling_ok = await test_cycling()

    # Итоги
    print("\n" + "="*70)
    print("FINAL RESULTS")
    print("="*70)
    print(f"{'Running:':<20s} {'[PASSED]' if running_ok else '[FAILED]'}")
    print(f"{'Swimming:':<20s} {'[PASSED]' if swimming_ok else '[FAILED]'}")
    print(f"{'Cycling:':<20s} {'[PASSED]' if cycling_ok else '[FAILED]'}")

    if running_ok and swimming_ok and cycling_ok:
        print("\n[SUCCESS] ALL TESTS PASSED - QUALIFICATION SYSTEM WORKS CORRECTLY!")
    else:
        print("\n[WARNING] SOME TESTS FAILED - FIXES REQUIRED")

    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
