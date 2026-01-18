"""
Скрипт для диагностики проблемы с "Мои соревнования"
"""
import asyncio
import aiosqlite
import os
from datetime import date

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

async def debug_user_competitions(user_id: int):
    """Детально проверить соревнования пользователя"""

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        print(f"\n{'='*80}")
        print(f"ДИАГНОСТИКА: Соревнования пользователя {user_id}")
        print(f"{'='*80}\n")

        # 1. Проверяем ВСЕ записи competition_participants для этого пользователя
        print("1. ВСЕ записи в competition_participants:")
        async with db.execute(
            """
            SELECT cp.id, cp.competition_id, cp.distance, cp.distance_name,
                   cp.target_time, cp.proposal_status, cp.status,
                   cp.proposed_by_coach, cp.proposed_by_coach_id,
                   c.name, c.date
            FROM competition_participants cp
            LEFT JOIN competitions c ON c.id = cp.competition_id
            WHERE cp.user_id = ?
            ORDER BY c.date
            """,
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            if rows:
                for row in rows:
                    print(f"  ID: {row[0]}")
                    print(f"    Competition: {row[9]} (ID: {row[1]})")
                    print(f"    Date: {row[10]}")
                    print(f"    Distance: {row[2]} km, Name: '{row[3]}'")
                    print(f"    Target Time: '{row[4]}'")
                    print(f"    Proposal Status: '{row[5]}'")
                    print(f"    Status: '{row[6]}'")
                    print(f"    Proposed by coach: {row[7]} (coach_id: {row[8]})")
                    print()
            else:
                print("  ❌ НЕТ ЗАПИСЕЙ!")

        # 2. Проверяем что возвращает get_user_competitions
        today = date.today().strftime('%Y-%m-%d')
        print(f"\n2. Запрос get_user_competitions (upcoming, date >= {today}):")
        async with db.execute(
            """
            SELECT c.id, c.name, c.date, cp.distance, cp.distance_name, cp.target_time,
                   cp.proposal_status, cp.status
            FROM competitions c
            JOIN competition_participants cp ON c.id = cp.competition_id
            WHERE cp.user_id = ? AND c.date >= date('now')
              AND (cp.proposal_status IS NULL
                   OR cp.proposal_status NOT IN ('pending', 'rejected'))
            ORDER BY c.date ASC
            """,
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            if rows:
                for row in rows:
                    print(f"  ✅ {row[1]} (ID: {row[0]})")
                    print(f"     Date: {row[2]}, Distance: {row[3]} / '{row[4]}'")
                    print(f"     Target Time: '{row[5]}', Proposal Status: '{row[6]}', Status: '{row[7]}'")
                    print()
            else:
                print("  ❌ ФИЛЬТР НЕ ПРОПУСКАЕТ ЗАПИСИ!")

        # 3. Проверяем без фильтра по proposal_status
        print(f"\n3. Запрос БЕЗ фильтра по proposal_status:")
        async with db.execute(
            """
            SELECT c.id, c.name, c.date, cp.proposal_status
            FROM competitions c
            JOIN competition_participants cp ON c.id = cp.competition_id
            WHERE cp.user_id = ? AND c.date >= date('now')
            ORDER BY c.date ASC
            """,
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            if rows:
                for row in rows:
                    print(f"  {row[1]} (ID: {row[0]}) - proposal_status: '{row[3]}'")
            else:
                print("  ❌ НЕТ ПРЕДСТОЯЩИХ СОРЕВНОВАНИЙ!")

        # 4. Проверяем текущую дату SQLite
        async with db.execute("SELECT date('now')") as cursor:
            now_row = await cursor.fetchone()
            print(f"\n4. Текущая дата в SQLite: {now_row[0]}")

async def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python test_my_competitions_debug.py <user_id>")
        print("\nПример: python test_my_competitions_debug.py 123456789")
        sys.exit(1)

    user_id = int(sys.argv[1])
    await debug_user_competitions(user_id)

if __name__ == "__main__":
    asyncio.run(main())
