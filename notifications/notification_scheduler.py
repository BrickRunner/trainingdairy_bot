"""
Система уведомлений для ежедневных напоминаний, 
поздравлений с днём рождения и недельных отчетов
"""

import asyncio
from datetime import datetime, timedelta
import pytz
from aiogram import Bot
from database.queries import (
    get_user_settings,
    get_trainings_by_period,
    get_training_statistics
)


async def check_birthdays(bot: Bot):
    """
    Проверка дней рождения пользователей и отправка поздравлений
    Должна вызываться ежедневно
    """
    import aiosqlite
    import os
    
    DB_PATH = os.getenv('DB_PATH', 'database.sqlite')
    
    today = datetime.now()
    today_str = today.strftime('%m-%d')  
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        async with db.execute(
            """
            SELECT user_id, name, birth_date 
            FROM user_settings 
            WHERE strftime('%m-%d', birth_date) = ?
            """,
            (today_str,)
        ) as cursor:
            rows = await cursor.fetchall()
            
            for row in rows:
                user_id = row['user_id']
                name = row['name'] or "друг"
                birth_date = datetime.strptime(row['birth_date'], '%Y-%m-%d')
                age = today.year - birth_date.year
                
                birthday_message = (
                    f"🎉🎂 **С Днём Рождения, {name}!** 🎂🎉\n\n"
                    f"Поздравляем с {age}-летием! 🎈\n\n"
                    "Желаем тебе:\n"
                    "💪 Новых спортивных достижений\n"
                    "🏆 Личных рекордов\n"
                    "❤️ Здоровья и энергии\n"
                    "🚀 Покорения новых вершин\n\n"
                    "Пусть каждая тренировка приносит радость! 🏃‍♂️"
                )
                
                try:
                    await bot.send_message(user_id, birthday_message, parse_mode="Markdown")
                except Exception as e:
                    print(f"Ошибка отправки поздравления пользователю {user_id}: {e}")


async def send_daily_reminders(bot: Bot):
    """
    Отправка ежедневных напоминаний о вводе пульса и веса
    Проверяет установленное время для каждого пользователя
    Использует timezone-aware datetime для корректной обработки часовых поясов
    """
    import aiosqlite
    import os
    from health.health_keyboards import get_daily_reminder_keyboard

    DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

    utc_now = datetime.now(pytz.UTC)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute(
            """
            SELECT user_id, name, daily_pulse_weight_time, timezone
            FROM user_settings
            WHERE daily_pulse_weight_time IS NOT NULL
            """
        ) as cursor:
            rows = await cursor.fetchall()

            for row in rows:
                user_id = row['user_id']
                name = row['name'] or "друг"
                reminder_time = row['daily_pulse_weight_time']
                user_timezone_str = row['timezone'] or 'Europe/Moscow'

                try:
                    user_tz = pytz.timezone(user_timezone_str)

                    user_now = utc_now.astimezone(user_tz)
                    current_time = user_now.strftime('%H:%M')
                    today = user_now.date()

                    if current_time != reminder_time:
                        continue

                except Exception as e:
                    print(f"Ошибка обработки часового пояса для пользователя {user_id}: {e}")
                    continue

                async with db.execute(
                    """
                    SELECT morning_pulse, weight, sleep_duration
                    FROM health_metrics
                    WHERE user_id = ? AND date = ?
                    """,
                    (user_id, today)
                ) as metrics_cursor:
                    metrics = await metrics_cursor.fetchone()

                missing_metrics = []
                if not metrics or not metrics['morning_pulse']:
                    missing_metrics.append("💗 Утренний пульс")
                if not metrics or not metrics['weight']:
                    missing_metrics.append("⚖️ Вес")
                if not metrics or not metrics['sleep_duration']:
                    missing_metrics.append("😴 Длительность сна")

                if missing_metrics:
                    reminder_message = (
                        f"⏰ <b>Доброе утро, {name}!</b> 👋\n\n"
                        "Время внести данные о здоровье:\n" +
                        "\n".join(missing_metrics) +
                        "\n\n❓ Хочешь внести данные сейчас?"
                    )

                    try:
                        await bot.send_message(
                            user_id,
                            reminder_message,
                            reply_markup=get_daily_reminder_keyboard(),
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        print(f"Ошибка отправки напоминания пользователю {user_id}: {e}")


async def send_weekly_reports(bot: Bot):
    """
    Отправка недельных отчётов о тренировках и здоровье в виде PDF файла
    Проверяет день недели и время для каждого пользователя
    Использует timezone-aware datetime для корректной обработки часовых поясов
    """
    import aiosqlite
    import os
    from aiogram.types import BufferedInputFile
    from bot.pdf_export import create_training_pdf

    DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

    utc_now = datetime.now(pytz.UTC)

    weekday_map = {
        'Monday': 'Понедельник',
        'Tuesday': 'Вторник',
        'Wednesday': 'Среда',
        'Thursday': 'Четверг',
        'Friday': 'Пятница',
        'Saturday': 'Суббота',
        'Sunday': 'Воскресенье'
    }

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute(
            """
            SELECT user_id, name, weekly_report_day, weekly_report_time, timezone
            FROM user_settings
            WHERE weekly_report_day IS NOT NULL AND weekly_report_time IS NOT NULL
            """
        ) as cursor:
            rows = await cursor.fetchall()

            for row in rows:
                user_id = row['user_id']
                name = row['name'] or "друг"
                report_day = row['weekly_report_day']
                report_time = row['weekly_report_time']
                user_timezone_str = row['timezone'] or 'Europe/Moscow'

                try:
                    user_tz = pytz.timezone(user_timezone_str)

                    user_now = utc_now.astimezone(user_tz)
                    current_weekday = user_now.strftime('%A')  
                    current_time = user_now.strftime('%H:%M')
                    current_weekday_ru = weekday_map.get(current_weekday, 'Понедельник')

                    if current_weekday_ru != report_day or current_time != report_time:
                        continue

                except Exception as e:
                    print(f"Ошибка обработки часового пояса для пользователя {user_id}: {e}")
                    continue

                try:
                    end_date = user_now.date()
                    start_date = end_date - timedelta(days=7)

                    trainings = await get_trainings_by_period(user_id, start_date, end_date)

                    if not trainings:
                        print(f"Пользователь {user_id}: нет тренировок за неделю, отчёт не отправлен")
                        continue

                    stats = await get_training_statistics(user_id, start_date, end_date)

                    from utils.date_formatter import DateFormatter, get_user_date_format
                    user_date_format = await get_user_date_format(user_id)
                    start_str = DateFormatter.format_date(start_date.strftime('%Y-%m-%d'), user_date_format)
                    end_str = DateFormatter.format_date(end_date.strftime('%Y-%m-%d'), user_date_format)
                    period_text = f"{start_str} - {end_str}"

                    pdf_buffer = await create_training_pdf(trainings, period_text, stats, user_id)

                    today = user_now.strftime('%Y-%m-%d')
                    filename = f"weekly_report_{today}.pdf"

                    pdf_file = BufferedInputFile(
                        pdf_buffer.read(),
                        filename=filename
                    )

                    await bot.send_document(
                        user_id,
                        pdf_file,
                        caption=f"📊 <b>Недельный отчёт</b>\n\nПривет, {name}! 👋\n\nТвой подробный отчёт за неделю готов!",
                        parse_mode="HTML"
                    )

                except Exception as e:
                    import traceback
                    print(f"Ошибка генерации или отправки отчёта пользователю {user_id}: {e}")
                    traceback.print_exc()


async def send_training_reminders(bot: Bot):
    """
    Отправка напоминаний о тренировках
    Проверяет день недели и время для каждого пользователя
    Использует timezone-aware datetime для корректной обработки часовых поясов
    """
    import aiosqlite
    import os
    import json
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

    utc_now = datetime.now(pytz.UTC)

    weekday_map = {
        'Monday': 'Понедельник',
        'Tuesday': 'Вторник',
        'Wednesday': 'Среда',
        'Thursday': 'Четверг',
        'Friday': 'Пятница',
        'Saturday': 'Суббота',
        'Sunday': 'Воскресенье'
    }

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute(
            """
            SELECT user_id, name, training_reminder_days, training_reminder_time, timezone
            FROM user_settings
            WHERE training_reminders_enabled = 1
            """
        ) as cursor:
            rows = await cursor.fetchall()

            for row in rows:
                user_id = row['user_id']
                name = row['name'] or "друг"
                reminder_days_json = row['training_reminder_days']
                reminder_time = row['training_reminder_time']
                user_timezone_str = row['timezone'] or 'Europe/Moscow'

                try:
                    reminder_days = json.loads(reminder_days_json) if reminder_days_json else []
                except:
                    reminder_days = []

                if not reminder_days or not reminder_time:
                    continue

                try:
                    user_tz = pytz.timezone(user_timezone_str)

                    user_now = utc_now.astimezone(user_tz)
                    current_weekday = user_now.strftime('%A')  
                    current_time = user_now.strftime('%H:%M')
                    current_weekday_ru = weekday_map.get(current_weekday, 'Понедельник')

                    if current_weekday_ru not in reminder_days:
                        continue

                    if current_time != reminder_time:
                        continue

                except Exception as e:
                    print(f"Ошибка обработки часового пояса для пользователя {user_id}: {e}")
                    continue

                today_date = user_now.date()
                async with db.execute(
                    """
                    SELECT COUNT(*) as count
                    FROM trainings
                    WHERE user_id = ? AND date = ?
                    """,
                    (user_id, today_date)
                ) as training_cursor:
                    training_row = await training_cursor.fetchone()
                    trainings_today = training_row['count'] if training_row else 0

                if trainings_today > 0:
                    continue

                reminder_message = (
                    f"🔔 <b>Напоминание, {name}!</b> 👋\n\n"
                    "Не забудь добавить тренировку за сегодня!\n\n"
                    "💪 Каждая тренировка приближает тебя к цели!"
                )

                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="➕ Добавить тренировку", callback_data="quick_add_training")]
                ])

                try:
                    await bot.send_message(
                        user_id,
                        reminder_message,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                except Exception as e:
                    print(f"Ошибка отправки напоминания пользователю {user_id}: {e}")


async def notification_scheduler(bot: Bot):
    """
    Главный планировщик уведомлений
    Запускается при старте бота и работает в фоне
    """
    while True:
        try:
            now = datetime.now()

            if now.hour == 0 and now.minute == 0:
                await check_birthdays(bot)

            await send_daily_reminders(bot)

            await send_weekly_reports(bot)

            await send_training_reminders(bot)

        except Exception as e:
            print(f"Ошибка в планировщике уведомлений: {e}")

        await asyncio.sleep(60)


def start_notification_scheduler(bot: Bot):
    """
    Запуск планировщика уведомлений в фоновом режиме
    Вызывается при старте бота
    """
    asyncio.create_task(notification_scheduler(bot))