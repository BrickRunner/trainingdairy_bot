"""
Модуль для работы с уровнями пользователей
"""

from typing import Dict, Tuple
from datetime import datetime, timedelta


LEVELS = {
    'новичок': {'min': 0, 'max': 2, 'emoji': '🌱'},
    'любитель': {'min': 3, 'max': 4, 'emoji': '💪'},
    'профи': {'min': 5, 'max': 5, 'emoji': '🏃'},
    'элитный': {'min': 6, 'max': 100, 'emoji': '⭐'}  
}

LEVEL_RETENTION_WEEKS = 3


def get_level_by_avg_trainings(trainings_this_week: float) -> str:
    """
    Определить уровень пользователя на основе количества тренировок за текущую неделю

    Args:
        trainings_this_week: Количество тренировок за текущую неделю

    Returns:
        Название уровня
    """
    for level_name, level_data in LEVELS.items():
        if level_data['min'] <= trainings_this_week <= level_data['max']:
            return level_name

    return 'новичок'


def get_level_emoji(level_name: str) -> str:
    """
    Получить эмодзи для уровня

    Args:
        level_name: Название уровня

    Returns:
        Эмодзи уровня
    """
    return LEVELS.get(level_name, {}).get('emoji', '🌱')


def get_level_info(level_name: str) -> Dict[str, any]:
    """
    Получить информацию об уровне

    Args:
        level_name: Название уровня

    Returns:
        Словарь с информацией об уровне
    """
    level_data = LEVELS.get(level_name, LEVELS['новичок'])

    if level_name == 'элитный':
        trainings_range = "6-7+ тренировок/неделю"
    elif level_data['min'] == level_data['max']:
        trainings_range = f"{level_data['min']} тренировок/неделю"
    else:
        trainings_range = f"{level_data['min']}-{level_data['max']} тренировок/неделю"

    return {
        'name': level_name,
        'emoji': level_data['emoji'],
        'trainings_range': trainings_range,
        'min': level_data['min'],
        'max': level_data['max']
    }


def calculate_avg_trainings_per_week(total_trainings: int, total_weeks: int) -> float:
    """
    Рассчитать среднее количество тренировок в неделю

    Args:
        total_trainings: Общее количество тренировок
        total_weeks: Общее количество недель

    Returns:
        Среднее количество тренировок в неделю
    """
    if total_weeks <= 0:
        return 0.0
    return round(total_trainings / total_weeks, 2)


def should_downgrade_level(last_training_date: datetime, current_level: str) -> Tuple[bool, str]:
    """
    Проверить, нужно ли понизить уровень пользователя из-за отсутствия активности

    Args:
        last_training_date: Дата последней тренировки
        current_level: Текущий уровень пользователя

    Returns:
        Кортеж (нужно_понизить, новый_уровень)
    """
    if current_level == 'новичок':
        return False, current_level

    weeks_since_last = (datetime.now() - last_training_date).days / 7

    if weeks_since_last > LEVEL_RETENTION_WEEKS:
        levels_list = ['новичок', 'любитель', 'профи', 'элитный']
        current_index = levels_list.index(current_level)

        if current_index > 0:
            new_level = levels_list[current_index - 1]
            return True, new_level

    return False, current_level


def get_next_level_info(current_level: str, current_avg: float) -> Dict[str, any]:
    """
    Получить информацию о следующем уровне и прогрессе

    Args:
        current_level: Текущий уровень
        current_avg: Текущее среднее количество тренировок в неделю

    Returns:
        Словарь с информацией о следующем уровне
    """
    levels_list = ['новичок', 'любитель', 'профи', 'элитный']

    try:
        current_index = levels_list.index(current_level)
    except ValueError:
        current_index = 0

    if current_index >= len(levels_list) - 1:
        return {
            'has_next': False,
            'next_level': None,
            'trainings_needed': 0
        }

    next_level_name = levels_list[current_index + 1]
    next_level_data = LEVELS[next_level_name]
    trainings_needed = next_level_data['min'] - current_avg

    return {
        'has_next': True,
        'next_level': next_level_name,
        'next_level_emoji': next_level_data['emoji'],
        'trainings_needed': max(0, trainings_needed)
    }


def get_all_levels_info() -> list:
    """
    Получить информацию о всех уровнях

    Returns:
        Список словарей с информацией о всех уровнях
    """
    levels_list = ['новичок', 'любитель', 'профи', 'элитный']
    return [get_level_info(level) for level in levels_list]
