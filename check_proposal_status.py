"""
Быстрая проверка proposal_status после принятия
"""
import asyncio
import aiosqlite
import os
import sys

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

async def check_status(student_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        print(f"\n{'='*80}")
        print(f"ПРОВЕРКА proposal_status для ученика {student_id}")
        print(f"{'='*80}\n")

        # Все записи для ученика
        async with db.execute(
            """
            SELECT cp.id, c.name, c.date, cp.distance, cp.distance_name,
                   cp.proposal_status, cp.status, cp.target_time
            FROM competition_participants cp
            JOIN competitions c ON c.id = cp.competition_id
            WHERE cp.user_id = ?
            ORDER BY c.date DESC
            """,
            (student_id,)
        ) as cursor:
            rows = await cursor.fetchall()

            if not rows:
                print("❌ НЕТ ЗАПИСЕЙ!")
                return

            for i, row in enumerate(rows, 1):
                print(f"{i}. {row[1]} ({row[2]})")
                print(f"   Distance: {row[3]} / {row[4]}")
                print(f"   Proposal Status: '{row[5]}'")
                print(f"   Status: '{row[6]}'")
                print(f"   Target Time: '{row[7]}'")

                # Проверка фильтра get_user_competitions
                proposal_ok = (row[5] is None or row[5] not in ('pending', 'rejected'))
                date_ok = row[2] >= '2026-01-18'  # примерная проверка

                if proposal_ok and date_ok:
                    print(f"   ✅ ПРОЙДЕТ фильтр get_user_competitions")
                else:
                    if not proposal_ok:
                        print(f"   ❌ БЛОКИРУЕТСЯ фильтром: proposal_status='{row[5]}'")
                    if not date_ok:
                        print(f"   ❌ БЛОКИРУЕТСЯ: дата в прошлом")
                print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_proposal_status.py <student_id>")
        sys.exit(1)

    asyncio.run(check_status(int(sys.argv[1])))
