"""
Скрипт для удаления всех нормативов из базы данных.
Используется для тестирования системы автоматического обновления.
"""

import asyncio
import aiosqlite
import os

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')


async def clear_standards():
    """
    Удаляет все нормативы из базы данных.
    """
    print("=" * 60)
    print("УДАЛЕНИЕ НОРМАТИВОВ ИЗ БАЗЫ ДАННЫХ")
    print("=" * 60)
    print(f"База данных: {DB_PATH}\n")

    async with aiosqlite.connect(DB_PATH) as db:
        # Получаем количество записей до удаления
        print("[STATISTICS] Before deletion:")
        print("-" * 60)

        async with db.execute("SELECT COUNT(*) FROM running_standards") as cursor:
            row = await cursor.fetchone()
            running_count = row[0] if row else 0
            print(f"  Running: {running_count} standards")

        async with db.execute("SELECT COUNT(*) FROM swimming_standards") as cursor:
            row = await cursor.fetchone()
            swimming_count = row[0] if row else 0
            print(f"  Swimming: {swimming_count} standards")

        async with db.execute("SELECT COUNT(*) FROM cycling_standards") as cursor:
            row = await cursor.fetchone()
            cycling_count = row[0] if row else 0
            print(f"  Cycling: {cycling_count} standards")

        async with db.execute("SELECT COUNT(*) FROM standards_versions") as cursor:
            row = await cursor.fetchone()
            versions_count = row[0] if row else 0
            print(f"  Versions: {versions_count} records")

        # Проверяем наличие таблицы standards_tracking
        try:
            async with db.execute("SELECT COUNT(*) FROM standards_tracking") as cursor:
                row = await cursor.fetchone()
                tracking_count = row[0] if row else 0
                print(f"  Tracking: {tracking_count} records")
        except:
            tracking_count = 0

        total_before = running_count + swimming_count + cycling_count + versions_count + tracking_count
        print(f"\n  TOTAL: {total_before} records")

        # Удаляем данные
        print("\n[DELETING] Removing data...")
        print("-" * 60)

        await db.execute("DELETE FROM running_standards")
        print("  [OK] Running standards deleted")

        await db.execute("DELETE FROM swimming_standards")
        print("  [OK] Swimming standards deleted")

        await db.execute("DELETE FROM cycling_standards")
        print("  [OK] Cycling standards deleted")

        await db.execute("DELETE FROM standards_versions")
        print("  [OK] Standards versions deleted")

        # Удаляем данные отслеживания (если таблица существует)
        try:
            await db.execute("DELETE FROM standards_tracking")
            print("  [OK] Tracking data deleted")
        except:
            pass

        await db.commit()

        # Проверяем количество после удаления
        print("\n[STATISTICS] After deletion:")
        print("-" * 60)

        async with db.execute("SELECT COUNT(*) FROM running_standards") as cursor:
            row = await cursor.fetchone()
            print(f"  Running: {row[0]} standards")

        async with db.execute("SELECT COUNT(*) FROM swimming_standards") as cursor:
            row = await cursor.fetchone()
            print(f"  Swimming: {row[0]} standards")

        async with db.execute("SELECT COUNT(*) FROM cycling_standards") as cursor:
            row = await cursor.fetchone()
            print(f"  Cycling: {row[0]} standards")

        async with db.execute("SELECT COUNT(*) FROM standards_versions") as cursor:
            row = await cursor.fetchone()
            print(f"  Versions: {row[0]} records")

        try:
            async with db.execute("SELECT COUNT(*) FROM standards_tracking") as cursor:
                row = await cursor.fetchone()
                print(f"  Tracking: {row[0]} records")
        except:
            pass

    print("\n" + "=" * 60)
    print("[SUCCESS] DELETION COMPLETED!")
    print("=" * 60)
    print("\nТеперь можно запустить бота для тестирования автоматического обновления:")
    print("  python main.py")
    print("\nИли запустить проверку вручную:")
    print("  python utils/qualifications_checker.py")


if __name__ == "__main__":
    asyncio.run(clear_standards())
