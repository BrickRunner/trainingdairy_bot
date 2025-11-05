"""
Утилита для форматирования и нормализации времени результатов
"""
import re
from typing import Optional


def normalize_time(time_str: str) -> str:
    """
    Нормализовать формат времени, убирая ведущие нули из часов

    Args:
        time_str: Время в формате HH:MM:SS.ss или MM:SS.ss или H:M:S и т.д.

    Returns:
        Нормализованное время без ведущих нулей в часах
        Примеры:
        - "00:40:30" -> "40:30"
        - "00:40:30.50" -> "40:30.50"
        - "01:23:45" -> "1:23:45"
        - "2:0:0" -> "2:00:00"
        - "10:15:30" -> "10:15:30"
        - "45:30" -> "45:30" (без изменений)
    """
    if not time_str or not isinstance(time_str, str):
        return time_str

    time_str = time_str.strip()

    # Проверяем формат HH:MM:SS.ss (с сотыми) - теперь разрешаем 1-2 цифры везде
    match = re.match(r'^(\d{1,2}):(\d{1,2}):(\d{1,2})\.(\d{1,2})$', time_str)
    if match:
        hours, minutes, seconds, hundredths = match.groups()
        hours_int = int(hours)
        minutes_int = int(minutes)
        seconds_int = int(seconds)

        # Нормализуем сотые до 2 цифр
        hundredths = hundredths.ljust(2, '0')[:2]

        # Форматируем минуты и секунды с ведущими нулями
        minutes_str = f"{minutes_int:02d}"
        seconds_str = f"{seconds_int:02d}"

        # Если часы = 0, возвращаем MM:SS.ss без ведущих нулей в минутах
        if hours_int == 0:
            return f"{minutes_int}:{seconds_str}.{hundredths}"

        # Убираем ведущий ноль из часов
        return f"{hours_int}:{minutes_str}:{seconds_str}.{hundredths}"

    # Проверяем формат HH:MM:SS (без сотых) - теперь разрешаем 1-2 цифры везде
    match = re.match(r'^(\d{1,2}):(\d{1,2}):(\d{1,2})$', time_str)
    if match:
        hours, minutes, seconds = match.groups()
        hours_int = int(hours)
        minutes_int = int(minutes)
        seconds_int = int(seconds)

        # Форматируем минуты и секунды с ведущими нулями
        minutes_str = f"{minutes_int:02d}"
        seconds_str = f"{seconds_int:02d}"

        # Если часы = 0, возвращаем MM:SS без ведущих нулей в минутах
        if hours_int == 0:
            return f"{minutes_int}:{seconds_str}"

        # Убираем ведущий ноль из часов, оставляем минуты и секунды с ведущими нулями
        return f"{hours_int}:{minutes_str}:{seconds_str}"

    # Проверяем формат MM:SS.ss (с сотыми) - разрешаем 1-2 цифры
    match = re.match(r'^(\d{1,2}):(\d{1,2})\.(\d{1,2})$', time_str)
    if match:
        minutes, seconds, hundredths = match.groups()
        minutes_int = int(minutes)
        seconds_int = int(seconds)

        # Нормализуем сотые до 2 цифр
        hundredths = hundredths.ljust(2, '0')[:2]

        # Форматируем секунды с ведущими нулями
        seconds_str = f"{seconds_int:02d}"

        return f"{minutes_int}:{seconds_str}.{hundredths}"

    # Проверяем формат MM:SS - разрешаем 1-2 цифры
    match = re.match(r'^(\d{1,2}):(\d{1,2})$', time_str)
    if match:
        minutes, seconds = match.groups()
        minutes_int = int(minutes)
        seconds_int = int(seconds)

        # Форматируем секунды с ведущими нулями
        seconds_str = f"{seconds_int:02d}"

        return f"{minutes_int}:{seconds_str}"

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

    # Допустимые форматы: HH:MM:SS.ss, HH:MM:SS, MM:SS.ss, MM:SS, H:M:S, M:S и т.д.
    # Теперь разрешаем любое количество цифр в минутах и секундах
    return bool(re.match(r'^\d{1,2}:\d{1,2}(:\d{1,2})?(\.\d{1,2})?$', time_str.strip()))


def parse_time_to_seconds(time_str: str) -> Optional[float]:
    """
    Преобразовать время в секунды (с учетом сотых)

    Args:
        time_str: Время в формате HH:MM:SS.ss или MM:SS.ss

    Returns:
        Количество секунд (float) или None при ошибке
    """
    if not validate_time_format(time_str):
        return None

    time_str = time_str.strip()

    # Отделяем сотые доли если есть
    hundredths = 0.0
    if '.' in time_str:
        time_str, hundredths_str = time_str.split('.')
        try:
            # Нормализуем к 2 цифрам
            hundredths_str = hundredths_str.ljust(2, '0')[:2]
            hundredths = int(hundredths_str) / 100.0
        except ValueError:
            return None

    parts = time_str.split(':')

    try:
        if len(parts) == 3:
            # HH:MM:SS
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds + hundredths
        elif len(parts) == 2:
            # MM:SS
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds + hundredths
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


def calculate_pace(time_str: str, distance_km: float) -> Optional[str]:
    """
    Рассчитать темп на км

    Args:
        time_str: Время в формате HH:MM:SS или MM:SS
        distance_km: Дистанция в километрах

    Returns:
        Темп в формате MM:SS/км или None при ошибке
    """
    if not time_str or not distance_km or distance_km <= 0:
        return None

    total_seconds = parse_time_to_seconds(time_str)
    if total_seconds is None:
        return None

    pace_seconds = int(total_seconds / distance_km)
    minutes = pace_seconds // 60
    seconds = pace_seconds % 60

    return f"{minutes}:{seconds:02d}"
