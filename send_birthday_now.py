"""
Скрипт для ручной отправки поздравлений с днём рождения (для тестирования)
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from aiogram import Bot

# Настройка кодировки для Windows консоли
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Загрузка переменных окружения
load_dotenv()

from utils.birthday_checker import check_and_send_birthday_greetings


async def main():
    """Отправка поздравлений вручную"""

    print("=" * 60)
    print("РУЧНАЯ ОТПРАВКА ПОЗДРАВЛЕНИЙ С ДНЁМ РОЖДЕНИЯ")
    print("=" * 60)

    # Получение токена
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        print("❌ ОШИБКА: BOT_TOKEN не найден в .env файле!")
        return

    print("\n✅ Токен бота найден")

    # Инициализация бота
    bot = Bot(token=bot_token)

    try:
        print("\n🚀 Запуск проверки и отправки поздравлений...")
        print("-" * 60)

        # Вызываем функцию проверки и отправки
        await check_and_send_birthday_greetings(bot)

        print("-" * 60)
        print("\n✅ Проверка завершена!")
        print("\nЕсли сегодня день рождения у пользователя,")
        print("поздравление должно быть отправлено.")

    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
