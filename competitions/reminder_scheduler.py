"""
Планировщик напоминаний о соревнованиях
"""

import asyncio
import aiosqlite
import os
import logging
from datetime import datetime, timedelta, date
from typing import Optional

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')
logger = logging.getLogger(__name__)


async def create_reminders_for_competition(user_id: int, competition_id: int, comp_date_str: str):
    """
    Создать напоминания для соревнования

    Args:
        user_id: ID пользователя
        competition_id: ID соревнования
        comp_date_str: Дата соревнования в формате YYYY-MM-DD
    """

    try:
        comp_date = datetime.strptime(comp_date_str, '%Y-%m-%d').date()
        today = date.today()

        reminder_periods = {
            '30days': 30,
            '14days': 14,
            '7days': 7,
            '3days': 3,
            '1day': 1
        }

        async with aiosqlite.connect(DB_PATH) as db:
            for reminder_type, days_before in reminder_periods.items():
                scheduled_date = comp_date - timedelta(days=days_before)

                if scheduled_date >= today:
                    await db.execute(
                        """
                        INSERT OR IGNORE INTO competition_reminders
                        (user_id, competition_id, reminder_type, scheduled_date, sent)
                        VALUES (?, ?, ?, ?, 0)
                        """,
                        (user_id, competition_id, reminder_type, scheduled_date.strftime('%Y-%m-%d'))
                    )

            result_reminder_date = comp_date + timedelta(days=1)
            await db.execute(
                """
                INSERT OR IGNORE INTO competition_reminders
                (user_id, competition_id, reminder_type, scheduled_date, sent)
                VALUES (?, ?, ?, ?, 0)
                """,
                (user_id, competition_id, 'result_input', result_reminder_date.strftime('%Y-%m-%d'))
            )

            await db.commit()

        logger.info(f"Created reminders for user {user_id}, competition {competition_id}")

    except Exception as e:
        logger.error(f"Error creating reminders: {e}")


async def get_pending_reminders(today: Optional[date] = None) -> list:
    """
    Получить напоминания, которые нужно отправить сегодня

    Args:
        today: Дата для проверки (по умолчанию - сегодня)

    Returns:
        Список напоминаний
    """

    if today is None:
        today = date.today()

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute(
            """
            SELECT
                r.id,
                r.user_id,
                r.competition_id,
                r.reminder_type,
                r.scheduled_date,
                c.name as competition_name,
                c.date as competition_date,
                c.type as competition_type,
                cp.distance,
                cp.target_time
            FROM competition_reminders r
            JOIN competitions c ON r.competition_id = c.id
            LEFT JOIN competition_participants cp ON
                r.competition_id = cp.competition_id AND
                r.user_id = cp.user_id
            WHERE r.scheduled_date <= ? AND r.sent = 0
            ORDER BY r.scheduled_date, r.user_id
            """,
            (today.strftime('%Y-%m-%d'),)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def mark_reminder_as_sent(reminder_id: int):
    """
    Отметить напоминание как отправленное

    Args:
        reminder_id: ID напоминания
    """

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            UPDATE competition_reminders
            SET sent = 1, sent_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (reminder_id,)
        )
        await db.commit()


async def send_competition_reminders(bot):
    """
    Отправить все запланированные напоминания (вызывается планировщиком)

    Args:
        bot: Экземпляр бота для отправки сообщений
    """

    try:
        reminders = await get_pending_reminders()

        if not reminders:
            logger.debug("No pending competition reminders")
            return

        logger.info(f"Found {len(reminders)} pending competition reminders")

        for reminder in reminders:
            try:
                await send_single_reminder(bot, reminder)
                await mark_reminder_as_sent(reminder['id'])
                await asyncio.sleep(0.5)  

            except Exception as e:
                logger.error(f"Error sending reminder {reminder['id']}: {e}")

        logger.info(f"Sent {len(reminders)} competition reminders")

    except Exception as e:
        logger.error(f"Error in send_competition_reminders: {e}")


async def send_single_reminder(bot, reminder: dict):
    """
    Отправить одно напоминание

    Args:
        bot: Экземпляр бота
        reminder: Данные напоминания
    """

    user_id = reminder['user_id']
    reminder_type = reminder['reminder_type']
    comp_name = reminder['competition_name']
    comp_date_str = reminder['competition_date']

    comp_date = datetime.strptime(comp_date_str, '%Y-%m-%d').date()
    days_until = (comp_date - date.today()).days

    if reminder_type == 'result_input':
        text = (
            "🏁 <b>КАК ПРОШЛО СОРЕВНОВАНИЕ?</b>\n\n"
            f"Вчера было ваше соревнование:\n"
            f"🏆 <b>{comp_name}</b>\n\n"
            f"Не забудьте добавить свои результаты!\n"
            f"Это поможет отслеживать прогресс."
        )

        from aiogram.utils.keyboard import InlineKeyboardBuilder
        from aiogram.types import InlineKeyboardButton

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="✍️ Добавить результат",
                callback_data=f"comp:add_result:{reminder['competition_id']}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="❌ Не участвовал",
                callback_data=f"comp:didnt_participate:{reminder['competition_id']}"
            )
        )

        await bot.send_message(
            user_id,
            text,
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )

    else:
        day_word = "день" if days_until == 1 else "дня" if 2 <= days_until <= 4 else "дней"

        from utils.date_formatter import get_user_date_format, DateFormatter
        from competitions.competitions_utils import format_competition_distance

        user_date_format = await get_user_date_format(user_id)
        formatted_date = DateFormatter.format_date(comp_date.strftime('%Y-%m-%d'), user_date_format)

        text = (
            f"⏰ <b>НАПОМИНАНИЕ О СОРЕВНОВАНИИ</b>\n\n"
            f"До старта осталось <b>{days_until} {day_word}</b>!\n\n"
            f"🏆 <b>{comp_name}</b>\n"
            f"📅 Дата: {formatted_date}\n"
        )

        if reminder.get('distance'):
            distance_formatted = await format_competition_distance(reminder['distance'], user_id)
            text += f"📏 Дистанция: {distance_formatted}\n"

        if reminder.get('target_time'):
            text += f"🎯 Ваша цель: {reminder['target_time']}\n"

        text += "\n💪 Удачной подготовки!"

        await bot.send_message(user_id, text, parse_mode="HTML")

    logger.info(f"Sent {reminder_type} reminder to user {user_id} for competition {reminder['competition_id']}")


async def schedule_competition_reminders(bot):
    """
    Планировщик проверки напоминаний (запускается раз в день)

    Args:
        bot: Экземпляр бота
    """

    logger.info("Competition reminders scheduler started")

    while True:
        try:
            now = datetime.now()
            if now.hour == 6 and 5 <= now.minute < 10:
                logger.info(f"Sending reminders at {now.strftime('%H:%M')}")
                await send_competition_reminders(bot)

            await asyncio.sleep(300)

        except Exception as e:
            logger.error(f"Error in competition reminders scheduler: {e}")
            await asyncio.sleep(300)
