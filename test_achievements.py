"""
Тестовый скрипт для проверки системы достижений
"""

import asyncio
import sqlite3
from ratings.achievements_checker import get_user_stats, check_achievement_condition, award_achievement
from ratings.achievements_data import ACHIEVEMENTS


async def test_achievements():
    """Проверить систему достижений"""

    # Получаем список пользователей
    conn = sqlite3.connect('database.sqlite')
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users LIMIT 5")
    users = cursor.fetchall()
    conn.close()

    print(f"Найдено пользователей: {len(users)}")
    print()

    if not users:
        print("❌ Нет пользователей в БД")
        return

    # Тестируем первого пользователя
    user_id, username = users[0]
    print(f"Тестируем пользователя: {username} (ID: {user_id})")
    print("=" * 60)

    # Получаем статистику
    print("\nStatistics:")
    stats = await get_user_stats(user_id)

    # Показываем основные показатели
    important_stats = [
        'total_competitions',
        'total_trainings',
        'has_10k',
        'has_half_marathon',
        'has_marathon',
        'different_cities',
        'podium_count',
        'total_results'
    ]

    for key in important_stats:
        if key in stats:
            print(f"  {key}: {stats[key]}")

    # Проверяем, какие достижения могут быть получены
    print("\nAvailable achievements:")
    available_count = 0

    for ach_id, ach_data in ACHIEVEMENTS.items():
        try:
            if await check_achievement_condition(user_id, ach_id, stats):
                available_count += 1
                print(f"  + {ach_data['name']} ({ach_data['points']} points)")

                # Присваиваем достижение
                await award_achievement(user_id, ach_id)
        except Exception as e:
            print(f"  - Error checking {ach_id}: {e}")

    print(f"\nTotal available: {available_count}/55")

    # Проверяем, что достижения сохранены
    conn = sqlite3.connect('database.sqlite')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM achievements WHERE user_id = ?", (user_id,))
    saved_count = cursor.fetchone()[0]
    conn.close()

    print(f"Saved in DB: {saved_count}")

    if saved_count != available_count:
        print("WARNING: Count mismatch!")
    else:
        print("SUCCESS: All achievements saved!")


if __name__ == "__main__":
    asyncio.run(test_achievements())
