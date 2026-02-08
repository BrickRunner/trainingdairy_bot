"""
Модуль для проверки дней рождения и отправки поздравлений
"""

import asyncio
from datetime import datetime, time
import logging
from aiogram import Bot

from database.queries import get_all_users_with_birthdays
from utils.birthday_greetings import get_birthday_greeting_for_user

logger = logging.getLogger(__name__)


async def check_and_send_birthday_greetings(bot: Bot):
    """
    Проверяет дни рождения пользователей и отправляет поздравления

    Args:
        bot: Экземпляр бота для отправки сообщений
    """
    try:
        today = datetime.now()
        current_day = today.day
        current_month = today.month

        logger.info(f"Checking birthdays for {current_day:02d}.{current_month:02d}")

        users_with_birthdays = await get_all_users_with_birthdays()

        if not users_with_birthdays:
            logger.info("No users with birthdays found in database")
            return

        birthday_count = 0

        for user in users_with_birthdays:
            user_id = user['user_id']
            birth_date = user['birth_date']

            if birth_date.day == current_day and birth_date.month == current_month:
                try:
                    greeting = get_birthday_greeting_for_user(user_id)

                    # Вычисляем возраст с учетом того, был ли уже день рождения в этом году
                    age = today.year - birth_date.year
                    if (today.month, today.day) < (birth_date.month, birth_date.day):
                        age -= 1

                    full_message = f"{greeting}\n\n🎂 Тебе исполнилось {age} лет!"

                    await bot.send_message(
                        chat_id=user_id,
                        text=full_message
                    )

                    birthday_count += 1
                    logger.info(f"Birthday greeting sent to user {user_id} (age: {age})")

                except Exception as e:
                    logger.error(f"Failed to send birthday greeting to user {user_id}: {e}")

        if birthday_count > 0:
            logger.info(f"Successfully sent {birthday_count} birthday greetings")
        else:
            logger.info("No birthdays today")

    except Exception as e:
        logger.error(f"Error in check_and_send_birthday_greetings: {e}")


async def schedule_birthday_check(bot: Bot):
    """
    Запускает ежедневную проверку дней рождения в 9:10

    Args:
        bot: Экземпляр бота для отправки сообщений
    """
    logger.info("Birthday checker scheduler started")

    while True:
        try:
            now = datetime.now()
            target_time = time(9, 0)

            from datetime import timedelta
            target_datetime = datetime.combine(now.date(), target_time)

            # Если уже прошло время проверки сегодня, запланируем на завтра
            if now.time() >= target_time:
                target_datetime = datetime.combine(now.date() + timedelta(days=1), target_time)

            delay = (target_datetime - now).total_seconds()

            logger.info(f"Next birthday check scheduled at {target_datetime.strftime('%Y-%m-%d %H:%M:%S')} (in {delay:.0f} seconds)")

            await asyncio.sleep(delay)

            logger.info("Running scheduled birthday check")
            await check_and_send_birthday_greetings(bot)

        except Exception as e:
            logger.error(f"Error in schedule_birthday_check: {e}")
            await asyncio.sleep(3600)
