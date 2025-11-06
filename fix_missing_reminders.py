"""
Создать напоминания для всех существующих регистраций, у которых их нет
"""
import asyncio
import aiosqlite
import os
from datetime import date, datetime

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')


async def fix_reminders():
    """Создать недостающие напоминания"""

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        print("=" * 60)
        print("SOZDANIE NEDOSTAYUSCHIH NAPOMINANIY")
        print("=" * 60)

        # Получаем все регистрации на будущие соревнования
        cursor = await db.execute(
            """
            SELECT
                cp.user_id,
                cp.competition_id,
                c.name as comp_name,
                c.date as comp_date
            FROM competition_participants cp
            JOIN competitions c ON cp.competition_id = c.id
            WHERE cp.status = 'registered'
            AND c.date >= date('now')
            ORDER BY c.date
            """
        )
        registrations = await cursor.fetchall()

        print(f"\nNaydeno registratsiy na budushchie sorevnovaniya: {len(registrations)}\n")

        if not registrations:
            print("Net registratsiy dlya obrabotki")
            return

        from competitions.reminder_scheduler import create_reminders_for_competition

        fixed_count = 0

        for reg in registrations:
            user_id = reg['user_id']
            comp_id = reg['competition_id']
            comp_name = reg['comp_name']
            comp_date_str = reg['comp_date']

            # Проверяем, есть ли уже напоминания
            cursor2 = await db.execute(
                "SELECT COUNT(*) as cnt FROM competition_reminders WHERE user_id = ? AND competition_id = ?",
                (user_id, comp_id)
            )
            row = await cursor2.fetchone()
            existing_count = row['cnt']

            comp_date = datetime.strptime(comp_date_str, '%Y-%m-%d').date()
            days_until = (comp_date - date.today()).days

            print(f"User {user_id} -> {comp_name} ({comp_date_str}, cherez {days_until} dney)")
            print(f"  Suschestvuyuschih napominaniy: {existing_count}")

            if existing_count == 0:
                # Создаём напоминания
                print(f"  Sozdaem napominaniya...")
                await create_reminders_for_competition(user_id, comp_id, comp_date_str)

                # Проверяем, сколько создалось
                cursor3 = await db.execute(
                    "SELECT COUNT(*) as cnt FROM competition_reminders WHERE user_id = ? AND competition_id = ?",
                    (user_id, comp_id)
                )
                row = await cursor3.fetchone()
                new_count = row['cnt']
                print(f"  [OK] Sozdano {new_count} napominaniy")
                fixed_count += 1
            else:
                print(f"  Napominaniya uzhe est, propuskaem")

            print()

        print("=" * 60)
        print(f"GOTOVO! Dobavleno napominaniy dlya {fixed_count} registratsiy")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(fix_reminders())
