"""
Миграционный скрипт для добавления таблицы health_metrics
Запустить один раз: python migrate_health_table.py
"""

import asyncio
import aiosqlite
import os
import sys

# Настройка кодировки для Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from database.models import CREATE_HEALTH_METRICS_TABLE

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')


async def migrate():
    """Добавляет таблицу health_metrics если её нет"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Проверяем, существует ли таблица
        async with db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='health_metrics'"
        ) as cursor:
            exists = await cursor.fetchone()

        if exists:
            print("OK - Таблица health_metrics уже существует")
        else:
            print("Создаю таблицу health_metrics...")
            await db.execute(CREATE_HEALTH_METRICS_TABLE)
            await db.commit()
            print("OK - Таблица health_metrics успешно создана!")

        # Проверяем структуру
        async with db.execute("PRAGMA table_info(health_metrics)") as cursor:
            columns = await cursor.fetchall()
            print(f"\nСтруктура таблицы ({len(columns)} колонок):")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")


if __name__ == "__main__":
    print("Запуск миграции...")
    asyncio.run(migrate())
    print("\nМиграция завершена!")
