"""
Модуль для отправки уведомлений о достижении целей и мотивационных сообщений
"""
import aiosqlite
import os
from datetime import datetime, timedelta
from aiogram import Bot

from database.queries import get_training_statistics, get_user_settings, update_user_setting


async def check_and_notify_goal_progress(bot: Bot, user_id: int):
    """
    Проверяет прогресс достижения недельных целей и отправляет уведомления

    Args:
        bot: Экземпляр бота для отправки сообщений
        user_id: ID пользователя
    """
    settings = await get_user_settings(user_id)
    if not settings:
        return

    weekly_volume_goal = settings.get('weekly_volume_goal')
    weekly_trainings_goal = settings.get('weekly_trainings_goal')
    distance_unit = settings.get('distance_unit', 'км')

    if not weekly_volume_goal and not weekly_trainings_goal:
        return

    stats = await get_training_statistics(user_id, 'week')
    total_distance = stats['total_distance']
    total_count = stats['total_count']

    today = datetime.now().date()
    current_week = today.strftime('%Y-%W')

    last_notification_week = settings.get('last_goal_notification_week')
    goal_achieved_this_week = (last_notification_week == current_week)

    if weekly_volume_goal and not goal_achieved_this_week:
        progress_percent = (total_distance / weekly_volume_goal) * 100 if weekly_volume_goal > 0 else 0

        if progress_percent >= 100:
            await bot.send_message(
                user_id,
                f"🎉 <b>Поздравляем!</b> 🎉\n\n"
                f"Вы достигли недельной цели по объёму тренировок!\n\n"
                f"🎯 Цель: {weekly_volume_goal} {distance_unit}\n"
                f"✅ Выполнено: {total_distance:.1f} {distance_unit} ({progress_percent:.0f}%)\n\n"
                f"💪 Отличная работа! Продолжайте в том же духе!",
                parse_mode="HTML"
            )
            await update_user_setting(user_id, 'last_goal_notification_week', current_week)
            return  

        remaining = weekly_volume_goal - total_distance

        if 80 <= progress_percent < 100:
            await bot.send_message(
                user_id,
                f"🔥 <b>Почти у цели!</b>\n\n"
                f"Осталось всего <b>{remaining:.1f} {distance_unit}</b> до достижения недельной цели!\n\n"
                f"📊 Прогресс: {total_distance:.1f}/{weekly_volume_goal} {distance_unit} ({progress_percent:.0f}%)\n\n"
                f"💪 Молодец! Ещё немного!",
                parse_mode="HTML"
            )
        elif 50 <= progress_percent < 80:
            await bot.send_message(
                user_id,
                f"💪 <b>Отличный прогресс!</b>\n\n"
                f"Вы прошли больше половины пути к цели!\n\n"
                f"📊 Прогресс: {total_distance:.1f}/{weekly_volume_goal} {distance_unit} ({progress_percent:.0f}%)\n"
                f"📉 Осталось: {remaining:.1f} {distance_unit}\n\n"
                f"🚀 Продолжайте в том же духе!",
                parse_mode="HTML"
            )

    if weekly_trainings_goal and not goal_achieved_this_week:
        trainings_progress = (total_count / weekly_trainings_goal) * 100 if weekly_trainings_goal > 0 else 0

        if trainings_progress >= 100 and (not weekly_volume_goal or progress_percent < 100):
            await bot.send_message(
                user_id,
                f"🎉 <b>Цель по количеству тренировок достигнута!</b>\n\n"
                f"🎯 Цель: {weekly_trainings_goal} тренировок\n"
                f"✅ Выполнено: {total_count} тренировок\n\n"
                f"💪 Отлично! Продолжайте тренироваться!",
                parse_mode="HTML"
            )


async def send_motivational_message_after_training(bot: Bot, user_id: int):
    """
    Отправляет мотивационное сообщение после добавления тренировки
    Учитывает прогресс к недельной цели

    Args:
        bot: Экземпляр бота
        user_id: ID пользователя
    """
    try:
        await check_and_notify_goal_progress(bot, user_id)
    except Exception as e:
        print(f"Ошибка отправки мотивационного сообщения пользователю {user_id}: {e}")
