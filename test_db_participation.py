"""
Тест сохранения и загрузки участия в соревнованиях
"""

import asyncio
import sys
import io

# Установка правильной кодировки для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

async def test_add_and_retrieve():
    """Тест добавления соревнования и его получения"""
    from database.queries import add_competition_participant
    from competitions.competitions_queries import get_user_competitions
    from datetime import datetime

    print("="*60)
    print("🧪 ТЕСТ СОХРАНЕНИЯ И ЗАГРУЗКИ УЧАСТИЯ")
    print("="*60)

    # Тестовые данные
    test_user_id = 999999999  # Тестовый пользователь
    test_competition = {
        'id': 'test_comp_123',
        'title': 'Тестовое соревнование',
        'begin_date': '2026-06-15T09:00:00',
        'city': 'Тест-город',
        'place': 'Тест-место',
        'url': 'https://test.com/comp/test_comp_123',
        'sport_code': 'run',
        'organizer': 'Тест-организатор',
        'distances': [
            {'name': '5 км', 'distance': 5.0},
            {'name': '10 км', 'distance': 10.0}
        ]
    }

    print("\n📝 Добавление участия в соревновании...")
    print(f"   Пользователь: {test_user_id}")
    print(f"   Соревнование: {test_competition['title']}")
    print(f"   Дистанция: 10 км")
    print(f"   Целевое время: 1:30:00")

    try:
        await add_competition_participant(
            user_id=test_user_id,
            competition_id=test_competition['id'],
            comp_data=test_competition,
            target_time='1:30:00',
            distance=10.0,
            distance_name='10 км'
        )
        print("✅ Участие успешно добавлено")

    except Exception as e:
        print(f"❌ Ошибка при добавлении: {e}")
        import traceback
        traceback.print_exc()
        return

    # Небольшая задержка для имитации реальной работы
    await asyncio.sleep(0.1)

    print("\n📖 Получение соревнований пользователя...")
    try:
        competitions = await get_user_competitions(test_user_id, status_filter='upcoming')

        print(f"✅ Найдено соревнований: {len(competitions)}")

        if competitions:
            print("\n📋 Детали соревнований:")
            for i, comp in enumerate(competitions, 1):
                print(f"\n{i}. {comp.get('name')}")
                print(f"   ID: {comp.get('id')}")
                print(f"   Дата: {comp.get('date')}")
                print(f"   Дистанция: {comp.get('distance')} км")
                print(f"   Название дистанции: {comp.get('distance_name')}")
                print(f"   Целевое время: {comp.get('target_time')}")
                print(f"   Город: {comp.get('city')}")
        else:
            print("⚠️ Соревнования не найдены!")
            print("\n🔍 Проверка базы данных напрямую...")

            import aiosqlite
            from database.queries import DB_PATH

            async with aiosqlite.connect(DB_PATH) as db:
                # Проверяем таблицу competitions
                cursor = await db.execute(
                    "SELECT * FROM competitions WHERE source_url = ?",
                    (test_competition['url'],)
                )
                comp_row = await cursor.fetchone()
                if comp_row:
                    print("✅ Соревнование найдено в таблице competitions")
                    print(f"   ID в БД: {comp_row[0]}")
                else:
                    print("❌ Соревнование НЕ найдено в таблице competitions")

                # Проверяем таблицу competition_participants
                cursor = await db.execute(
                    "SELECT * FROM competition_participants WHERE user_id = ?",
                    (test_user_id,)
                )
                part_rows = await cursor.fetchall()
                if part_rows:
                    print(f"✅ Найдено {len(part_rows)} записей в competition_participants")
                    for row in part_rows:
                        print(f"   ID: {row[0]}, competition_id: {row[1]}, user_id: {row[2]}, distance: {row[5]}")
                else:
                    print("❌ Записи НЕ найдены в competition_participants")

    except Exception as e:
        print(f"❌ Ошибка при получении: {e}")
        import traceback
        traceback.print_exc()

    # Очистка тестовых данных
    print("\n🧹 Очистка тестовых данных...")
    try:
        import aiosqlite
        from database.queries import DB_PATH

        async with aiosqlite.connect(DB_PATH) as db:
            # Удаляем участие
            await db.execute(
                "DELETE FROM competition_participants WHERE user_id = ?",
                (test_user_id,)
            )

            # Удаляем соревнование
            await db.execute(
                "DELETE FROM competitions WHERE source_url = ?",
                (test_competition['url'],)
            )

            await db.commit()
        print("✅ Тестовые данные удалены")

    except Exception as e:
        print(f"⚠️ Ошибка при очистке: {e}")

    print("\n" + "="*60)


if __name__ == "__main__":
    asyncio.run(test_add_and_retrieve())
