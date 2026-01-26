"""
Автоматическая миграция: Убрать NOT NULL constraint для поля duration в таблице trainings
"""

import aiosqlite
import asyncio
import os
import shutil
from datetime import datetime


DB_PATH = os.getenv('DB_PATH', 'database.sqlite')


async def migrate():
    """Выполняет миграцию автоматически"""

    print(f"🔄 Миграция базы данных: {DB_PATH}")

    if not os.path.exists(DB_PATH):
        print("⚠️  База данных не найдена. Миграция не требуется.")
        return

    # Создаем бэкап
    backup_path = f"{DB_PATH}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    try:
        shutil.copy2(DB_PATH, backup_path)
        print(f"✅ Бэкап создан: {backup_path}")
    except Exception as e:
        print(f"❌ Ошибка создания бэкапа: {e}")
        return

    async with aiosqlite.connect(DB_PATH) as db:
        # Проверяем, нужна ли миграция
        async with db.execute("PRAGMA table_info(trainings)") as cursor:
            columns = await cursor.fetchall()
            duration_col = [col for col in columns if col[1] == 'duration']

            if duration_col and duration_col[0][3] == 0:  # уже nullable
                print("✅ Поле duration уже nullable. Миграция не требуется.")
                os.remove(backup_path)  # удаляем ненужный бэкап
                return

        print("🔨 Выполняем миграцию...")

        try:
            # 1. Создаем новую таблицу
            await db.execute("""
                CREATE TABLE trainings_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    date DATE NOT NULL,
                    time TEXT,
                    duration INTEGER,
                    distance REAL,
                    avg_pace TEXT,
                    pace_unit TEXT,
                    avg_pulse INTEGER,
                    max_pulse INTEGER,
                    exercises TEXT,
                    intervals TEXT,
                    calculated_volume REAL,
                    description TEXT,
                    results TEXT,
                    comment TEXT,
                    fatigue_level INTEGER,
                    added_by_coach_id INTEGER,
                    is_planned INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (added_by_coach_id) REFERENCES users(id)
                )
            """)

            # 2. Копируем данные
            await db.execute("""
                INSERT INTO trainings_new
                SELECT * FROM trainings
            """)

            # 3. Удаляем старую таблицу
            await db.execute("DROP TABLE trainings")

            # 4. Переименовываем
            await db.execute("ALTER TABLE trainings_new RENAME TO trainings")

            await db.commit()

            # Проверяем результат
            async with db.execute("SELECT COUNT(*) FROM trainings") as cursor:
                count = await cursor.fetchone()
                print(f"✅ Миграция успешна! Тренировок в базе: {count[0]}")

        except Exception as e:
            print(f"❌ Ошибка миграции: {e}")
            print(f"💾 Восстановите из бэкапа: {backup_path}")
            raise


if __name__ == "__main__":
    asyncio.run(migrate())
