"""
Утилиты для конвертации единиц измерения
"""
from typing import Tuple, Optional


def km_to_miles(km: float) -> float:
    """
    Конвертирует километры в мили
    
    Args:
        km: Расстояние в километрах
        
    Returns:
        Расстояние в милях
    """
    return km * 0.621371


def miles_to_km(miles: float) -> float:
    """
    Конвертирует мили в километры
    
    Args:
        miles: Расстояние в милях
        
    Returns:
        Расстояние в километрах
    """
    return miles / 0.621371


def format_distance(distance_km: float, distance_unit: str = 'км') -> str:
    """
    Форматирует дистанцию в зависимости от единиц измерения

    Args:
        distance_km: Дистанция в километрах (всегда хранится в км в БД)
        distance_unit: Единица измерения ('км' или 'мили')

    Returns:
        Отформатированная строка с дистанцией
    """
    if distance_unit == 'мили':
        distance = km_to_miles(distance_km)
        return f"{distance:.1f} миль"
    else:
        return f"{distance_km:.1f} км"


def format_pace(distance_km: float, total_seconds: int, 
                distance_unit: str = 'км', training_type: str = 'кросс') -> Tuple[str, str]:
    """
    Форматирует темп в зависимости от типа тренировки и единиц измерения
    
    Args:
        distance_km: Дистанция в километрах
        total_seconds: Общее время в секундах
        distance_unit: Единица измерения дистанции ('км' или 'мили')
        training_type: Тип тренировки
        
    Returns:
        Кортеж (темп, единица_измерения)
    """
    if training_type == 'плавание':
        # Для плавания: мин:сек на 100 метров (не зависит от единиц дистанции)
        distance_in_meters = distance_km * 1000
        seconds_per_100m = (total_seconds / distance_in_meters) * 100
        pace_minutes = int(seconds_per_100m // 60)
        pace_seconds = int(seconds_per_100m % 60)
        return f"{pace_minutes}:{pace_seconds:02d}", "мин/100м"
    
    elif training_type == 'велотренировка':
        # Для велотренировки: средняя скорость
        hours_total = total_seconds / 3600
        
        if distance_unit == 'мили':
            distance = km_to_miles(distance_km)
            avg_speed = distance / hours_total
            return f"{avg_speed:.1f}", "миль/ч"
        else:
            avg_speed = distance_km / hours_total
            return f"{avg_speed:.1f}", "км/ч"
    
    else:
        # Для кросса: мин:сек на км или на милю
        total_minutes = total_seconds / 60
        
        if distance_unit == 'мили':
            distance = km_to_miles(distance_km)
            avg_pace_minutes = total_minutes / distance
            pace_minutes = int(avg_pace_minutes)
            pace_seconds = int((avg_pace_minutes - pace_minutes) * 60)
            return f"{pace_minutes}:{pace_seconds:02d}", "мин/миля"
        else:
            avg_pace_minutes = total_minutes / distance_km
            pace_minutes = int(avg_pace_minutes)
            pace_seconds = int((avg_pace_minutes - pace_minutes) * 60)
            return f"{pace_minutes}:{pace_seconds:02d}", "мин/км"


def format_swimming_distance(distance_km: float, distance_unit: str = 'км') -> str:
    """
    Форматирует дистанцию для плавания (показывает и км/мили и метры/ярды)

    Args:
        distance_km: Дистанция в километрах
        distance_unit: Единица измерения ('км' или 'мили')

    Returns:
        Отформатированная строка с дистанцией
    """
    if distance_unit == 'мили':
        distance_miles = km_to_miles(distance_km)
        distance_yards = distance_miles * 1760
        return f"{distance_miles:.1f} миль ({int(distance_yards)} ярдов)"
    else:
        distance_meters = distance_km * 1000
        return f"{distance_km:.1f} км ({int(distance_meters)} м)"
