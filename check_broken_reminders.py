"""
Проверка и удаление сломанных напоминаний
"""
import asyncio
import aiosqlite
import os

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')


async def check_and_fix():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        print("=" * 60)
        print("PROVERKA SLOMANNYH NAPOMINANIY")
        print("=" * 60)

        # Находим напоминания, у которых нет соревнования
        cursor = await db.execute(
            """
            SELECT r.*
            FROM competition_reminders r
            LEFT JOIN competitions c ON r.competition_id = c.id
            WHERE c.id IS NULL
            """
        )
        broken_reminders = await cursor.fetchall()

        if not broken_reminders:
            print("\n[OK] Vse napominaniya v poryadke, net slomannyh")
            return

        print(f"\n[!] Naydeno {len(broken_reminders)} slomannyh napominaniy:\n")

        for rem in broken_reminders:
            print(f"ID: {rem['id']}")
            print(f"  User ID: {rem['user_id']}")
            print(f"  Competition ID: {rem['competition_id']} (NE SUSCHESTVUET)")
            print(f"  Type: {rem['reminder_type']}")
            print(f"  Scheduled: {rem['scheduled_date']}")
            print(f"  Sent: {rem['sent']}")
            print()

        # Удаляем сломанные напоминания
        print("=" * 60)
        print("UDALENIE SLOMANNYH NAPOMINANIY")
        print("=" * 60)

        cursor = await db.execute(
            """
            DELETE FROM competition_reminders
            WHERE id IN (
                SELECT r.id
                FROM competition_reminders r
                LEFT JOIN competitions c ON r.competition_id = c.id
                WHERE c.id IS NULL
            )
            """
        )
        deleted_count = cursor.rowcount
        await db.commit()

        print(f"\n[OK] Udaleno {deleted_count} slomannyh napominaniy")

        # Проверяем участников без соревнований
        print("\n" + "=" * 60)
        print("PROVERKA UCHASTNIKOV BEZ SOREVNOVANIY")
        print("=" * 60)

        cursor = await db.execute(
            """
            SELECT cp.*
            FROM competition_participants cp
            LEFT JOIN competitions c ON cp.competition_id = c.id
            WHERE c.id IS NULL
            """
        )
        broken_participants = await cursor.fetchall()

        if broken_participants:
            print(f"\n[!] Naydeno {len(broken_participants)} uchastnikov bez sorevnovaniy")
            for p in broken_participants:
                print(f"  User: {p['user_id']}, Comp ID: {p['competition_id']} (NE SUSCHESTVUET)")

            # Удаляем
            cursor = await db.execute(
                """
                DELETE FROM competition_participants
                WHERE id IN (
                    SELECT cp.id
                    FROM competition_participants cp
                    LEFT JOIN competitions c ON cp.competition_id = c.id
                    WHERE c.id IS NULL
                )
                """
            )
            deleted_count = cursor.rowcount
            await db.commit()
            print(f"\n[OK] Udaleno {deleted_count} slomannyh zapisey uchastnikov")
        else:
            print("\n[OK] Vse uchastniki v poryadke")


if __name__ == "__main__":
    asyncio.run(check_and_fix())
