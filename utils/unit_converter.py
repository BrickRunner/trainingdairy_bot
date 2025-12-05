"""
Утилиты для конвертации единиц измерения
"""
from typing import Tuple, Optional


def pluralize(number: float, forms: Tuple[str, str, str], case: str = 'nominative') -> str:
    """
    Склоняет слово в зависимости от числа и падежа

    Args:
        number: Число
        forms: Кортеж из трех форм (1, 2, 5) для именительного падежа
               например ('метр', 'метра', 'метров')
               или словарь с падежами:
               {
                   'nominative': ('километр', 'километра', 'километров'),
                   'genitive': ('километра', 'километров', 'километров'),
                   'prepositional': ('километре', 'километрах', 'километрах')
               }
        case: Падеж ('nominative' - именительный, 'genitive' - родительный,
                     'prepositional' - предложный)

    Returns:
        Правильная форма слова
    """
    number = abs(number)
    # Берем целую часть для правильного склонения
    n = int(number)

    # Если forms - словарь, выбираем нужный падеж
    if isinstance(forms, dict):
        case_forms = forms.get(case, forms.get('nominative', ('', '', '')))
    else:
        # Если кортеж - используем его как есть (только для именительного падежа)
        case_forms = forms

    # Правила для русского языка
    if n % 10 == 1 and n % 100 != 11:
        return case_forms[0]
    elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        return case_forms[1]
    else:
        return case_forms[2]


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


def kg_to_lbs(kg: float) -> float:
    """
    Конвертирует килограммы в фунты

    Args:
        kg: Вес в килограммах

    Returns:
        Вес в фунтах
    """
    return kg * 2.20462


def lbs_to_kg(lbs: float) -> float:
    """
    Конвертирует фунты в килограммы

    Args:
        lbs: Вес в фунтах

    Returns:
        Вес в килограммах
    """
    return lbs / 2.20462


def format_distance(distance_km: float, distance_unit: str = 'км', case: str = 'nominative') -> str:
    """
    Форматирует дистанцию в зависимости от единиц измерения

    Args:
        distance_km: Дистанция в километрах (всегда хранится в км в БД)
        distance_unit: Единица измерения ('км' или 'мили')
        case: Падеж ('nominative', 'genitive', 'prepositional')

    Returns:
        Отформатированная строка с дистанцией
    """
    # Словари склонений для каждой единицы
    km_forms = {
        'nominative': ('километр', 'километра', 'километров'),
        'genitive': ('километра', 'километров', 'километров'),
        'prepositional': ('километре', 'километрах', 'километрах')
    }

    miles_forms = {
        'nominative': ('миля', 'мили', 'миль'),
        'genitive': ('мили', 'миль', 'миль'),
        'prepositional': ('миле', 'милях', 'милях')
    }

    if distance_unit == 'мили':
        distance = km_to_miles(distance_km)
        unit = pluralize(distance, miles_forms, case)
        return f"{distance:.1f} {unit}"
    else:
        unit = pluralize(distance_km, km_forms, case)
        return f"{distance_km:.1f} {unit}"


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
        # Для плавания: темп зависит от единиц измерения
        if distance_unit == 'мили':
            # Для миль используем ярды: 1 км = 1093.61 ярдов
            distance_in_yards = distance_km * 1093.61
            seconds_per_100yards = (total_seconds / distance_in_yards) * 100
            pace_minutes = int(seconds_per_100yards // 60)
            pace_seconds = int(seconds_per_100yards % 60)
            return f"{pace_minutes}:{pace_seconds:02d}", "мин/100ярд"
        else:
            # Для километров используем метры
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
        unit_miles = pluralize(distance_miles, ('миля', 'мили', 'миль'))
        unit_yards = pluralize(distance_yards, ('ярд', 'ярда', 'ярдов'))
        return f"{distance_miles:.1f} {unit_miles} ({int(distance_yards)} {unit_yards})"
    else:
        distance_meters = distance_km * 1000
        unit_km = pluralize(distance_km, ('километр', 'километра', 'километров'))
        unit_m = pluralize(distance_meters, ('метр', 'метра', 'метров'))
        return f"{distance_km:.1f} {unit_km} ({int(distance_meters)} {unit_m})"


def format_weight(weight: float, weight_unit: str = 'кг', case: str = 'nominative') -> str:
    """
    Форматирует вес с правильным склонением

    Args:
        weight: Вес (в кг если weight_unit='кг', в фунтах если weight_unit='фунты')
        weight_unit: Единица измерения ('кг' или 'фунты')
        case: Падеж ('nominative', 'genitive', 'prepositional')

    Returns:
        Отформатированная строка с весом
    """
    # Словари склонений
    kg_forms = {
        'nominative': ('килограмм', 'килограмма', 'килограммов'),
        'genitive': ('килограмма', 'килограммов', 'килограммов'),
        'prepositional': ('килограмме', 'килограммах', 'килограммах')
    }

    lbs_forms = {
        'nominative': ('фунт', 'фунта', 'фунтов'),
        'genitive': ('фунта', 'фунтов', 'фунтов'),
        'prepositional': ('фунте', 'фунтах', 'фунтах')
    }

    if weight_unit == 'фунты':
        unit = pluralize(weight, lbs_forms, case)
        return f"{weight:.1f} {unit}"
    else:
        unit = pluralize(weight, kg_forms, case)
        return f"{weight:.1f} {unit}"


async def format_distance_for_user(distance_km: float, user_id: int) -> str:
    """
    Форматировать дистанцию согласно настройкам пользователя

    Args:
        distance_km: Дистанция в километрах
        user_id: ID пользователя

    Returns:
        Отформатированная строка с дистанцией
    """
    from database.queries import get_user_settings

    settings = await get_user_settings(user_id)
    distance_unit = settings.get('distance_unit', 'км') if settings else 'км'

    return format_distance(distance_km, distance_unit)
