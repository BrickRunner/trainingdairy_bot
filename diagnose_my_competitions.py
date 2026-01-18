"""
Диагностика проблемы с "Мои соревнования"
"""
import asyncio
import aiosqlite
import os

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

async def diagnose(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        print(f"\n=== ДИАГНОСТИКА 'МОИ СОРЕВНОВАНИЯ' для user_id={user_id} ===\n")

        # 1. Все записи в competition_participants
        print("1. ВСЕ записи в competition_participants:")
        async with db.execute(
            """
            SELECT id, competition_id, distance, distance_name, proposal_status, status
            FROM competition_participants
            WHERE user_id = ?
            """,
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            print(f"   Всего записей: {len(rows)}")
            for row in rows:
                print(f"   - id={row[0]}, comp_id={row[1]}, dist={row[2]}, dist_name='{row[3]}', proposal='{row[4]}', status='{row[5]}'")

        # 2. Записи которые должны показываться (proposal_status IS NULL or NOT IN pending/rejected)
        print("\n2. Записи которые ДОЛЖНЫ показываться (фильтр get_user_competitions):")
        async with db.execute(
            """
            SELECT cp.id, cp.competition_id, cp.distance, cp.distance_name, c.name, c.date
            FROM competition_participants cp
            JOIN competitions c ON c.id = cp.competition_id
            WHERE cp.user_id = ?
              AND (cp.proposal_status IS NULL OR cp.proposal_status NOT IN ('pending', 'rejected'))
            """,
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            print(f"   Записей после фильтра: {len(rows)}")
            for row in rows:
                print(f"   - id={row[0]}, comp_id={row[1]}, dist={row[2]}, dist_name='{row[3]}', comp_name='{row[4]}', date={row[5]}")

        # 3. Предстоящие соревнования (с фильтром по дате)
        print("\n3. ПРЕДСТОЯЩИЕ соревнования (date >= now):")
        async with db.execute(
            """
            SELECT cp.id, cp.competition_id, cp.distance, cp.distance_name, c.name, c.date, cp.proposal_status
            FROM competition_participants cp
            JOIN competitions c ON c.id = cp.competition_id
            WHERE cp.user_id = ?
              AND c.date >= date('now')
              AND (cp.proposal_status IS NULL OR cp.proposal_status NOT IN ('pending', 'rejected'))
            """,
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            print(f"   Предстоящих соревнований: {len(rows)}")
            for row in rows:
                print(f"   - id={row[0]}, comp_id={row[1]}, dist={row[2]}, dist_name='{row[3]}', comp_name='{row[4]}', date={row[5]}, proposal='{row[6]}'")

        # 4. Текущая дата в SQLite
        async with db.execute("SELECT date('now')") as cursor:
            now_row = await cursor.fetchone()
            print(f"\n4. Текущая дата в SQLite: {now_row[0]}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        user_id = int(sys.argv[1])
    else:
        user_id = int(input("Введите user_id: "))

    asyncio.run(diagnose(user_id))
