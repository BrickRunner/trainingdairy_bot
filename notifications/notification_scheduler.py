# notification_scheduler.py (добавил форматирование дат в сообщениях, если нужно; но здесь даты в отчётах не отображаются явно, так что без изменений)
"""
Система уведомлений для ежедневных напоминаний, 
поздравлений с днём рождения и недельных отчетов
"""

import asyncio
from datetime import datetime, timedelta
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
    """
    import aiosqlite
    import os
    
    DB_PATH = os.getenv('DB_PATH', 'database.sqlite')
    
    current_time = datetime.now().strftime('%H:%M')
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Находим пользователей с установленным временем напоминания
        async with db.execute(
            """
            SELECT user_id, name, daily_pulse_weight_time 
            FROM user_settings 
            WHERE daily_pulse_weight_time = ?
            """,
            (current_time,)
        ) as cursor:
            rows = await cursor.fetchall()
            
            for row in rows:
                user_id = row['user_id']
                name = row['name'] or "друг"
                
                reminder_message = (
                    f"⏰ **Ежедневное напоминание**\n\n"
                    f"Привет, {name}! 👋\n\n"
                    "Не забудь записать сегодня:\n"
                    "💓 Пульс в покое\n"
                    "⚖️ Текущий вес\n\n"
                    "Это поможет отслеживать твой прогресс! 📊"
                )
                
                try:
                    await bot.send_message(user_id, reminder_message, parse_mode="Markdown")
                except Exception as e:
                    print(f"Ошибка отправки напоминания пользователю {user_id}: {e}")


async def send_weekly_reports(bot: Bot):
    """
    Отправка недельных отчётов о тренировках
    Проверяет день недели и время для каждого пользователя
    """
    import aiosqlite
    import os
    
    DB_PATH = os.getenv('DB_PATH', 'database.sqlite')
    
    # Определяем текущий день недели и время
    now = datetime.now()
    current_weekday = now.strftime('%A')  # Английское название дня
    current_time = now.strftime('%H:%M')
    
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
    
    current_weekday_ru = weekday_map.get(current_weekday, 'Понедельник')
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Находим пользователей с подходящим днём и временем отчёта
        async with db.execute(
            """
            SELECT user_id, name, weekly_report_day, weekly_report_time 
            FROM user_settings 
            WHERE weekly_report_day = ? AND weekly_report_time = ?
            """,
            (current_weekday_ru, current_time)
        ) as cursor:
            rows = await cursor.fetchall()
            
            for row in rows:
                user_id = row['user_id']
                name = row['name'] or "друг"
                
                # Получаем статистику за неделю
                stats = await get_training_statistics(user_id, 'week')
                settings = await get_user_settings(user_id)
                
                distance_unit = settings.get('distance_unit', 'км') if settings else 'км'
                
                # Формируем отчёт
                report_message = (
                    f"📊 **Недельный отчёт**\n\n"
                    f"Привет, {name}! 👋\n\n"
                    f"Твои результаты за неделю:\n\n"
                    f"🏃 Тренировок: {stats['total_count']}\n"
                    f"📏 Общий объём: {stats['total_distance']} {distance_unit}\n"
                )
                
                # Добавляем разбивку по типам
                if stats['types_count']:
                    report_message += "\n**По типам тренировок:**\n"
                    for t_type, count in stats['types_count'].items():
                        report_message += f"  • {t_type}: {count}\n"
                
                # Средний уровень усталости
                if stats['avg_fatigue'] > 0:
                    report_message += f"\n😴 Средняя усталость: {stats['avg_fatigue']}/10\n"
                
                # Проверяем выполнение целей
                if settings:
                    weekly_goal = settings.get('weekly_volume_goal')
                    trainings_goal = settings.get('weekly_trainings_goal')
                    
                    if weekly_goal:
                        progress = (stats['total_distance'] / weekly_goal) * 100
                        status = "✅" if progress >= 100 else "📈"
                        report_message += f"\n{status} Цель по объёму: {progress:.0f}% ({stats['total_distance']}/{weekly_goal} {distance_unit})\n"
                    
                    if trainings_goal:
                        progress = (stats['total_count'] / trainings_goal) * 100
                        status = "✅" if progress >= 100 else "📈"
                        report_message += f"{status} Цель по количеству: {progress:.0f}% ({stats['total_count']}/{trainings_goal})\n"
                
                report_message += "\n💪 Продолжай в том же духе!"
                
                try:
                    await bot.send_message(user_id, report_message, parse_mode="Markdown")
                except Exception as e:
                    print(f"Ошибка отправки отчёта пользователю {user_id}: {e}")


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