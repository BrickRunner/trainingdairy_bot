"""
Инициализация базы данных с правильной схемой
"""
import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.insert(0, os.path.dirname(__file__))

from database.queries import init_db


async def main():
    print("Инициализация базы данных...")
    await init_db()
    print("✅ База данных успешно инициализирована!")
    print("✅ Таблица competition_participants создана с полем distance_name")


if __name__ == '__main__':
    asyncio.run(main())
