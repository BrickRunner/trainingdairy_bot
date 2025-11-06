"""
Создание тестового соревнования и регистрация на него
"""
import asyncio
import aiosqlite
import os
from datetime import date, timedelta

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')


async def create_test():
    """Создать тестовое соревнование"""

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Ищем существующего пользователя
        cursor = await db.execute("SELECT user_id FROM user_settings LIMIT 1")
        user_row = await cursor.fetchone()

        if not user_row:
            print("[X] Ne naydeno polzovateley v user_settings")
            print("Sozdayte testovogo polzovatelya:")
            user_id = int(input("Vvedite user_id (naprimer, 123456789): "))
        else:
            user_id = user_row['user_id']
            print(f"[OK] Ispolzuetsya polzovatel: {user_id}")

        # Создаём соревнование через 30 дней
        comp_date = date.today() + timedelta(days=30)
        comp_name = f"Test Marathon {comp_date.strftime('%Y-%m-%d')}"

        print(f"\nSozdaem sorevnovanie:")
        print(f"  Nazvanie: {comp_name}")
        print(f"  Data: {comp_date.strftime('%Y-%m-%d')} (cherez 30 dney)")

        # Проверяем, есть ли уже такое соревнование
        cursor = await db.execute(
            "SELECT id FROM competitions WHERE name = ? AND date = ?",
            (comp_name, comp_date.strftime('%Y-%m-%d'))
        )
        existing = await cursor.fetchone()

        if existing:
            comp_id = existing['id']
            print(f"[OK] Sorevnovanie uzhe suschestvuet (ID: {comp_id})")
        else:
            # Создаём соревнование
            cursor = await db.execute(
                """
                INSERT INTO competitions
                (name, date, city, organizer, distances, type, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    comp_name,
                    comp_date.strftime('%Y-%m-%d'),
                    'Test City',
                    'Test Organizer',
                    '[21.1, 10.0, 5.0]',
                    'official',
                    'Test competition for reminders'
                )
            )
            await db.commit()
            comp_id = cursor.lastrowid
            print(f"[OK] Sorevnovanie sozdano (ID: {comp_id})")

        # Проверяем, зарегистрирован ли пользователь
        cursor = await db.execute(
            "SELECT id FROM competition_participants WHERE user_id = ? AND competition_id = ?",
            (user_id, comp_id)
        )
        existing_reg = await cursor.fetchone()

        if existing_reg:
            print(f"[OK] Polzovatel uzhe zaregistrirovan")
            # Удаляем старую регистрацию для пересоздания
            await db.execute(
                "DELETE FROM competition_participants WHERE user_id = ? AND competition_id = ?",
                (user_id, comp_id)
            )
            print("[OK] Staraya registratsiya udalena")

        # Регистрируем пользователя
        cursor = await db.execute(
            """
            INSERT INTO competition_participants
            (user_id, competition_id, distance, status)
            VALUES (?, ?, ?, 'registered')
            """,
            (user_id, comp_id, 21.1)
        )
        await db.commit()
        print(f"[OK] Polzovatel zaregistrirovan na distantsiyu 21.1 km")

        # Удаляем старые напоминания
        await db.execute(
            "DELETE FROM competition_reminders WHERE user_id = ? AND competition_id = ?",
            (user_id, comp_id)
        )
        await db.commit()
        print("[OK] Starye napominaniya udaleny")

        # Создаём напоминания
        from competitions.reminder_scheduler import create_reminders_for_competition
        await create_reminders_for_competition(user_id, comp_id, comp_date.strftime('%Y-%m-%d'))

        print("\n[OK] Napominaniya sozdany!")

        # Показываем созданные напоминания
        cursor = await db.execute(
            """
            SELECT id, reminder_type, scheduled_date, sent
            FROM competition_reminders
            WHERE user_id = ? AND competition_id = ?
            ORDER BY scheduled_date
            """,
            (user_id, comp_id)
        )
        reminders = await cursor.fetchall()

        print(f"\nSozdano {len(reminders)} napominaniy:")
        for rem in reminders:
            status = "otpravleno" if rem['sent'] else "NE otpravleno"
            print(f"  - {rem['reminder_type']}: {rem['scheduled_date']} ({status})")

        print(f"\n========================================")
        print(f"GOTOVO!")
        print(f"User ID: {user_id}")
        print(f"Competition ID: {comp_id}")
        print(f"Data sorevnovaniya: {comp_date.strftime('%Y-%m-%d')}")
        print(f"Napominaniy sozdano: {len(reminders)}")
        print(f"========================================")


if __name__ == "__main__":
    asyncio.run(create_test())
