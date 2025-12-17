"""
Полная проверка сценария: добавление -> отображение
"""

import asyncio
import sys
import io

# Установка правильной кодировки для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

async def test_full_flow():
    """Тестируем полный поток добавления и отображения"""
    from database.queries import add_competition_participant
    from competitions.competitions_queries import get_user_competitions
    import aiosqlite
    from database.queries import DB_PATH

    print("="*60)
    print("🧪 ТЕСТ ПОЛНОГО СЦЕНАРИЯ")
    print("="*60)

    # Используем реального пользователя (замените на ваш telegram ID)
    test_user_id = 123456789  # ЗАМЕНИТЕ НА СВОЙ ID

    test_competition = {
        'id': 'real_test_123',
        'title': '🧪 ТЕСТОВОЕ СОРЕВНОВАНИЕ',
        'begin_date': '2025-12-25T09:00:00',  # Будущая дата
        'city': 'Москва',
        'place': 'Лужники',
        'url': 'https://test.timerman.org/event/real_test_123',
        'sport_code': 'run',
        'organizer': 'Test Org',
        'service': 'Timerman',
        'distances': [
            {'name': '10 км', 'distance': 10.0}
        ]
    }

    print(f"\n📝 Шаг 1: Добавление соревнования")
    print(f"   User ID: {test_user_id}")
    print(f"   Соревнование: {test_competition['title']}")
    print(f"   Дата: {test_competition['begin_date']}")

    try:
        await add_competition_participant(
            user_id=test_user_id,
            competition_id=test_competition['id'],
            comp_data=test_competition,
            target_time='1:00:00',
            distance=10.0,
            distance_name='10 км'
        )
        print("   ✅ Успешно добавлено")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return

    # Имитируем задержку как в коде
    print("\n⏱️ Шаг 2: Задержка 0.2 секунды (как в коде)")
    await asyncio.sleep(0.2)

    print("\n📖 Шаг 3: Получение соревнований пользователя")
    try:
        competitions = await get_user_competitions(test_user_id, status_filter='upcoming')

        print(f"   Найдено соревнований: {len(competitions)}")

        if competitions:
            print("\n   📋 Список соревнований:")
            for i, comp in enumerate(competitions, 1):
                print(f"\n   {i}. {comp.get('name')}")
                print(f"      ID в БД: {comp.get('id')}")
                print(f"      Дата: {comp.get('date')}")
                print(f"      Дистанция: {comp.get('distance')} км")
                print(f"      Целевое время: {comp.get('target_time')}")

                # Проверяем, есть ли наше тестовое
                if '🧪' in comp.get('name', ''):
                    print(f"      ✅ ТЕСТОВОЕ НАЙДЕНО!")
        else:
            print("   ⚠️ Список пуст!")

    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

    # Детальная проверка БД
    print("\n🔍 Шаг 4: Проверка базы данных напрямую")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Проверяем competitions
        print("\n   📊 Таблица competitions:")
        cursor = await db.execute(
            "SELECT id, name, date, status FROM competitions WHERE name LIKE '%ТЕСТОВОЕ%'"
        )
        rows = await cursor.fetchall()
        for row in rows:
            print(f"      ID: {row['id']}, Name: {row['name']}, Date: {row['date']}, Status: {row['status']}")

        # Проверяем competition_participants
        print("\n   📊 Таблица competition_participants:")
        cursor = await db.execute(
            "SELECT cp.*, c.name, c.date FROM competition_participants cp "
            "JOIN competitions c ON cp.competition_id = c.id "
            "WHERE cp.user_id = ?",
            (test_user_id,)
        )
        rows = await cursor.fetchall()
        print(f"      Всего записей: {len(rows)}")
        for row in rows:
            print(f"      - {row['name']}, Date: {row['date']}, Distance: {row['distance']}, Target: {row['target_time']}")

        # Проверяем запрос который использует get_user_competitions
        print("\n   📊 SQL запрос из get_user_competitions:")
        cursor = await db.execute(
            """
            SELECT c.*, cp.distance, cp.distance_name, cp.target_time
            FROM competitions c
            JOIN competition_participants cp ON c.id = cp.competition_id
            WHERE cp.user_id = ? AND c.date >= date('now')
            ORDER BY c.date ASC
            """,
            (test_user_id,)
        )
        rows = await cursor.fetchall()
        print(f"      Результатов: {len(rows)}")
        for row in rows:
            row_dict = dict(row)
            print(f"      - {row_dict.get('name')}")
            print(f"        Date в БД: {row_dict.get('date')}")
            print(f"        date('now'): ", end="")
            cursor2 = await db.execute("SELECT date('now')")
            now = await cursor2.fetchone()
            print(now[0])

    print("\n" + "="*60)
    print("\n💡 ВАЖНО: Проверьте дату соревнования!")
    print("   Если date < date('now'), соревнование не попадет в 'upcoming'")

    # Не удаляем, чтобы проверить в реальном боте
    print("\n⚠️  ТЕСТОВЫЕ ДАННЫЕ НЕ УДАЛЕНЫ - проверьте в боте!")
    print("   После проверки удалите вручную или запустите скрипт снова")

if __name__ == "__main__":
    asyncio.run(test_full_flow())
