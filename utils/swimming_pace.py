"""
Модуль для расчета темпа плавания
"""


def calculate_swimming_pace(distance_km: float, time_seconds: float, distance_unit: str = 'км') -> str:
    """
    Рассчитывает темп плавания на 100 метров или 100 ярдов

    Args:
        distance_km: Дистанция в километрах (всегда в км в БД)
        time_seconds: Время в секундах
        distance_unit: Единица измерения ('км' или 'мили')

    Returns:
        Темп в формате "ММ:СС на 100м" или "ММ:СС на 100ярд"

    Note:
        В плавании темп измеряется:
        - на 100 метров (если единица - километры)
        - на 100 ярдов (если единица - мили)
    """
    if distance_km <= 0:
        return "—"

    if distance_unit == 'мили':
        # Для миль используем ярды: 1 км = 1093.61 ярдов
        distance_in_yards = distance_km * 1093.61
        pace_per_100yards = (time_seconds / distance_in_yards) * 100
        minutes = int(pace_per_100yards // 60)
        seconds = int(pace_per_100yards % 60)
        return f"{minutes:02d}:{seconds:02d} на 100ярд"
    else:
        # Для километров используем метры
        distance_m = distance_km * 1000
        pace_per_100m = (time_seconds / distance_m) * 100
        minutes = int(pace_per_100m // 60)
        seconds = int(pace_per_100m % 60)
        return f"{minutes:02d}:{seconds:02d} на 100м"


def format_swimming_styles(styles: list) -> str:
    """
    Форматирует список стилей плавания для отображения

    Args:
        styles: Список стилей (например, ['freestyle', 'breaststroke'])

    Returns:
        Отформатированная строка со стилями
    """
    if not styles:
        return "—"

    styles_dict = {
        'freestyle': 'Вольный стиль',
        'breaststroke': 'Брасс',
        'butterfly': 'Баттерфляй',
        'backstroke': 'На спине',
        'im': 'Комплекс (IM)'
    }

    formatted = [styles_dict.get(style, style) for style in styles]
    return ", ".join(formatted)


def format_swimming_location(location: str, pool_length: int = None) -> str:
    """
    Форматирует место проведения тренировки

    Args:
        location: Место ('pool' или 'open_water')
        pool_length: Длина бассейна (25 или 50), если место - бассейн

    Returns:
        Отформатированная строка
    """
    if location == 'pool':
        if pool_length:
            return f"Бассейн {pool_length}м"
        return "Бассейн"
    elif location == 'open_water':
        return "Открытая вода"
    return "—"
