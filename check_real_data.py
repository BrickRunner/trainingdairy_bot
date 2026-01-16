"""
Проверка реальных данных в БД
"""

import asyncio
import aiosqlite
from database.queries import DB_PATH
from datetime import datetime

async def check_real_data():
    """Проверка реальных данных в БД"""

    print("=" * 70)
    print("ПРОВЕРКА РЕАЛЬНЫХ ДАННЫХ В БД")
    print("=" * 70)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # 1. Проверяем общее количество соревнований
        print("\n1. Общая статистика:")
        async with db.execute("SELECT COUNT(*) FROM competitions") as cursor:
            count = (await cursor.fetchone())[0]
            print(f"   - Всего соревнований в БД: {count}")

        async with db.execute("SELECT COUNT(*) FROM competition_participants") as cursor:
            count = (await cursor.fetchone())[0]
            print(f"   - Всего регистраций: {count}")

        # 2. Последние добавленные регистрации (топ 10)
        print("\n2. Последние 10 регистраций:")
        query = """
            SELECT cp.id, cp.user_id, c.name, c.date, cp.distance, cp.distance_name,
                   cp.target_time, cp.status, cp.proposal_status, cp.registered_at,
                   c.date >= date('now') as is_upcoming
            FROM competition_participants cp
            JOIN competitions c ON cp.competition_id = c.id
            ORDER BY cp.id DESC
            LIMIT 10
        """
        async with db.execute(query) as cursor:
            rows = await cursor.fetchall()
            if rows:
                for row in rows:
                    r = dict(row)
                    upcoming = "✓ Предстоящее" if r['is_upcoming'] else "✗ Прошедшее"
                    proposal = f" | proposal: {r['proposal_status']}" if r['proposal_status'] else ""
                    print(f"   [{r['id']}] user={r['user_id']} | {r['name'][:40]} | "
                          f"дата={r['date']} | дист={r['distance_name'] or r['distance']} | "
                          f"{upcoming}{proposal}")
            else:
                print("   Нет регистраций")

        # 3. Проверяем регистрации с proposal_status='pending'
        print("\n3. Регистрации со статусом 'pending' (ожидают подтверждения):")
        async with db.execute(
            "SELECT COUNT(*) FROM competition_participants WHERE proposal_status = 'pending'"
        ) as cursor:
            count = (await cursor.fetchone())[0]
            print(f"   - Всего: {count}")

            if count > 0:
                query = """
                    SELECT cp.user_id, c.name, c.date, cp.distance_name
                    FROM competition_participants cp
                    JOIN competitions c ON cp.competition_id = c.id
                    WHERE cp.proposal_status = 'pending'
                    ORDER BY cp.id DESC
                    LIMIT 5
                """
                async with db.execute(query) as c:
                    rows = await c.fetchall()
                    for row in rows:
                        r = dict(row)
                        print(f"     user={r['user_id']} | {r['name'][:40]} | {r['date']} | {r['distance_name']}")

        # 4. Проверяем недавно добавленные соревнования (последние 24 часа)
        print("\n4. Соревнования, добавленные недавно:")
        query = """
            SELECT c.id, c.name, c.date, c.source_url, c.created_at,
                   (SELECT COUNT(*) FROM competition_participants WHERE competition_id = c.id) as participants_count
            FROM competitions c
            ORDER BY c.id DESC
            LIMIT 10
        """
        async with db.execute(query) as cursor:
            rows = await cursor.fetchall()
            if rows:
                for row in rows:
                    r = dict(row)
                    print(f"   [ID:{r['id']}] {r['name'][:50]} | дата={r['date']} | участников={r['participants_count']}")
            else:
                print("   Нет соревнований")

        # 5. Проверяем предстоящие соревнования по пользователям
        print("\n5. Количество предстоящих соревнований по пользователям (топ 5):")
        query = """
            SELECT cp.user_id,
                   COUNT(*) as total_comps,
                   SUM(CASE WHEN c.date >= date('now') THEN 1 ELSE 0 END) as upcoming_comps,
                   SUM(CASE WHEN cp.proposal_status = 'pending' THEN 1 ELSE 0 END) as pending_comps
            FROM competition_participants cp
            JOIN competitions c ON cp.competition_id = c.id
            GROUP BY cp.user_id
            ORDER BY total_comps DESC
            LIMIT 5
        """
        async with db.execute(query) as cursor:
            rows = await cursor.fetchall()
            if rows:
                for row in rows:
                    r = dict(row)
                    print(f"   User {r['user_id']}: "
                          f"всего={r['total_comps']}, "
                          f"предстоящих={r['upcoming_comps']}, "
                          f"pending={r['pending_comps']}")
            else:
                print("   Нет данных")

        # 6. Проверяем последние регистрации БЕЗ proposal_status='pending'
        print("\n6. Последние 5 подтвержденных регистраций:")
        query = """
            SELECT cp.user_id, c.name, c.date, cp.distance_name, cp.target_time,
                   c.date >= date('now') as is_upcoming
            FROM competition_participants cp
            JOIN competitions c ON cp.competition_id = c.id
            WHERE cp.proposal_status IS NULL OR cp.proposal_status != 'pending'
            ORDER BY cp.id DESC
            LIMIT 5
        """
        async with db.execute(query) as cursor:
            rows = await cursor.fetchall()
            if rows:
                for row in rows:
                    r = dict(row)
                    upcoming = "Предстоящее" if r['is_upcoming'] else "Прошедшее"
                    print(f"   user={r['user_id']} | {r['name'][:40]} | "
                          f"дата={r['date']} ({upcoming}) | дист={r['distance_name']} | "
                          f"время={r['target_time']}")
            else:
                print("   Нет регистраций")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    asyncio.run(check_real_data())
