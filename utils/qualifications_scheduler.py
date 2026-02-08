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
            await daily_standards_check(bot)

            await asyncio.sleep(24 * 60 * 60)  

        except asyncio.CancelledError:
            logger.info("Планировщик проверки нормативов остановлен")
            break
        except Exception as e:
            logger.error(f"Ошибка в планировщике проверки нормативов: {e}")
            await asyncio.sleep(60 * 60)
