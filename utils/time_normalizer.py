"""
Утилита для нормализации времени в формат ЧЧ:ММ
"""
import re
from typing import Optional, Tuple


def normalize_time(time_str: str) -> Optional[str]:
    """
    Нормализует время в формат ЧЧ:ММ

    Принимает различные форматы:
    - 8:0 -> 08:00
    - 8:30 -> 08:30
    - 08:00 -> 08:00
    - 9 -> 09:00
    - 23:5 -> 23:05

    Args:
        time_str: Строка со временем

    Returns:
        Нормализованное время в формате ЧЧ:ММ или None если формат неверный
    """
    time_str = time_str.strip()

    # Паттерн для времени с двоеточием: 8:0, 08:00, 23:45
    pattern_with_colon = r'^(\d{1,2}):(\d{1,2})$'
    match = re.match(pattern_with_colon, time_str)

    if match:
        hour, minute = match.groups()
        hour_int = int(hour)
        minute_int = int(minute)

        # Проверка валидности
        if hour_int < 0 or hour_int > 23:
            return None
        if minute_int < 0 or minute_int > 59:
            return None

        # Нормализуем к формату ЧЧ:ММ
        return f"{hour_int:02d}:{minute_int:02d}"

    # Паттерн для времени без двоеточия: 8, 9, 23
    pattern_without_colon = r'^(\d{1,2})$'
    match = re.match(pattern_without_colon, time_str)

    if match:
        hour = match.group(1)
        hour_int = int(hour)

        # Проверка валидности
        if hour_int < 0 or hour_int > 23:
            return None

        # Нормализуем к формату ЧЧ:00
        return f"{hour_int:02d}:00"

    return None


def validate_and_normalize_time(time_str: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Валидирует и нормализует время

    Args:
        time_str: Строка со временем

    Returns:
        Кортеж (успех, нормализованное_время, сообщение_об_ошибке)
    """
    normalized = normalize_time(time_str)

    if normalized is None:
        return False, None, "❌ Неверный формат времени. Используйте формат Ч:М, ЧЧ:ММ или просто Ч\n\nПримеры:\n• 8:0\n• 08:00\n• 9\n• 23:30"

    return True, normalized, None
