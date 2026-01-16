"""
Тестовый скрипт для проверки сохранения соревнований в БД
"""

import asyncio
import aiosqlite
import json
from datetime import datetime
from database.queries import add_competition_participant, DB_PATH
from competitions.competitions_queries import get_user_competitions

async def test_competition_save():
    """Тестирование сохранения и извлечения соревнований"""

    # Тестовые данные
    test_user_id = 999999999  # Тестовый пользователь
    test_comp_id = "test_comp_123"

    test_comp_data = {
        'id': test_comp_id,
        'title': 'Тестовое соревнование',
        'begin_date': '2026-12-25T09:00:00',
        'end_date': '2026-12-25T12:00:00',
        'city': 'Москва',
        'place': 'Парк Горького',
        'sport_code': 'run',
        'url': f'https://test.com/comp/{test_comp_id}',
        'distances': [
            {'distance': 5.0, 'name': '5 км'},
            {'distance': 10.0, 'name': '10 км'}
        ]
    }

    print("=" * 60)
    print("ТЕСТ СОХРАНЕНИЯ СОРЕВНОВАНИЯ")
    print("=" * 60)

    # Очистка старых тестовых данных
    print("\n1. Очистка старых тестовых данных...")
    async with aiosqlite.connect(DB_PATH) as db:
        # Удаляем старые тестовые записи
        await db.execute("DELETE FROM competition_participants WHERE user_id = ?", (test_user_id,))
        await db.execute("DELETE FROM competitions WHERE source_url = ?", (test_comp_data['url'],))
        await db.commit()
        print("   ✓ Очищено")

    # Шаг 1: Добавляем участника
    print("\n2. Добавление участника на дистанцию 5 км...")
    try:
        await add_competition_participant(
            user_id=test_user_id,
            competition_id=test_comp_id,
            comp_data=test_comp_data,
            target_time="00:25:00",
            distance=5.0,
            distance_name="5 км"
        )
        print("   ✓ add_competition_participant() выполнена успешно")
    except Exception as e:
        print(f"   ✗ ОШИБКА при вызове add_competition_participant(): {e}")
        return

    # Шаг 2: Проверяем сохранение в таблице competitions
    print("\n3. Проверка таблицы competitions...")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM competitions WHERE source_url = ?",
            (test_comp_data['url'],)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                comp = dict(row)
                print(f"   ✓ Соревнование найдено:")
                print(f"     - ID: {comp['id']}")
                print(f"     - Название: {comp['name']}")
                print(f"     - Дата: {comp['date']}")
                print(f"     - Город: {comp['city']}")
                print(f"     - URL: {comp['source_url']}")
                comp_db_id = comp['id']
            else:
                print("   ✗ ОШИБКА: Соревнование НЕ найдено в БД!")
                return

    # Шаг 3: Проверяем сохранение в таблице competition_participants
    print("\n4. Проверка таблицы competition_participants...")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM competition_participants WHERE user_id = ? AND competition_id = ?",
            (test_user_id, comp_db_id)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                part = dict(row)
                print(f"   ✓ Участник найден:")
                print(f"     - User ID: {part['user_id']}")
                print(f"     - Competition ID: {part['competition_id']}")
                print(f"     - Distance: {part['distance']}")
                print(f"     - Distance Name: {part['distance_name']}")
                print(f"     - Target Time: {part['target_time']}")
                print(f"     - Status: {part['status']}")
            else:
                print("   ✗ ОШИБКА: Участник НЕ найден в БД!")
                return

    # Шаг 4: Проверяем функцию get_user_competitions
    print("\n5. Проверка get_user_competitions('upcoming')...")
    try:
        comps = await get_user_competitions(test_user_id, status_filter='upcoming')
        print(f"   Получено соревнований: {len(comps)}")

        if comps:
            print("   ✓ Соревнования найдены:")
            for idx, comp in enumerate(comps, 1):
                print(f"     [{idx}] {comp.get('name')} - {comp.get('date')} - {comp.get('distance')} км")
        else:
            print("   ✗ ПРОБЛЕМА: get_user_competitions вернула ПУСТОЙ список!")
            print("      Проверим условие фильтрации дат...")

            # Проверим дату соревнования
            async with aiosqlite.connect(DB_PATH) as db:
                async with db.execute("SELECT date('now') as today") as cursor:
                    row = await cursor.fetchone()
                    today = row[0]
                    print(f"      - Сегодняшняя дата в БД: {today}")
                    print(f"      - Дата соревнования: 2026-12-25")
                    print(f"      - Условие: c.date >= date('now') => 2026-12-25 >= {today}")

                    if '2026-12-25' >= today:
                        print("      ✓ Условие выполняется, соревнование должно быть в списке")
                    else:
                        print("      ✗ Условие НЕ выполняется")

    except Exception as e:
        print(f"   ✗ ОШИБКА при вызове get_user_competitions(): {e}")
        import traceback
        traceback.print_exc()

    # Шаг 5: Проверяем все условия в запросе
    print("\n6. Ручная проверка SQL запроса...")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Выполняем точно такой же запрос как в get_user_competitions
        query = """
            SELECT c.*, cp.distance, cp.distance_name, cp.target_time, cp.finish_time,
                   cp.place_overall, cp.place_age_category, cp.age_category,
                   cp.result_comment, cp.result_photo, cp.heart_rate, cp.qualification, cp.status as participant_status,
                   cp.registered_at, cp.result_added_at, cp.proposal_status
            FROM competitions c
            JOIN competition_participants cp ON c.id = cp.competition_id
            WHERE cp.user_id = ? AND c.date >= date('now') AND (cp.proposal_status IS NULL OR cp.proposal_status != 'pending')
            ORDER BY c.date ASC
        """

        async with db.execute(query, (test_user_id,)) as cursor:
            rows = await cursor.fetchall()
            print(f"   Результат прямого SQL запроса: {len(rows)} строк")

            if rows:
                print("   ✓ Данные найдены через прямой SQL!")
                for row in rows:
                    comp = dict(row)
                    print(f"     - {comp.get('name')} | дата: {comp.get('date')} | дистанция: {comp.get('distance')}")
            else:
                print("   ✗ Данные НЕ найдены через прямой SQL")

                # Проверим каждое условие отдельно
                print("\n   Проверка условий по отдельности:")

                # Условие 1: cp.user_id = ?
                async with db.execute(
                    "SELECT COUNT(*) FROM competition_participants WHERE user_id = ?",
                    (test_user_id,)
                ) as c:
                    count = (await c.fetchone())[0]
                    print(f"     - Участников с user_id={test_user_id}: {count}")

                # Условие 2: c.date >= date('now')
                async with db.execute(
                    """SELECT COUNT(*) FROM competitions c
                       JOIN competition_participants cp ON c.id = cp.competition_id
                       WHERE cp.user_id = ? AND c.date >= date('now')""",
                    (test_user_id,)
                ) as c:
                    count = (await c.fetchone())[0]
                    print(f"     - С условием date >= now: {count}")

                # Условие 3: proposal_status
                async with db.execute(
                    """SELECT COUNT(*) FROM competitions c
                       JOIN competition_participants cp ON c.id = cp.competition_id
                       WHERE cp.user_id = ?
                       AND (cp.proposal_status IS NULL OR cp.proposal_status != 'pending')""",
                    (test_user_id,)
                ) as c:
                    count = (await c.fetchone())[0]
                    print(f"     - С условием proposal_status: {count}")

    print("\n" + "=" * 60)
    print("ТЕСТ ЗАВЕРШЕН")
    print("=" * 60)

    # Очистка
    print("\n7. Очистка тестовых данных...")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM competition_participants WHERE user_id = ?", (test_user_id,))
        await db.execute("DELETE FROM competitions WHERE source_url = ?", (test_comp_data['url'],))
        await db.commit()
        print("   ✓ Тестовые данные удалены")

if __name__ == "__main__":
    asyncio.run(test_competition_save())
