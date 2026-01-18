"""
Полная диагностика проблемы с предложениями соревнований
"""
import asyncio
import aiosqlite
import os
import sys

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

async def full_diagnosis(student_id: int, coach_id: int = None):
    """Полная диагностика"""

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        print(f"\n{'='*100}")
        print(f"ПОЛНАЯ ДИАГНОСТИКА: Предложения соревнований")
        print(f"Student ID: {student_id}")
        if coach_id:
            print(f"Coach ID: {coach_id}")
        print(f"{'='*100}\n")

        # 1. ВСЕ записи competition_participants для ученика
        print("1. ВСЕ записи в competition_participants для ученика:")
        print("-" * 100)
        async with db.execute(
            """
            SELECT cp.id, cp.competition_id, cp.distance, cp.distance_name,
                   cp.target_time, cp.proposal_status, cp.status,
                   cp.proposed_by_coach, cp.proposed_by_coach_id, cp.reminders_enabled,
                   c.name, c.date
            FROM competition_participants cp
            LEFT JOIN competitions c ON c.id = cp.competition_id
            WHERE cp.user_id = ?
            ORDER BY cp.id DESC
            """,
            (student_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            if rows:
                for i, row in enumerate(rows, 1):
                    print(f"\n{i}. ЗАПИСЬ ID: {row[0]}")
                    print(f"   Competition: {row[10]} (comp_id={row[1]})")
                    print(f"   Date: {row[11]}")
                    print(f"   Distance: {row[2]} km")
                    print(f"   Distance Name: '{row[3]}'")
                    print(f"   Target Time: '{row[4]}' (type: {type(row[4]).__name__})")
                    print(f"   Proposal Status: '{row[5]}'")
                    print(f"   Status: '{row[6]}'")
                    print(f"   Proposed by coach: {row[7]} (coach_id={row[8]})")
                    print(f"   Reminders enabled: {row[9]}")

                    # Проверка target_time
                    target_time_value = row[4]
                    has_target_time = (
                        target_time_value is not None
                        and target_time_value != ''
                        and str(target_time_value).lower() != 'none'
                    )
                    print(f"   >>> has_target_time = {has_target_time}")
            else:
                print("   ❌ НЕТ ЗАПИСЕЙ!")

        # 2. Проверка фильтра get_user_competitions
        print(f"\n\n2. Результат запроса get_user_competitions (upcoming):")
        print("-" * 100)
        async with db.execute(
            """
            SELECT c.id, c.name, c.date, cp.distance, cp.distance_name,
                   cp.target_time, cp.proposal_status, cp.status
            FROM competitions c
            JOIN competition_participants cp ON c.id = cp.competition_id
            WHERE cp.user_id = ? AND c.date >= date('now')
              AND (cp.proposal_status IS NULL
                   OR cp.proposal_status NOT IN ('pending', 'rejected'))
            ORDER BY c.date ASC
            """,
            (student_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            if rows:
                for i, row in enumerate(rows, 1):
                    print(f"\n{i}. ✅ ПРОШЛО ФИЛЬТР:")
                    print(f"   {row[1]} (comp_id={row[0]})")
                    print(f"   Date: {row[2]}")
                    print(f"   Distance: {row[3]} km / Name: '{row[4]}'")
                    print(f"   Target Time: '{row[5]}'")
                    print(f"   Proposal Status: '{row[6]}'")
                    print(f"   Status: '{row[7]}'")
            else:
                print("   ❌ НЕТ ЗАПИСЕЙ! Все записи заблокированы фильтром!")

        # 3. Записи, заблокированные фильтром
        print(f"\n\n3. Записи ЗАБЛОКИРОВАННЫЕ фильтром proposal_status:")
        print("-" * 100)
        async with db.execute(
            """
            SELECT c.id, c.name, c.date, cp.proposal_status, cp.status
            FROM competitions c
            JOIN competition_participants cp ON c.id = cp.competition_id
            WHERE cp.user_id = ? AND c.date >= date('now')
              AND (cp.proposal_status IN ('pending', 'rejected'))
            ORDER BY c.date ASC
            """,
            (student_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            if rows:
                for i, row in enumerate(rows, 1):
                    print(f"\n{i}. ⚠️ ЗАБЛОКИРОВАНО:")
                    print(f"   {row[1]} (comp_id={row[0]})")
                    print(f"   Date: {row[2]}")
                    print(f"   Proposal Status: '{row[3]}' ← БЛОКИРУЕТ")
                    print(f"   Status: '{row[4]}'")
            else:
                print("   ✅ Нет заблокированных записей")

        # 4. Текущая дата SQLite
        async with db.execute("SELECT date('now'), datetime('now')") as cursor:
            row = await cursor.fetchone()
            print(f"\n\n4. Текущая дата/время в SQLite:")
            print(f"   date('now') = {row[0]}")
            print(f"   datetime('now') = {row[1]}")

        # 5. Если указан тренер, показываем что он видит
        if coach_id:
            print(f"\n\n5. Что видит ТРЕНЕР (get_student_competitions_for_coach):")
            print("-" * 100)
            async with db.execute(
                """
                SELECT c.id, c.name, c.date, cp.distance, cp.distance_name,
                       cp.target_time, cp.proposal_status, cp.status
                FROM competitions c
                JOIN competition_participants cp ON c.id = cp.competition_id
                WHERE cp.user_id = ? AND c.date >= date('now')
                ORDER BY c.date ASC
                """,
                (student_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                if rows:
                    for i, row in enumerate(rows, 1):
                        print(f"\n{i}. {row[1]} (comp_id={row[0]})")
                        print(f"   Date: {row[2]}")
                        print(f"   Distance: {row[3]} km / Name: '{row[4]}'")
                        print(f"   Target Time: '{row[5]}'")
                        print(f"   Proposal Status: '{row[6]}'")
                        print(f"   Status: '{row[7]}'")
                else:
                    print("   ❌ Тренер тоже ничего не видит!")

async def main():
    if len(sys.argv) < 2:
        print("Usage: python diagnose_proposal_issue.py <student_id> [coach_id]")
        print("\nПример:")
        print("  python diagnose_proposal_issue.py 123456789")
        print("  python diagnose_proposal_issue.py 123456789 987654321")
        sys.exit(1)

    student_id = int(sys.argv[1])
    coach_id = int(sys.argv[2]) if len(sys.argv) > 2 else None

    await full_diagnosis(student_id, coach_id)

if __name__ == "__main__":
    asyncio.run(main())
