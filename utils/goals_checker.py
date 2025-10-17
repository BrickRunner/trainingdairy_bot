"""
Модуль для проверки достижения целей пользователя
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from aiogram import Bot

from database.queries import (
    get_user_settings,
    get_training_statistics,
    get_training_type_goals,
    get_trainings_by_period
)


async def check_weekly_goals(user_id: int, bot: Bot) -> None:
    """
    Проверить достижение недельных целей пользователя

    Args:
        user_id: ID пользователя
        bot: Экземпляр бота для отправки сообщений
    """
    settings = await get_user_settings(user_id)
    if not settings:
        return

    # Получаем статистику за текущую неделю
    stats = await get_training_statistics(user_id, 'week')

    achieved_goals = []

    # 1. Проверка цели по недельному объему
    weekly_volume_goal = settings.get('weekly_volume_goal')
    if weekly_volume_goal and stats['total_distance'] >= weekly_volume_goal:
        distance_unit = settings.get('distance_unit', 'км')
        achieved_goals.append(
            f"📊 Недельный объем: {stats['total_distance']} {distance_unit} "
            f"(цель: {weekly_volume_goal} {distance_unit})"
        )

    # 2. Проверка цели по количеству тренировок
    weekly_count_goal = settings.get('weekly_trainings_goal')
    if weekly_count_goal and stats['total_count'] >= weekly_count_goal:
        achieved_goals.append(
            f"🔢 Количество тренировок: {stats['total_count']} "
            f"(цель: {weekly_count_goal})"
        )

    # 3. Проверка целей по типам тренировок
    type_goals = await get_training_type_goals(user_id)
    if type_goals:
        # Получаем тренировки за неделю для подсчета по типам
        trainings = await get_trainings_by_period(user_id, 'week')

        # Подсчитываем объем/время по типам
        type_stats = {}
        for training in trainings:
            t_type = training['type']

            if t_type not in type_stats:
                type_stats[t_type] = 0

            # Для силовых - считаем минуты, для остальных - дистанцию
            if t_type == 'силовая':
                # duration хранится в минутах
                type_stats[t_type] += training.get('duration', 0)
            else:
                # Используем calculated_volume для интервальных, distance для остальных
                if training.get('calculated_volume'):
                    type_stats[t_type] += training['calculated_volume']
                elif training.get('distance'):
                    type_stats[t_type] += training['distance']

        # Проверяем достижение целей по типам
        distance_unit = settings.get('distance_unit', 'км')
        for t_type, goal in type_goals.items():
            current = type_stats.get(t_type, 0)
            if current >= goal:
                if t_type == 'силовая':
                    achieved_goals.append(
                        f"🏃 {t_type.capitalize()}: {current} мин "
                        f"(цель: {goal} мин)"
                    )
                else:
                    achieved_goals.append(
                        f"🏃 {t_type.capitalize()}: {current} {distance_unit} "
                        f"(цель: {goal} {distance_unit})"
                    )

    # Если есть достигнутые цели - отправляем уведомление
    if achieved_goals:
        message = "🎉 **Поздравляем! Вы достигли своих целей:**\n\n"
        message += "\n".join(achieved_goals)
        message += "\n\n💪 Отличная работа! Продолжайте в том же духе!"

        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode="Markdown"
        )


async def check_weight_goal(user_id: int, current_weight: float, bot: Bot) -> None:
    """
    Проверить достижение целевого веса

    Args:
        user_id: ID пользователя
        current_weight: Текущий вес пользователя
        bot: Экземпляр бота для отправки сообщений
    """
    settings = await get_user_settings(user_id)
    if not settings:
        return

    weight_goal = settings.get('weight_goal')
    if not weight_goal:
        return

    weight_unit = settings.get('weight_unit', 'кг')

    # Определяем направление цели (набор или снижение веса)
    current_saved_weight = settings.get('weight')

    if not current_saved_weight:
        return

    # Проверяем достижение цели (с погрешностью 0.5 кг)
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
