# notification_scheduler.py (добавил форматирование дат в сообщениях, если нужно; но здесь даты в отчётах не отображаются явно, так что без изменений)
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
    today_str = today.strftime('%m-%d')  # Формат ММ-ДД
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Находим всех пользователей с днём рождения сегодня
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

    # Получаем текущее UTC время
    utc_now = datetime.now(pytz.UTC)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Получаем всех пользователей с установленным временем напоминания
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
                    # Получаем часовой пояс пользователя
                    user_tz = pytz.timezone(user_timezone_str)

                    # Конвертируем UTC время в часовой пояс пользователя
                    user_now = utc_now.astimezone(user_tz)
                    current_time = user_now.strftime('%H:%M')
                    today = user_now.date()

                    # Проверяем, совпадает ли текущее время с временем напоминания
                    if current_time != reminder_time:
                        continue

                except Exception as e:
                    print(f"Ошибка обработки часового пояса для пользователя {user_id}: {e}")
                    continue

                # Проверяем, какие метрики уже заполнены сегодня
                async with db.execute(
                    """
                    SELECT morning_pulse, weight, sleep_duration
                    FROM health_metrics
                    WHERE user_id = ? AND date = ?
                    """,
                    (user_id, today)
                ) as metrics_cursor:
                    metrics = await metrics_cursor.fetchone()

                # Определяем, что нужно внести
                missing_metrics = []
                if not metrics or not metrics['morning_pulse']:
                    missing_metrics.append("💗 Утренний пульс")
                if not metrics or not metrics['weight']:
                    missing_metrics.append("⚖️ Вес")
                if not metrics or not metrics['sleep_duration']:
                    missing_metrics.append("😴 Длительность сна")

                # Отправляем напоминание только если есть незаполненные метрики
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
    from reports.weekly_report_pdf import generate_weekly_report_pdf

    DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

    # Получаем текущее UTC время
    utc_now = datetime.now(pytz.UTC)

    # Маппинг дней недели
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

        # Получаем всех пользователей с настроенными недельными отчётами
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
                    # Получаем часовой пояс пользователя
                    user_tz = pytz.timezone(user_timezone_str)

                    # Конвертируем UTC время в часовой пояс пользователя
                    user_now = utc_now.astimezone(user_tz)
                    current_weekday = user_now.strftime('%A')  # Английское название дня
                    current_time = user_now.strftime('%H:%M')
                    current_weekday_ru = weekday_map.get(current_weekday, 'Понедельник')

                    # Проверяем, совпадает ли текущий день и время с настройками отчёта
                    if current_weekday_ru != report_day or current_time != report_time:
                        continue

                except Exception as e:
                    print(f"Ошибка обработки часового пояса для пользователя {user_id}: {e}")
                    continue

                # Генерируем PDF отчёт
                try:
                    pdf_buffer = await generate_weekly_report_pdf(user_id)

                    # Формируем имя файла
                    today = user_now.strftime('%Y-%m-%d')
                    filename = f"weekly_report_{today}.pdf"

                    # Отправляем PDF файл
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
                    print(f"Ошибка генерации или отправки отчёта пользователю {user_id}: {e}")


async def notification_scheduler(bot: Bot):
    """
    Главный планировщик уведомлений
    Запускается при старте бота и работает в фоне
    """
    while True:
        try:
            now = datetime.now()
            
            # Проверяем дни рождения в 00:00
            if now.hour == 0 and now.minute == 0:
                await check_birthdays(bot)
            
            # Проверяем ежедневные напоминания каждую минуту
            await send_daily_reminders(bot)
            
            # Проверяем недельные отчёты каждую минуту
            await send_weekly_reports(bot)
            
        except Exception as e:
            print(f"Ошибка в планировщике уведомлений: {e}")
        
        # Ждём 60 секунд до следующей проверки
        await asyncio.sleep(60)


def start_notification_scheduler(bot: Bot):
    """
    Запуск планировщика уведомлений в фоновом режиме
    Вызывается при старте бота
    """
    asyncio.create_task(notification_scheduler(bot))