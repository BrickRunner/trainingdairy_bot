"""
Миграция для добавления полей напоминаний о тренировках
"""

import asyncio
import aiosqlite
import os


async def migrate():
    """Добавляет поля для напоминаний о тренировках в таблицу user_settings"""

    DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

    async with aiosqlite.connect(DB_PATH) as db:
        try:
            # Проверяем и добавляем поле для включения/выключения напоминаний
            cursor = await db.execute("PRAGMA table_info(user_settings)")
            columns = [row[1] for row in await cursor.fetchall()]

            if 'training_reminders_enabled' not in columns:
                await db.execute("""
                    ALTER TABLE user_settings
                    ADD COLUMN training_reminders_enabled INTEGER DEFAULT 0
                """)
                print("+ Dobavleno pole training_reminders_enabled")
            else:
                print("Pole training_reminders_enabled uzhe suschestvuet")

            # Добавляем поле для хранения выбранных дней недели (JSON массив)
            if 'training_reminder_days' not in columns:
                await db.execute("""
                    ALTER TABLE user_settings
                    ADD COLUMN training_reminder_days TEXT DEFAULT '[]'
                """)
                print("+ Dobavleno pole training_reminder_days")
            else:
                print("Pole training_reminder_days uzhe suschestvuet")

            # Добавляем поле для времени напоминания
            if 'training_reminder_time' not in columns:
                await db.execute("""
                    ALTER TABLE user_settings
                    ADD COLUMN training_reminder_time TEXT DEFAULT '18:00'
                """)
                print("+ Dobavleno pole training_reminder_time")
            else:
                print("Pole training_reminder_time uzhe suschestvuet")

            await db.commit()
            print("\nMigratsiya uspeshno vypolnena!")

        except Exception as e:
            print(f"Oshibka pri vypolnenii migratsii: {e}")
            await db.rollback()


if __name__ == "__main__":
    asyncio.run(migrate())
