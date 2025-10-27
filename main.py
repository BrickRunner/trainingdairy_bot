"""
Trainingdiary_bot - Telegram бот для ведения дневника тренировок
Точка входа в приложение
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os

from bot.handlers import router
from settings.settings_handlers_full import router as settings_router
from health.health_handlers import router as health_router
from database.queries import init_db
from notifications.notification_scheduler import start_notification_scheduler
from utils.birthday_checker import schedule_birthday_check

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Основная функция запуска бота"""
    
    # Получение токена из переменных окружения
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logger.error("BOT_TOKEN не найден в .env файле!")
        return
    
    # Инициализация бота и диспетчера
    bot = Bot(token=bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Подключение роутеров
    # ВАЖНО: settings_router должен быть первым, так как содержит более специфичные обработчики (cal_birth_)
    dp.include_router(settings_router)
    dp.include_router(health_router)
    dp.include_router(router)
    
    # Инициализация базы данных
    await init_db()
    logger.info("База данных инициализирована")
    
    # Запуск планировщика уведомлений
    start_notification_scheduler(bot)
    logger.info("Планировщик уведомлений запущен")

    # Запуск планировщика поздравлений с днём рождения
    asyncio.create_task(schedule_birthday_check(bot))
    logger.info("Планировщик поздравлений с днём рождения запущен")

    # Запуск бота
    logger.info("Бот запущен!")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")