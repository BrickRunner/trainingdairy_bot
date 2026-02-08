"""
Trainingdiary_bot - Telegram бот для ведения дневника тренировок
Точка входа в приложение
"""

# Загружаем переменные окружения из .env файла (BOT_TOKEN и др.)
from dotenv import load_dotenv
load_dotenv()

import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# Импортируем роутеры всех модулей бота
from bot.handlers import router
from settings.settings_handlers_full import router as settings_router
from health.health_handlers import router as health_router
from health.health_handlers_calendar_export import router as health_calendar_export_router
from ratings.ratings_handlers import router as ratings_router
from registration.registration_handlers import router as registration_router
from competitions.competitions_handlers import router as competitions_router
from competitions.custom_competitions_handlers import router as custom_competitions_router
from competitions.search_competitions_handlers import router as search_competitions_router
from competitions.competitions_statistics_handlers import router as competitions_statistics_router
from competitions.upcoming_competitions_handlers import router as upcoming_competitions_router
from coach.coach_handlers import router as coach_router
from coach.coach_add_training_handlers import router as coach_add_training_router
from coach.coach_competitions_handlers import router as coach_competitions_router
from coach.coach_upcoming_competitions_handlers import router as coach_upcoming_competitions_router
from training_assistant.ta_handlers import router as training_assistant_router
from help.help_handlers import router as help_router

# Импортируем функции для работы с базой данных и фоновыми задачами
from database.queries import init_db
from notifications.notification_scheduler import start_notification_scheduler
from utils.birthday_checker import schedule_birthday_check
from ratings.rating_updater import schedule_rating_updates
from competitions.reminder_scheduler import schedule_competition_reminders
from utils.qualifications_scheduler import schedule_qualifications_check
from utils.qualifications_checker import daily_standards_check
from utils.database_backup import schedule_backups

# Настраиваем логирование для отслеживания работы бота
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Основная функция запуска бота"""

    # Получаем токен бота из переменных окружения
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logger.error("BOT_TOKEN не найден в .env файле!")
        return

    # Инициализируем бота и диспетчер с хранилищем состояний в памяти
    bot = Bot(token=bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # ВАЖНО: Порядок регистрации роутеров критичен!
    # Более специфичные роутеры должны быть зарегистрированы первыми,
    # иначе общие роутеры могут перехватить их callback'и
    dp.include_router(upcoming_competitions_router)
    dp.include_router(registration_router)
    dp.include_router(settings_router)
    dp.include_router(competitions_statistics_router)
    dp.include_router(coach_router)
    dp.include_router(coach_add_training_router)
    dp.include_router(coach_upcoming_competitions_router)
    dp.include_router(custom_competitions_router)
    dp.include_router(coach_competitions_router)
    dp.include_router(competitions_router)
    dp.include_router(search_competitions_router)
    dp.include_router(health_calendar_export_router)
    dp.include_router(health_router)
    dp.include_router(ratings_router)
    dp.include_router(training_assistant_router)
    dp.include_router(help_router)
    dp.include_router(router)  

    # Создаем таблицы в базе данных (если их еще нет)
    await init_db()
    logger.info("База данных инициализирована")

    # Запускаем фоновую задачу для автоматического резервного копирования БД
    asyncio.create_task(schedule_backups())
    logger.info("Планировщик backup'ов базы данных запущен")

    # Проверяем обновления спортивных нормативов ЕВСК при старте бота
    logger.info("Проверка обновлений нормативов ЕВСК при старте...")
    try:
        await daily_standards_check(bot)
    except Exception as e:
        logger.error(f"Ошибка при проверке нормативов при старте: {e}")

    # Запускаем планировщик уведомлений (напоминания о тренировках, здоровье и т.д.)
    start_notification_scheduler(bot)
    logger.info("Планировщик уведомлений запущен")

    # Запускаем ежедневную проверку дней рождения пользователей для поздравлений
    asyncio.create_task(schedule_birthday_check(bot))
    logger.info("Планировщик поздравлений с днём рождения запущен")

    # Запускаем еженедельное обновление рейтинга пользователей
    asyncio.create_task(schedule_rating_updates())
    logger.info("Планировщик обновления рейтингов запущен")

    # Запускаем отправку напоминаний о предстоящих соревнованиях
    asyncio.create_task(schedule_competition_reminders(bot))
    logger.info("Планировщик напоминаний о соревнованиях запущен")

    # Запускаем ежемесячную проверку обновлений нормативов ЕВСК
    asyncio.create_task(schedule_qualifications_check(bot))
    logger.info("Планировщик проверки обновлений нормативов ЕВСК запущен")

    # Запускаем бота в режиме long polling (постоянное получение обновлений)
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