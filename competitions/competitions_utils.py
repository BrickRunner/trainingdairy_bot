"""
Утилиты для работы с соревнованиями с учётом настроек пользователя
"""

from typing import Optional, Dict, Any
from datetime import datetime, date
from database.queries import get_user_settings
from utils.unit_converter import format_distance, km_to_miles, miles_to_km
from utils.date_formatter import DateFormatter


async def get_user_distance_unit(user_id: int) -> str:
    """
    Получить единицу измерения дистанции пользователя

    Args:
        user_id: ID пользователя

    Returns:
        'км' или 'мили'
    """
    settings = await get_user_settings(user_id)
    if settings:
        return settings.get('distance_unit', 'км')
    return 'км'


async def format_competition_distance(distance_km: float, user_id: int) -> str:
    """
    Форматировать дистанцию соревнования согласно настройкам пользователя

    Args:
        distance_km: Дистанция в километрах
        user_id: ID пользователя

    Returns:
        Отформатированная строка (например: "42.2 км", "800 м" или "26.2 мили", "880 ярдов")
    """
    distance_unit = await get_user_distance_unit(user_id)

    # Специальные названия дистанций
    if distance_unit == 'км':
        # Для дистанций менее 1 км показываем в метрах
        if distance_km < 1.0:
            distance_meters = int(distance_km * 1000)
            return f"{distance_meters} м"
        elif 42.0 <= distance_km <= 42.3:
            return "Марафон (42.2 км)"
        elif 21.0 <= distance_km <= 21.2:
            return "Полумарафон (21.1 км)"
        elif distance_km == 10:
            return "10 км"
        elif distance_km == 5:
            return "5 км"
        else:
            return f"{distance_km:.1f} км"
    else:
        distance_miles = km_to_miles(distance_km)
        # Для дистанций менее 1 мили показываем в ярдах
        if distance_miles < 1.0:
            distance_yards = int(distance_miles * 1760)
            return f"{distance_yards} ярдов"
        elif 42.0 <= distance_km <= 42.3:
            return f"Марафон ({distance_miles:.1f} миль)"
        elif 21.0 <= distance_km <= 21.2:
            return f"Полумарафон ({distance_miles:.1f} миль)"
        else:
            return f"{distance_miles:.1f} миль"


async def parse_user_distance_input(distance_text: str, user_id: int) -> Optional[float]:
    """
    Парсить ввод дистанции с учётом единиц измерения пользователя

    Args:
        distance_text: Текст с дистанцией
        user_id: ID пользователя

    Returns:
        Дистанция в километрах или None при ошибке
    """
    distance_unit = await get_user_distance_unit(user_id)

    try:
        distance_value = float(distance_text.replace(',', '.'))

        # Конвертируем в км если нужно
        if distance_unit == 'мили':
            distance_km = miles_to_km(distance_value)
        else:
            distance_km = distance_value

        return distance_km
    except ValueError:
        return None


async def format_competition_date(date_str: str, user_id: int) -> str:
    """
    Форматировать дату соревнования согласно настройкам пользователя

    Args:
        date_str: Дата в формате YYYY-MM-DD
        user_id: ID пользователя

    Returns:
        Отформатированная дата согласно настройкам
    """
    settings = await get_user_settings(user_id)
    date_format = settings.get('date_format', 'ДД.ММ.ГГГГ') if settings else 'ДД.ММ.ГГГГ'

    return DateFormatter.format_date(date_str, date_format)


async def parse_user_date_input(date_text: str, user_id: int) -> Optional[date]:
    """
    Парсить ввод даты с учётом формата пользователя

    Args:
        date_text: Текст с датой
        user_id: ID пользователя

    Returns:
        Объект date или None при ошибке
    """
    settings = await get_user_settings(user_id)
    date_format = settings.get('date_format', 'ДД.ММ.ГГГГ') if settings else 'ДД.ММ.ГГГГ'

    return DateFormatter.parse_date(date_text, date_format)


async def get_date_format_description(user_id: int) -> str:
    """
    Получить описание формата даты для пользователя

    Args:
        user_id: ID пользователя

    Returns:
        Описание формата (например: "ДД.ММ.ГГГГ (например, 15.01.2024)")
    """
    settings = await get_user_settings(user_id)
    date_format = settings.get('date_format', 'ДД.ММ.ГГГГ') if settings else 'ДД.ММ.ГГГГ'

    return DateFormatter.get_format_description(date_format)


async def get_distance_unit_name(user_id: int) -> str:
    """
    Получить название единицы дистанции

    Args:
        user_id: ID пользователя

    Returns:
        'км' или 'миль'
    """
    distance_unit = await get_user_distance_unit(user_id)
    return distance_unit if distance_unit == 'км' else 'миль'


def determine_competition_type(distance_km: float) -> str:
    """
    Определить тип соревнования по дистанции

    Args:
        distance_km: Дистанция в километрах

    Returns:
        Тип соревнования
    """
    if distance_km >= 42:
        return "марафон"
    elif distance_km >= 21:
        return "полумарафон"
    elif distance_km >= 10:
        return "забег"
    else:
        return "забег"
