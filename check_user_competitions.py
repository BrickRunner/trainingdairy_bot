"""
Проверка соревнований пользователя в БД
"""

import asyncio
import sys
import io
import aiosqlite
from database.queries import DB_PATH

# Установка правильной кодировки для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

async def check_competitions():
    """Проверить все соревнования пользователя"""

    # ВАЖНО: Укажите ваш реальный Telegram ID
    user_id = int(input("Введите ваш Telegram User ID: "))

    print("\n" + "="*60)
    print("🔍 ПРОВЕРКА СОРЕВНОВАНИЙ В БАЗЕ ДАННЫХ")
    print("="*60)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # 1. Все соревнования пользователя (без фильтра по дате)
        print(f"\n📊 ВСЕ соревнования пользователя {user_id}:")
        cursor = await db.execute(
            """
            SELECT c.id, c.name, c.date, c.status, cp.distance, cp.distance_name, cp.target_time
            FROM competitions c
            JOIN competition_participants cp ON c.id = cp.competition_id
            WHERE cp.user_id = ?
            ORDER BY c.date DESC
            """,
            (user_id,)
        )
        all_rows = await cursor.fetchall()

        if not all_rows:
            print("   ❌ Не найдено ни одного соревнования!")
            return

        for i, row in enumerate(all_rows, 1):
            print(f"\n   {i}. {row['name']}")
            print(f"      ID: {row['id']}")
            print(f"      Дата: {row['date']}")
            print(f"      Статус: {row['status']}")
            print(f"      Дистанция: {row['distance']} км ({row['distance_name']})")
            print(f"      Целевое время: {row['target_time']}")

        # 2. Только предстоящие (upcoming)
        print(f"\n" + "="*60)
        print("📅 ПРЕДСТОЯЩИЕ соревнования (date >= today):")

        # Получаем текущую дату
        cursor = await db.execute("SELECT date('now') as today")
        today_row = await cursor.fetchone()
        today = today_row['today']
        print(f"   Сегодня: {today}")

        cursor = await db.execute(
            """
            SELECT c.id, c.name, c.date, c.status, cp.distance, cp.target_time
            FROM competitions c
            JOIN competition_participants cp ON c.id = cp.competition_id
            WHERE cp.user_id = ? AND c.date >= date('now')
            ORDER BY c.date ASC
            """,
            (user_id,)
        )
        upcoming_rows = await cursor.fetchall()

        if not upcoming_rows:
            print(f"\n   ⚠️ Нет предстоящих соревнований!")
            print(f"   Возможно, все даты < {today}")
        else:
            print(f"\n   Найдено: {len(upcoming_rows)} предстоящих")
            for i, row in enumerate(upcoming_rows, 1):
                print(f"\n   {i}. {row['name']}")
                print(f"      Дата: {row['date']}")
                print(f"      Целевое время: {row['target_time']}")

        # 3. Проверка последнего добавленного
        print(f"\n" + "="*60)
        print("🆕 ПОСЛЕДНИЕ 5 добавленных:")
        cursor = await db.execute(
            """
            SELECT c.id, c.name, c.date, cp.registered_at, cp.target_time, cp.distance_name
            FROM competitions c
            JOIN competition_participants cp ON c.id = cp.competition_id
            WHERE cp.user_id = ?
            ORDER BY cp.registered_at DESC
            LIMIT 5
            """,
            (user_id,)
        )
        recent_rows = await cursor.fetchall()

        for i, row in enumerate(recent_rows, 1):
            print(f"\n   {i}. {row['name']}")
            print(f"      Дата соревнования: {row['date']}")
            print(f"      Дата регистрации: {row['registered_at']}")
            print(f"      Дистанция: {row['distance_name']}")
            print(f"      Целевое время: {row['target_time']}")

            # Проверяем, попадет ли в upcoming
            is_upcoming = row['date'] >= today if row['date'] else False
            if is_upcoming:
                print(f"      ✅ Попадет в 'Мои соревнования' (upcoming)")
            else:
                print(f"      ❌ НЕ попадет в 'Мои соревнования' (дата в прошлом)")

    print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(check_competitions())
