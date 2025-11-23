"""
Планировщик ежедневной проверки обновлений нормативов ЕВСК
"""

import asyncio
import logging
from datetime import time
from utils.qualifications_checker import daily_standards_check

logger = logging.getLogger(__name__)


async def schedule_qualifications_check(bot):
    """
    Запускает ежедневную проверку обновлений нормативов ЕВСК в 9:00 утра.

    Args:
        bot: Экземпляр бота для отправки уведомлений
    """
    logger.info("Запущен планировщик проверки обновлений нормативов ЕВСК")

    while True:
        try:
            # Выполняем проверку
            await daily_standards_check(bot)

            # Ждем 24 часа до следующей проверки
            await asyncio.sleep(24 * 60 * 60)  # 24 часа

        except asyncio.CancelledError:
            logger.info("Планировщик проверки нормативов остановлен")
            break
        except Exception as e:
            logger.error(f"Ошибка в планировщике проверки нормативов: {e}")
            # Ждем 1 час перед повторной попыткой
            await asyncio.sleep(60 * 60)
