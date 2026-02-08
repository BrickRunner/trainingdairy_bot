"""
Модуль для расчета рейтинговых очков пользователей
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta


# Базовые баллы за различные типы тренировок
# Используется для расчета общего рейтинга пользователя
TRAINING_TYPE_POINTS = {
    'беговая': 3,
    'силовая': 2,
    'кросс': 1,
    'велотренировка': 3,
    'плавание': 3,
}

# Дополнительные баллы за каждый час тренировки
POINTS_PER_HOUR = 0.5

# Баллы за призовые места в соревнованиях
COMPETITION_PLACE_POINTS = {
    1: 10,  # 1 место
    2: 7,   # 2 место
    3: 5,   # 3 место
}
# Баллы просто за участие (без призового места)
COMPETITION_PARTICIPATION_POINTS = 2  


def calculate_training_type_points(training_type: str) -> int:
    """
    Рассчитать баллы за тип тренировки

    Args:
        training_type: Тип тренировки

    Returns:
        Количество баллов
    """
    return TRAINING_TYPE_POINTS.get(training_type.lower(), 1)


def calculate_duration_points(duration_minutes: int) -> float:
    """
    Рассчитать баллы за время тренировки

    Args:
        duration_minutes: Длительность тренировки в минутах

    Returns:
        Количество баллов (0.5 за каждый час)
    """
    hours = duration_minutes / 60.0
    return hours * POINTS_PER_HOUR


def calculate_competition_points(place: int) -> int:
    """
    Рассчитать баллы за место в соревновании

    Args:
        place: Место в соревновании (1, 2, 3 или другое)

    Returns:
        Количество баллов
    """
    if place in COMPETITION_PLACE_POINTS:
        return COMPETITION_PLACE_POINTS[place]
    elif place > 0:
        return COMPETITION_PARTICIPATION_POINTS
    return 0


def calculate_training_points(trainings: List[Dict[str, Any]]) -> float:
    """
    Рассчитать общее количество баллов за тренировки

    Args:
        trainings: Список тренировок с полями type и duration

    Returns:
        Общее количество баллов
    """
    total_points = 0.0

    for training in trainings:
        training_type = training.get('type', '')
        duration = training.get('duration', 0)

        if training_type and duration:
            type_points = calculate_training_type_points(training_type)
            duration_points = calculate_duration_points(duration)

            total_points += type_points + duration_points

    return round(total_points, 2)


def calculate_competitions_points(competitions: List[Dict[str, Any]]) -> int:
    """
    Рассчитать общее количество баллов за соревнования

    Args:
        competitions: Список соревнований с полем place

    Returns:
        Общее количество баллов
    """
    total_points = 0

    for competition in competitions:
        place = competition.get('place', 0)
        if place:
            total_points += calculate_competition_points(place)

    return total_points


def calculate_total_points(trainings: List[Dict[str, Any]],
                          competitions: List[Dict[str, Any]]) -> float:
    """
    Рассчитать общее количество баллов пользователя

    Args:
        trainings: Список тренировок
        competitions: Список соревнований

    Returns:
        Общее количество баллов
    """
    training_points = calculate_training_points(trainings)
    competition_points = calculate_competitions_points(competitions)

    return round(training_points + competition_points, 2)


def get_period_dates(period: str) -> tuple:
    """
    Получить даты начала и конца для периода

    Args:
        period: Тип периода ('week', 'month', 'season', 'all')

    Returns:
        Кортеж (start_date, end_date) или (None, None) для 'all'
    """
    import calendar
    today = datetime.now().date()

    if period == 'week':
        # Неделя начинается с понедельника (weekday=0)
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
        return start_date, end_date

    elif period == 'month':
        # Текущий месяц: с 1 числа до последнего дня
        start_date = today.replace(day=1)
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_date = today.replace(day=last_day)
        return start_date, end_date

    elif period == 'season':
        # Сезон = последние 90 дней (~3 месяца)
        start_date = today - timedelta(days=89)
        return start_date, today

    else:
        # Для 'all' возвращаем None - означает весь период
        return None, None


def get_season_name(date: datetime = None) -> str:
    """
    Определить название сезона по дате

    Args:
        date: Дата (по умолчанию - сегодня)

    Returns:
        Название сезона: 'Зима', 'Весна', 'Лето', 'Осень'
    """
    if date is None:
        date = datetime.now()

    month = date.month

    # Определяем сезон по месяцу
    if month in [12, 1, 2]:
        return 'Зима'
    elif month in [3, 4, 5]:
        return 'Весна'
    elif month in [6, 7, 8]:
        return 'Лето'
    else:  # 9, 10, 11
        return 'Осень'
