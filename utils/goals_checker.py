"""
Модуль для проверки достижения целей пользователя
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from aiogram import Bot

from database.queries import (
    get_user_settings,
    get_training_statistics,
    get_training_type_goals,
    get_trainings_by_period,
    update_user_setting
)


async def check_weekly_goals(user_id: int, bot: Bot, last_training_type: str = None) -> None:
    """
    Проверить достижение недельных целей пользователя
    Отправляет отдельное уведомление о достижении каждой цели только один раз за неделю
    Также отправляет мотивационные сообщения о прогрессе

    Args:
        user_id: ID пользователя
        bot: Экземпляр бота для отправки сообщений
        last_training_type: Тип последней добавленной тренировки (для фильтрации уведомлений)
    """
    settings = await get_user_settings(user_id)
    if not settings:
        return

    stats = await get_training_statistics(user_id, 'week')
    distance_unit = settings.get('distance_unit', 'км')

    # Формируем ключ текущей недели для отслеживания уведомлений
    today = datetime.now().date()
    current_week = today.strftime('%Y-%W')

    # Получаем историю уже отправленных уведомлений
    goal_notifications_json = settings.get('goal_notifications', '{}')
    try:
        goal_notifications = json.loads(goal_notifications_json) if goal_notifications_json else {}
    except:
        goal_notifications = {}

    week_goals = goal_notifications.get(current_week, {})

    weekly_volume_goal = settings.get('weekly_volume_goal')
    if weekly_volume_goal and last_training_type not in ['силовая', 'интервальная']:
        total_distance = stats['total_distance']
        progress_percent = (total_distance / weekly_volume_goal) * 100 if weekly_volume_goal > 0 else 0

        if progress_percent >= 100 and not week_goals.get('volume'):
            await bot.send_message(
                user_id,
                f"🎉 <b>Поздравляем! Вы достигли цели по недельному объему!</b>\n\n"
                f"📊 Недельный объем: {total_distance:.1f} {distance_unit}\n"
                f"🎯 Цель: {weekly_volume_goal} {distance_unit}\n\n"
                f"💪 Отличная работа! Продолжайте в том же духе!",
                parse_mode="HTML"
            )
            week_goals['volume'] = True
        # Отправляем мотивационные сообщения при достижении промежуточных целей
        elif not week_goals.get('volume'):
            remaining = weekly_volume_goal - total_distance

            # При достижении 80% - мотивируем на финальный рывок
            if 80 <= progress_percent < 100 and not week_goals.get('progress_80'):
                await bot.send_message(
                    user_id,
                    f"🔥 <b>Почти у цели!</b>\n\n"
                    f"Осталось всего <b>{remaining:.1f} {distance_unit}</b> до достижения недельной цели по объёму!\n\n"
                    f"📊 Прогресс: {total_distance:.1f}/{weekly_volume_goal} {distance_unit} ({progress_percent:.0f}%)\n\n"
                    f"💪 Молодец! Ещё немного!",
                    parse_mode="HTML"
                )
                week_goals['progress_80'] = True
            # При достижении 50% - поддерживаем мотивацию
            elif 50 <= progress_percent < 80 and not week_goals.get('progress_50'):
                await bot.send_message(
                    user_id,
                    f"💪 <b>Отличный прогресс!</b>\n\n"
                    f"Вы прошли больше половины пути к цели по объёму!\n\n"
                    f"📊 Прогресс: {total_distance:.1f}/{weekly_volume_goal} {distance_unit} ({progress_percent:.0f}%)\n"
                    f"📉 Осталось: {remaining:.1f} {distance_unit}\n\n"
                    f"🚀 Продолжайте в том же духе!",
                    parse_mode="HTML"
                )
                week_goals['progress_50'] = True

    weekly_count_goal = settings.get('weekly_trainings_goal')
    if weekly_count_goal and stats['total_count'] >= weekly_count_goal and not week_goals.get('count'):
        await bot.send_message(
            user_id,
            f"🎉 <b>Поздравляем! Вы достигли цели по количеству тренировок!</b>\n\n"
            f"🔢 Количество тренировок: {stats['total_count']}\n"
            f"🎯 Цель: {weekly_count_goal}\n\n"
            f"💪 Отличная работа! Продолжайте в том же духе!",
            parse_mode="HTML"
        )
        week_goals['count'] = True

    # Проверяем цели по типам тренировок (бег, плавание и т.д.)
    type_goals = await get_training_type_goals(user_id)
    if type_goals:
        trainings = await get_trainings_by_period(user_id, 'week')

        # Собираем статистику по каждому типу тренировки
        type_stats = {}
        for training in trainings:
            t_type = training['type']

            if t_type not in type_stats:
                type_stats[t_type] = 0

            # Для силовой считаем минуты, для остальных - километры
            if t_type == 'силовая':
                type_stats[t_type] += training.get('duration', 0)
            else:
                if training.get('calculated_volume'):
                    type_stats[t_type] += training['calculated_volume']
                elif training.get('distance'):
                    type_stats[t_type] += training['distance']

        for t_type, goal in type_goals.items():
            current = type_stats.get(t_type, 0)
            goal_key = f'type_{t_type}'

            if current >= goal and not week_goals.get(goal_key):
                if t_type == 'силовая':
                    await bot.send_message(
                        user_id,
                        f"🎉 <b>Поздравляем! Вы достигли цели по типу '{t_type}'!</b>\n\n"
                        f"🏃 {t_type.capitalize()}: {current:.0f} мин\n"
                        f"🎯 Цель: {goal:.0f} мин\n\n"
                        f"💪 Отличная работа! Продолжайте в том же духе!",
                        parse_mode="HTML"
                    )
                else:
                    await bot.send_message(
                        user_id,
                        f"🎉 <b>Поздравляем! Вы достигли цели по типу '{t_type}'!</b>\n\n"
                        f"🏃 {t_type.capitalize()}: {current:.1f} {distance_unit}\n"
                        f"🎯 Цель: {goal} {distance_unit}\n\n"
                        f"💪 Отличная работа! Продолжайте в том же духе!",
                        parse_mode="HTML"
                    )
                week_goals[goal_key] = True

    goal_notifications[current_week] = week_goals

    # Храним только последние 4 недели для экономии места в БД
    weeks_to_keep = sorted(goal_notifications.keys(), reverse=True)[:4]
    goal_notifications = {week: goal_notifications[week] for week in weeks_to_keep}

    await update_user_setting(user_id, 'goal_notifications', json.dumps(goal_notifications))


async def check_weight_goal(user_id: int, current_weight: float, bot: Bot) -> None:
    """
    Проверить достижение целевого веса
    Уведомление отправляется только один раз при достижении цели.

    Args:
        user_id: ID пользователя
        current_weight: Текущий вес пользователя
        bot: Экземпляр бота для отправки сообщений
    """
    import json

    settings = await get_user_settings(user_id)
    if not settings:
        return

    weight_goal = settings.get('weight_goal')
    if not weight_goal:
        return

    weight_unit = settings.get('weight_unit', 'кг')

    current_saved_weight = settings.get('weight')

    if not current_saved_weight:
        return

    goal_notifications_json = settings.get('goal_notifications', '{}')
    try:
        goal_notifications = json.loads(goal_notifications_json) if goal_notifications_json else {}
    except:
        goal_notifications = {}

    if goal_notifications.get('weight_goal_notified'):
        return

    if abs(current_weight - weight_goal) <= 0.5:
        message = (
            f"🎯 **Поздравляем! Вы достигли целевого веса!**\n\n"
            f"⚖️ Целевой вес: {weight_goal} {weight_unit}\n"
            f"⚖️ Текущий вес: {current_weight} {weight_unit}\n\n"
            f"💪 Отличный результат! Теперь главное - поддерживать форму!"
        )

        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode="Markdown"
        )

        goal_notifications['weight_goal_notified'] = True
        await update_user_setting(user_id, 'goal_notifications', json.dumps(goal_notifications))
