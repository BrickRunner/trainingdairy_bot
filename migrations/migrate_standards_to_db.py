"""
Миграция для переноса статических нормативов ЕВСК в базу данных.
Переносит все нормативы из utils/qualifications.py в таблицы БД.
"""

import asyncio
import aiosqlite
import os
import sys
from datetime import date

# Добавляем корневую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.running_standards_frs24 import get_frs24_running_standards
from utils.swimming_standards_frs24 import get_frs24_swimming_standards
from utils.cycling_standards_frs24 import get_frs24_cycling_standards

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')


async def init_standards_tables():
    """
    Создает таблицы для хранения нормативов, если они не существуют.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        # Таблица нормативов по бегу
        await db.execute("""
            CREATE TABLE IF NOT EXISTS running_standards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                distance REAL NOT NULL,
                gender TEXT NOT NULL,
                rank TEXT NOT NULL,
                time_seconds REAL NOT NULL,
                version TEXT NOT NULL,
                effective_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(distance, gender, rank, version)
            )
        """)

        # Таблица нормативов по плаванию
        await db.execute("""
            CREATE TABLE IF NOT EXISTS swimming_standards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                distance REAL NOT NULL,
                pool_length INTEGER NOT NULL,
                gender TEXT NOT NULL,
                rank TEXT NOT NULL,
                time_seconds REAL NOT NULL,
                version TEXT NOT NULL,
                effective_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(distance, pool_length, gender, rank, version)
            )
        """)

        # Таблица нормативов по велоспорту
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cycling_standards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                distance REAL NOT NULL,
                discipline TEXT NOT NULL,
                gender TEXT NOT NULL,
                rank TEXT NOT NULL,
                time_seconds REAL,
                place INTEGER,
                version TEXT NOT NULL,
                effective_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(distance, discipline, gender, rank, version)
            )
        """)

        # Таблица версий нормативов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS standards_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sport_type TEXT NOT NULL,
                version TEXT NOT NULL,
                effective_date DATE NOT NULL,
                source_url TEXT,
                file_hash TEXT,
                is_active INTEGER DEFAULT 1,
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(sport_type, version)
            )
        """)

        await db.commit()
        print("[OK] Таблицы созданы успешно")


async def migrate_running_standards():
    """
    Мигрирует нормативы ЕВСК по бегу в БД.
    Использует данные из http://frs24.ru/st/normativ-po-begu/
    """
    version = "EVSK 2022-2025 (frs24.ru)"
    effective_date = "2025-01-01"

    async with aiosqlite.connect(DB_PATH) as db:
        # Проверяем, есть ли уже эта версия
        async with db.execute(
            "SELECT id FROM standards_versions WHERE sport_type = 'running' AND version = ?",
            (version,)
        ) as cursor:
            existing = await cursor.fetchone()

        if existing:
            print(f"[WARNING] Версия '{version}' для бега уже существует, пропускаем миграцию")
            return

        print(f"\n[RUNNING] Миграция нормативов по бегу (версия {version})...")

        # Добавляем версию
        await db.execute(
            """
            INSERT INTO standards_versions (sport_type, version, effective_date, source_url, is_active)
            VALUES ('running', ?, ?, ?, 1)
            """,
            (version, effective_date, 'http://frs24.ru/st/normativ-po-begu/')
        )

        # Получаем нормативы с frs24.ru
        standards = get_frs24_running_standards()

        # Переносим нормативы
        count = 0
        for standard in standards:
            await db.execute(
                """
                INSERT OR IGNORE INTO running_standards
                (distance, gender, rank, time_seconds, version, effective_date)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    standard['distance'],
                    standard['gender'],
                    standard['rank'],
                    standard['time_seconds'],
                    version,
                    effective_date
                )
            )
            count += 1

        await db.commit()
        print(f"[OK] Мигрировано {count} нормативов по бегу")


async def migrate_swimming_standards():
    """
    Мигрирует нормативы по плаванию в БД.
    Использует данные из http://frs24.ru/st/plavanie-normativ/
    """
    version = "EVSK 2022-2025 (frs24.ru)"
    effective_date = "2025-01-01"

    async with aiosqlite.connect(DB_PATH) as db:
        # Проверяем, есть ли уже эта версия
        async with db.execute(
            "SELECT id FROM standards_versions WHERE sport_type = 'swimming' AND version = ?",
            (version,)
        ) as cursor:
            existing = await cursor.fetchone()

        if existing:
            print(f"[WARNING] Версия '{version}' для плавания уже существует, пропускаем миграцию")
            return

        print(f"\n[SWIMMING] Миграция нормативов по плаванию (версия {version})...")

        # Добавляем версию
        await db.execute(
            """
            INSERT INTO standards_versions (sport_type, version, effective_date, source_url, is_active)
            VALUES ('swimming', ?, ?, ?, 1)
            """,
            (version, effective_date, 'http://frs24.ru/st/plavanie-normativ/')
        )

        # Получаем нормативы с frs24.ru
        standards = get_frs24_swimming_standards()

        # Переносим нормативы
        count = 0
        for standard in standards:
            await db.execute(
                """
                INSERT OR IGNORE INTO swimming_standards
                (distance, pool_length, gender, rank, time_seconds, version, effective_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    standard['distance'],
                    standard['pool_length'],
                    standard['gender'],
                    standard['rank'],
                    standard['time_seconds'],
                    version,
                    effective_date
                )
            )
            count += 1

        await db.commit()
        print(f"[OK] Мигрировано {count} нормативов по плаванию")


async def migrate_cycling_standards():
    """
    Мигрирует нормативы по велоспорту в БД.
    Использует данные из http://frs24.ru/st/velosport-shosse-normativ/

    ВАЖНО: Разряды по велоспорту присваиваются по времени в шоссейных гонках.
    Две дисциплины: индивидуальная гонка и парная гонка.
    """
    version = "EVSK 2022-2025 (frs24.ru)"
    effective_date = "2025-01-01"

    async with aiosqlite.connect(DB_PATH) as db:
        # Проверяем, есть ли уже эта версия
        async with db.execute(
            "SELECT id FROM standards_versions WHERE sport_type = 'cycling' AND version = ?",
            (version,)
        ) as cursor:
            existing = await cursor.fetchone()

        if existing:
            print(f"[WARNING] Версия '{version}' для велоспорта уже существует, пропускаем миграцию")
            return

        print(f"\n[CYCLING] Миграция нормативов по велоспорту (версия {version})...")

        # Добавляем версию
        await db.execute(
            """
            INSERT INTO standards_versions (sport_type, version, effective_date, source_url, is_active)
            VALUES ('cycling', ?, ?, ?, 1)
            """,
            (version, effective_date, 'http://frs24.ru/st/velosport-shosse-normativ/')
        )

        # Получаем нормативы с frs24.ru
        standards = get_frs24_cycling_standards()

        # Переносим нормативы
        count = 0
        for standard in standards:
            await db.execute(
                """
                INSERT OR IGNORE INTO cycling_standards
                (distance, discipline, gender, rank, time_seconds, place, version, effective_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    standard['distance'],
                    standard['discipline'],
                    standard['gender'],
                    standard['rank'],
                    standard['time_seconds'],
                    None,  # place не используется для временных нормативов
                    version,
                    effective_date
                )
            )
            count += 1

        await db.commit()
        print(f"[OK] Мигрировано {count} нормативов по велоспорту (шоссе)")
        print(f"[OK] Примечание: разряды присваиваются по времени в шоссейных гонках")


async def verify_migration():
    """
    Проверяет успешность миграции.
    """
    print("\n" + "="*60)
    print("ПРОВЕРКА МИГРАЦИИ")
    print("="*60)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Проверяем версии
        print("\n[VERSIONS] Версии нормативов:")
        async with db.execute("SELECT * FROM standards_versions ORDER BY sport_type") as cursor:
            versions = await cursor.fetchall()
            for v in versions:
                status = "[ACTIVE]" if v['is_active'] else "[INACTIVE]"
                print(f"  - {v['sport_type']}: {v['version']} (с {v['effective_date']}) - {status}")

        # Проверяем количество нормативов по бегу
        async with db.execute("SELECT COUNT(*) as cnt FROM running_standards") as cursor:
            row = await cursor.fetchone()
            print(f"\n[RUNNING] Нормативы по бегу: {row['cnt']} записей")

        # Проверяем количество нормативов по плаванию
        async with db.execute("SELECT COUNT(*) as cnt FROM swimming_standards WHERE pool_length = 50") as cursor:
            row = await cursor.fetchone()
            count_50m = row['cnt']

        async with db.execute("SELECT COUNT(*) as cnt FROM swimming_standards WHERE pool_length = 25") as cursor:
            row = await cursor.fetchone()
            count_25m = row['cnt']

        print(f"[SWIMMING] Нормативы по плаванию:")
        print(f"  - Бассейн 50м: {count_50m} записей")
        print(f"  - Бассейн 25м: {count_25m} записей")
        print(f"  - Всего: {count_50m + count_25m} записей")

        # Проверяем количество нормативов по велоспорту
        async with db.execute("SELECT COUNT(*) as cnt FROM cycling_standards") as cursor:
            row = await cursor.fetchone()
            print(f"\n[CYCLING] Нормативы по велоспорту: {row['cnt']} записей")

        async with db.execute("SELECT discipline, COUNT(*) as cnt FROM cycling_standards GROUP BY discipline") as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                print(f"  - {row['discipline']}: {row['cnt']} разрядов")

        # Примеры нормативов
        print("\n[EXAMPLES] Примеры нормативов (бег, мужчины, полумарафон):")
        async with db.execute(
            """
            SELECT rank, time_seconds
            FROM running_standards
            WHERE distance = 21.0975 AND gender = 'male'
            ORDER BY time_seconds
            """) as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                minutes = int(row['time_seconds'] // 60)
                seconds = int(row['time_seconds'] % 60)
                print(f"  - {row['rank']}: {minutes:02d}:{seconds:02d}")

        print("\n[EXAMPLES] Примеры нормативов (велоспорт, мужчины, 25км, индивидуальная гонка):")
        async with db.execute(
            """
            SELECT rank, time_seconds, discipline
            FROM cycling_standards
            WHERE distance = 25 AND gender = 'male' AND discipline = 'индивидуальная гонка'
            ORDER BY time_seconds
            """) as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                minutes = int(row['time_seconds'] // 60)
                seconds = int(row['time_seconds'] % 60)
                print(f"  - {row['rank']}: {minutes:02d}:{seconds:02d}")


async def main():
    """
    Основная функция миграции.
    """
    print("="*60)
    print("МИГРАЦИЯ НОРМАТИВОВ ЕВСК В БАЗУ ДАННЫХ")
    print("="*60)
    print(f"База данных: {DB_PATH}")
    print()

    try:
        # Создаем таблицы
        await init_standards_tables()

        # Мигрируем нормативы по бегу
        await migrate_running_standards()

        # Мигрируем нормативы по плаванию
        await migrate_swimming_standards()

        # Мигрируем нормативы по велоспорту
        await migrate_cycling_standards()

        # Проверяем результат
        await verify_migration()

        print("\n" + "="*60)
        print("[SUCCESS] МИГРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
        print("="*60)
        print("\nИсточник данных: frs24.ru")
        print("Ожидаемое количество нормативов:")
        print("  - Бег: 242 норматива")
        print("  - Плавание: 630 нормативов")
        print("  - Велоспорт: 89 нормативов")
        print("  - Всего: 961 норматив")
        print("\nСледующие шаги:")
        print("1. Запустите бота для проверки работы с новыми нормативами")
        print("2. Функция get_qualification_async() теперь работает с БД для всех видов спорта")
        print("3. Велоспорт: разряды определяются по ВРЕМЕНИ в шоссейных гонках")
        print("4. При ошибках БД будет автоматический fallback на статические словари")

    except Exception as e:
        print(f"\n[ERROR] ОШИБКА МИГРАЦИИ: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
