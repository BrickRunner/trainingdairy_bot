"""
Добавление тестовых соревнований на вчерашний день для проверки ввода результатов
"""
import asyncio
import aiosqlite
from datetime import datetime, timedelta

DB_PATH = 'database.sqlite'


async def add_test_competitions():
    """Добавить тестовые соревнования на вчерашний день"""

    # Вчерашняя дата
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    print(f"Добавление тестовых соревнований на дату: {yesterday}")
    print("="*70)

    # Тестовые соревнования
    test_competitions = [
        {
            'name': '🏃 Московский забег "Осенний марафон"',
            'date': yesterday,
            'city': 'Москва',
            'country': 'Россия',
            'distances': '[5.0, 10.0, 21.1, 42.195]',
            'type': 'марафон',
            'description': 'Тестовое соревнование для проверки ввода результатов',
            'status': 'finished',
            'is_official': 1
        },
        {
            'name': '🏃 Забег в парке Сокольники',
            'date': yesterday,
            'city': 'Москва',
            'country': 'Россия',
            'distances': '[5.0, 10.0]',
            'type': 'забег',
            'description': 'Парковый забег для всех желающих',
            'status': 'finished',
            'is_official': 1
        },
        {
            'name': '🏃 Городской полумарафон',
            'date': yesterday,
            'city': 'Санкт-Петербург',
            'country': 'Россия',
            'distances': '[10.0, 21.1]',
            'type': 'полумарафон',
            'description': 'Тестовый полумарафон в Петербурге',
            'status': 'finished',
            'is_official': 1
        }
    ]

    async with aiosqlite.connect(DB_PATH) as db:
        competition_ids = []

        for comp_data in test_competitions:
            cursor = await db.execute(
                """
                INSERT INTO competitions
                (name, date, city, country, distances, type, description, status, is_official)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    comp_data['name'],
                    comp_data['date'],
                    comp_data['city'],
                    comp_data['country'],
                    comp_data['distances'],
                    comp_data['type'],
                    comp_data['description'],
                    comp_data['status'],
                    comp_data['is_official']
                )
            )
            comp_id = cursor.lastrowid
            competition_ids.append(comp_id)

            print(f"[OK] Added competition ID {comp_id}")
            print(f"     Date: {comp_data['date']}")
            print(f"     City: {comp_data['city']}")
            print(f"     Distances: {comp_data['distances']}")
            print()

        await db.commit()

    print("="*70)
    print("[SUCCESS] All test competitions added!")
    print()
    print("[NEXT STEP]:")
    print("   1. Open bot in Telegram")
    print("   2. Go to 'Competitions' -> 'Find competitions'")
    print("   3. Register for these competitions")
    print("   4. They will appear in 'Finished competitions'")
    print("   5. You can add results there")
    print()
    print(f"[IDs] Added competitions: {competition_ids}")

    return competition_ids


async def register_user_for_test_competitions(user_id, competition_ids):
    """
    Автоматически зарегистрировать пользователя на тестовые соревнования
    """
    print()
    print("="*70)
    print(f"Регистрация пользователя {user_id} на тестовые соревнования...")
    print("="*70)

    async with aiosqlite.connect(DB_PATH) as db:
        registrations = [
            (competition_ids[0], 10.0, '00:45:00'),  # Осенний марафон - 10 км
            (competition_ids[0], 5.0, '00:22:00'),   # Осенний марафон - 5 км
            (competition_ids[1], 5.0, '00:20:00'),   # Сокольники - 5 км
            (competition_ids[2], 21.1, '1:45:00'),   # Полумарафон - 21.1 км
        ]

        for comp_id, distance, target_time in registrations:
            cursor = await db.execute(
                """
                INSERT INTO competition_participants
                (user_id, competition_id, distance, target_time, status)
                VALUES (?, ?, ?, ?, 'registered')
                """,
                (user_id, comp_id, distance, target_time)
            )

            # Получаем название соревнования
            cursor = await db.execute(
                "SELECT name FROM competitions WHERE id = ?",
                (comp_id,)
            )
            row = await cursor.fetchone()
            comp_name = row[0] if row else 'Неизвестно'

            print(f"[OK] Registered for competition ID {comp_id}")
            print(f"     Distance: {distance} km")
            print(f"     Target time: {target_time}")
            print()

        await db.commit()

    print("="*70)
    print("[SUCCESS] Registration completed!")
    print()
    print("[IN BOT NOW]:")
    print("   - Go to 'Competitions' -> 'Finished competitions'")
    print("   - Select any competition")
    print("   - Click 'Add result'")
    print("   - Enter finish time, place and other info")


async def main():
    """Главная функция"""
    print("="*70)
    print("СОЗДАНИЕ ТЕСТОВЫХ СОРЕВНОВАНИЙ ДЛЯ ПРОВЕРКИ ВВОДА РЕЗУЛЬТАТОВ")
    print("="*70)
    print()

    # Добавляем соревнования
    competition_ids = await add_test_competitions()

    # Спрашиваем про автоматическую регистрацию
    print()
    print("[?] Auto-register test user?")
    print("   User ID: 1611441720")
    response = input("   Enter 'yes' to register (Enter to skip): ").strip().lower()

    if response in ['да', 'yes', 'y', 'д']:
        await register_user_for_test_competitions(1611441720, competition_ids)
    else:
        print()
        print("[SKIPPED] Register manually via bot.")

    print()
    print("="*70)
    print("[DONE] Script completed!")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
