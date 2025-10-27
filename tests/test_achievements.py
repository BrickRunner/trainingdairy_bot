"""
Комплексное тестирование раздела достижений
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database.rating_queries import (
    get_user_rating,
    get_global_rankings,
    get_weekly_rankings,
    get_monthly_rankings,
    get_seasonal_rankings,
    get_user_rank,
    update_user_rating
)
from database.level_queries import (
    get_user_level,
    get_user_level_with_week,
    get_user_training_stats_for_level,
    calculate_and_update_user_level,
    update_user_level
)
from ratings.rating_calculator import (
    calculate_training_type_points,
    calculate_duration_points,
    calculate_competition_points,
    calculate_total_points,
    get_season_name
)
from ratings.user_levels import (
    get_level_by_avg_trainings,
    get_level_emoji,
    get_level_info,
    get_next_level_info
)


def print_section(title):
    """Красивый вывод заголовка секции"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(test_name, passed, details=""):
    """Красивый вывод результата теста"""
    status = "[OK] PASS" if passed else "[!!] FAIL"
    print(f"{status} | {test_name}")
    if details:
        print(f"      {details}")


async def test_rating_calculator():
    """Тест 1: Проверка расчета рейтинговых очков"""
    print_section("ТЕСТ 1: Расчет рейтинговых очков")

    # Тест баллов за типы тренировок
    tests = [
        ("Беговая", "беговая", 3),
        ("Силовая", "силовая", 2),
        ("Кросс", "кросс", 1),
        ("Велотренировка", "велотренировка", 3),
        ("Плавание", "плавание", 3),
    ]

    for name, training_type, expected in tests:
        points = calculate_training_type_points(training_type)
        passed = points == expected
        print_result(f"{name}: {points} баллов", passed, f"ожидалось {expected}")

    # Тест баллов за время
    duration_tests = [
        (60, 0.5),   # 1 час = 0.5 балла
        (120, 1.0),  # 2 часа = 1 балл
        (90, 0.75),  # 1.5 часа = 0.75 балла
    ]

    for minutes, expected in duration_tests:
        points = calculate_duration_points(minutes)
        passed = points == expected
        print_result(f"{minutes} минут: {points} баллов", passed, f"ожидалось {expected}")

    # Тест баллов за соревнования
    comp_tests = [
        (1, 10),  # 1 место
        (2, 7),   # 2 место
        (3, 5),   # 3 место
        (5, 2),   # участие
    ]

    for place, expected in comp_tests:
        points = calculate_competition_points(place)
        passed = points == expected
        print_result(f"{place} место: {points} баллов", passed, f"ожидалось {expected}")

    # Тест общего расчета
    trainings = [
        {'type': 'беговая', 'duration': 60},     # 3 + 0.5 = 3.5
        {'type': 'силовая', 'duration': 30},      # 2 + 0.25 = 2.25
    ]
    competitions = [{'place': 1}]  # 10

    total = calculate_total_points(trainings, competitions)
    expected_total = 15.75
    passed = total == expected_total
    print_result(f"Общий расчет: {total} баллов", passed, f"ожидалось {expected_total}")


async def test_user_levels():
    """Тест 2: Проверка системы уровней"""
    print_section("ТЕСТ 2: Система уровней")

    level_tests = [
        (0, "новичок", "🌱"),
        (1, "новичок", "🌱"),
        (2, "новичок", "🌱"),
        (3, "любитель", "💪"),
        (4, "любитель", "💪"),
        (5, "профи", "🏃"),
        (6, "элитный", "⭐"),
        (7, "элитный", "⭐"),
    ]

    for trainings, expected_level, expected_emoji in level_tests:
        level = get_level_by_avg_trainings(trainings)
        emoji = get_level_emoji(level)
        passed = level == expected_level and emoji == expected_emoji
        print_result(f"{trainings} тренировок/неделю -> {level}",
                    passed, f"ожидалось {expected_level}")

    # Тест информации о следующем уровне
    next_tests = [
        ("новичок", 2, "любитель", 1),
        ("любитель", 4, "профи", 1),
        ("профи", 5, "элитный", 1),
        ("элитный", 7, None, 0),
    ]

    for current, trainings, expected_next, expected_needed in next_tests:
        next_info = get_next_level_info(current, trainings)
        if expected_next:
            passed = (next_info['has_next'] and
                     next_info['next_level'] == expected_next and
                     next_info['trainings_needed'] == expected_needed)
            print_result(f"{current} -> {next_info.get('next_level', 'макс')}",
                        passed, f"нужно еще {next_info['trainings_needed']}")
        else:
            passed = not next_info['has_next']
            print_result(f"{current} -> максимальный уровень", passed)


async def test_database_operations():
    """Тест 3: Операции с базой данных"""
    print_section("ТЕСТ 3: Операции с базой данных")

    # Создаем тестовые данные
    test_user_id = 999999999

    # Тест 3.1: Обновление рейтинга
    await update_user_rating(test_user_id, 100.5, 20.0, 50.0, 75.0)
    rating = await get_user_rating(test_user_id)

    passed = (rating and rating['points'] == 100.5 and
             rating['week_points'] == 20.0 and
             rating['month_points'] == 50.0 and
             rating['season_points'] == 75.0)
    print_result("Обновление рейтинга", passed,
                f"очки: {rating['points'] if rating else 'None'}")

    # Тест 3.2: Получение места в рейтинге
    rank = await get_user_rank(test_user_id, 'global')
    print_result("Получение места в рейтинге", rank is not None,
                f"место: {rank if rank else 'не найдено'}")

    # Тест 3.3: Обновление уровня
    await update_user_level(test_user_id, "профи")
    level = await get_user_level(test_user_id)
    passed = level == "профи"
    print_result("Обновление уровня", passed, f"уровень: {level}")

    # Тест 3.4: Получение уровня с неделей
    level, week = await get_user_level_with_week(test_user_id)
    passed = level == "профи" and week is not None
    print_result("Получение уровня с неделей", passed,
                f"уровень: {level}, неделя: {week}")


async def test_rankings():
    """Тест 4: Проверка рейтингов"""
    print_section("ТЕСТ 4: Рейтинги")

    # Тест глобального рейтинга
    global_rank = await get_global_rankings(limit=10)
    passed = isinstance(global_rank, list)
    print_result("Глобальный рейтинг", passed,
                f"пользователей: {len(global_rank)}")

    # Тест недельного рейтинга
    weekly_rank = await get_weekly_rankings(limit=10)
    passed = isinstance(weekly_rank, list)
    print_result("Недельный рейтинг", passed,
                f"пользователей: {len(weekly_rank)}")

    # Тест месячного рейтинга
    monthly_rank = await get_monthly_rankings(limit=10)
    passed = isinstance(monthly_rank, list)
    print_result("Месячный рейтинг", passed,
                f"пользователей: {len(monthly_rank)}")

    # Тест сезонного рейтинга
    seasonal_rank = await get_seasonal_rankings(limit=10)
    passed = isinstance(seasonal_rank, list)
    season = get_season_name()
    print_result(f"Сезонный рейтинг ({season})", passed,
                f"пользователей: {len(seasonal_rank)}")


async def test_level_calculation():
    """Тест 5: Расчет уровней пользователей"""
    print_section("ТЕСТ 5: Расчет уровней")

    # Находим реального пользователя для теста
    import aiosqlite
    DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id FROM users LIMIT 1") as cursor:
            row = await cursor.fetchone()
            if row:
                user_id = row[0]

                # Получаем статистику
                stats = await get_user_training_stats_for_level(user_id)
                print_result("Получение статистики тренировок", True,
                           f"тренировок на неделе: {stats['current_week_trainings']}, "
                           f"всего: {stats['total_trainings']}")

                # Пересчитываем уровень
                result = await calculate_and_update_user_level(user_id)
                print_result("Пересчет уровня", True,
                           f"{result['old_level']} -> {result['new_level']} "
                           f"({'изменен' if result['level_changed'] else 'не изменен'})")
            else:
                print_result("Пользователи в БД", False, "нет пользователей")


async def test_edge_cases():
    """Тест 6: Граничные случаи"""
    print_section("ТЕСТ 6: Граничные случаи")

    # Тест пользователя без рейтинга
    fake_user = 888888888
    rating = await get_user_rating(fake_user)
    passed = rating is None
    print_result("Пользователь без рейтинга", passed,
                "корректно возвращает None")

    # Тест пользователя без уровня
    level = await get_user_level(fake_user)
    passed = level is None
    print_result("Пользователь без уровня", passed,
                "корректно возвращает None")

    # Тест пустых тренировок
    trainings = []
    competitions = []
    points = calculate_total_points(trainings, competitions)
    passed = points == 0.0
    print_result("Пустые данные", passed, f"очки: {points}")


async def run_all_tests():
    """Запуск всех тестов"""
    print("\n")
    print("+" + "=" * 58 + "+")
    print("|" + " " * 10 + "ТЕСТИРОВАНИЕ РАЗДЕЛА ДОСТИЖЕНИЙ" + " " * 16 + "|")
    print("+" + "=" * 58 + "+")

    try:
        await test_rating_calculator()
        await test_user_levels()
        await test_database_operations()
        await test_rankings()
        await test_level_calculation()
        await test_edge_cases()

        print_section("РЕЗУЛЬТАТЫ")
        print("[OK] Все тесты завершены!")
        print("\nПроверьте результаты выше для деталей.")

    except Exception as e:
        print(f"\n[!!] КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(run_all_tests())
