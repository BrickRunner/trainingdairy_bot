"""
Утилита для форматирования и нормализации времени результатов
"""
import re
from typing import Optional


def normalize_time(time_str: str) -> str:
    """
    Нормализовать формат времени, убирая ведущие нули из часов

    Args:
        time_str: Время в формате HH:MM:SS или MM:SS или H:MM:SS

    Returns:
        Нормализованное время без ведущих нулей в часах
        Примеры:
        - "00:40:30" -> "40:30"
        - "01:23:45" -> "1:23:45"
        - "10:15:30" -> "10:15:30"
        - "45:30" -> "45:30" (без изменений)
    """
    if not time_str or not isinstance(time_str, str):
        return time_str

    time_str = time_str.strip()

    # Проверяем формат HH:MM:SS
    match = re.match(r'^(\d{1,2}):(\d{2}):(\d{2})$', time_str)
    if match:
        hours, minutes, seconds = match.groups()
        hours_int = int(hours)
        minutes_int = int(minutes)

        # Если часы = 0, возвращаем MM:SS без ведущих нулей в минутах
        if hours_int == 0:
            return f"{minutes_int}:{seconds}"

        # Убираем ведущий ноль из часов, оставляем минуты и секунды с ведущими нулями
        return f"{hours_int}:{minutes}:{seconds}"

    # Проверяем формат MM:SS (оставляем без изменений)
    match = re.match(r'^(\d{1,2}):(\d{2})$', time_str)
    if match:
        return time_str

    # Если формат не распознан, возвращаем как есть
    return time_str


def validate_time_format(time_str: str) -> bool:
    """
    Проверить корректность формата времени

    Args:
        time_str: Строка со временем

    Returns:
        True если формат корректен
    """
    if not time_str or not isinstance(time_str, str):
        return False

    # Допустимые форматы: HH:MM:SS или MM:SS
    return bool(re.match(r'^\d{1,2}:\d{2}(:\d{2})?$', time_str.strip()))


def parse_time_to_seconds(time_str: str) -> Optional[int]:
    """
    Преобразовать время в секунды

    Args:
        time_str: Время в формате HH:MM:SS или MM:SS

    Returns:
        Количество секунд или None при ошибке
    """
    if not validate_time_format(time_str):
        return None

    time_str = time_str.strip()
    parts = time_str.split(':')

    try:
        if len(parts) == 3:
            # HH:MM:SS
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:
            # MM:SS
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
    except ValueError:
        return None

    return None


def seconds_to_time_str(seconds: int) -> str:
    """
    Преобразовать секунды в строку времени

    Args:
        seconds: Количество секунд

    Returns:
        Строка в формате H:MM:SS или MM:SS
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"
