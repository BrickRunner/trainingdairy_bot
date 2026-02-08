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
    # Берем абсолютное значение числа для склонения
    number = abs(number)
    n = int(number)

    # Определяем падеж из словаря или используем базовые формы
    if isinstance(forms, dict):
        case_forms = forms.get(case, forms.get('nominative', ('', '', '')))
    else:
        case_forms = forms

    # Правила склонения для русского языка:
    # 1, 21, 31... - первая форма (1 километр, 21 километр)
    if n % 10 == 1 and n % 100 != 11:
        return case_forms[0]
    # 2-4, 22-24, 32-34... - вторая форма (2 километра, 22 километра)
    elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        return case_forms[1]
    # 5-20, 25-30... - третья форма (5 километров, 11 километров)
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
    # Международный коэффициент: 1 км = 0.621371 миль
    return km * 0.621371


def miles_to_km(miles: float) -> float:
    """
    Конвертирует мили в километры

    Args:
        miles: Расстояние в милях

    Returns:
        Расстояние в километрах
    """
    # Обратная конвертация: 1 миля = 1.60934 км
    return miles / 0.621371


def kg_to_lbs(kg: float) -> float:
    """
    Конвертирует килограммы в фунты

    Args:
        kg: Вес в килограммах

    Returns:
        Вес в фунтах
    """
    # Международный коэффициент: 1 кг = 2.20462 фунта
    return kg * 2.20462


def lbs_to_kg(lbs: float) -> float:
    """
    Конвертирует фунты в килограммы

    Args:
        lbs: Вес в фунтах

    Returns:
        Вес в килограммах
    """
    # Обратная конвертация: 1 фунт = 0.453592 кг
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
    # Формы слова для разных падежей (русский язык)
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

    # Если пользователь выбрал мили, конвертируем и форматируем
    if distance_unit == 'мили':
        distance = km_to_miles(distance_km)
        unit = pluralize(distance, miles_forms, case)
        return f"{distance:.1f} {unit}"
    # Иначе оставляем километры
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
    # Для плавания темп измеряется на 100 метров или 100 ярдов
    if training_type == 'плавание':
        if distance_unit == 'мили':
            # Конвертируем км в ярды (1 км = 1093.61 ярдов)
            distance_in_yards = distance_km * 1093.61
            # Считаем темп на 100 ярдов
            seconds_per_100yards = (total_seconds / distance_in_yards) * 100
            pace_minutes = int(seconds_per_100yards // 60)
            pace_seconds = int(seconds_per_100yards % 60)
            return f"{pace_minutes}:{pace_seconds:02d}", "мин/100ярд"
        else:
            # Конвертируем км в метры
            distance_in_meters = distance_km * 1000
            # Считаем темп на 100 метров
            seconds_per_100m = (total_seconds / distance_in_meters) * 100
            pace_minutes = int(seconds_per_100m // 60)
            pace_seconds = int(seconds_per_100m % 60)
            return f"{pace_minutes}:{pace_seconds:02d}", "мин/100м"

    # Для велотренировки показываем среднюю скорость (км/ч или миль/ч)
    elif training_type == 'велотренировка':
        hours_total = total_seconds / 3600

        if distance_unit == 'мили':
            # Считаем скорость в милях в час
            distance = km_to_miles(distance_km)
            avg_speed = distance / hours_total
            return f"{avg_speed:.1f}", "миль/ч"
        else:
            # Считаем скорость в км/ч
            avg_speed = distance_km / hours_total
            return f"{avg_speed:.1f}", "км/ч"

    # Для бега и других видов показываем темп (мин/км или мин/миля)
    else:
        total_minutes = total_seconds / 60

        if distance_unit == 'мили':
            # Считаем темп на милю
            distance = km_to_miles(distance_km)
            avg_pace_minutes = total_minutes / distance
            pace_minutes = int(avg_pace_minutes)
            pace_seconds = int((avg_pace_minutes - pace_minutes) * 60)
            return f"{pace_minutes}:{pace_seconds:02d}", "мин/миля"
        else:
            # Считаем темп на километр
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
    # Для миль показываем дополнительно ярды
    if distance_unit == 'мили':
        distance_miles = km_to_miles(distance_km)
        # 1 миля = 1760 ярдов
        distance_yards = distance_miles * 1760
        unit_miles = pluralize(distance_miles, ('миля', 'мили', 'миль'))
        unit_yards = pluralize(distance_yards, ('ярд', 'ярда', 'ярдов'))
        return f"{distance_miles:.1f} {unit_miles} ({int(distance_yards)} {unit_yards})"
    # Для километров показываем дополнительно метры
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
    # Формы слова для разных падежей
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

    # Форматируем с правильным склонением
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
    # Получаем настройки пользователя из БД
    from database.queries import get_user_settings

    settings = await get_user_settings(user_id)
    # Извлекаем предпочтительную единицу измерения
    distance_unit = settings.get('distance_unit', 'км') if settings else 'км'

    # Форматируем с учетом настроек
    return format_distance(distance_km, distance_unit)


def convert_distance_name(distance_name: str, target_unit: str = 'км') -> str:
    """
    Конвертировать комплексные названия дистанций в другие единицы измерения

    Args:
        distance_name: Название дистанции (например, "500м плавание + 3000м бег")
        target_unit: Целевая единица измерения ('км' или 'мили')

    Returns:
        Сконвертированное название дистанции

    Examples:
        "500м плавание + 3000м бег" (км) -> "500м плавание + 3000м бег"
        "500м плавание + 3000м бег" (мили) -> "547 ярдов плавание + 1.9 мили бег"
        "10 км" (км) -> "10 км"
        "10 км" (мили) -> "6.2 мили"
    """
    import re

    # Если целевая единица - км, ничего не меняем
    if target_unit == 'км' or not distance_name:
        return distance_name

    # Заменяем запятые на точки для корректного парсинга
    distance_name = re.sub(r'(\d+),(\d+)', r'\1.\2', distance_name)

    # Паттерн для поиска дистанций (км, м, метр и т.д.)
    pattern = r'(\d+(?:\.\d+)?)\s*(км|м|метр|метра|метров|километр|километра|километров)(?![а-яё])'

    def replace_distance(match):
        """Функция замены для re.sub - конвертирует каждое найденное расстояние"""
        value_str = match.group(1)
        value = float(value_str)
        unit = match.group(2).lower()

        # Определяем, это км или метры
        if unit == 'км' or 'километр' in unit:
            km_value = value
        else:
            km_value = value / 1000

        # Для дистанций >= 1 км показываем в милях
        if km_value >= 1.0:
            miles = km_to_miles(km_value)
            # Округляем целые мили (например, 10.0 миль вместо 10.1)
            if abs(miles - round(miles)) < 0.01:
                formatted_miles = str(int(round(miles)))
            else:
                formatted_miles = f"{miles:.1f}"
            miles_word = pluralize(miles, ('миля', 'мили', 'миль'))
            return f"{formatted_miles} {miles_word}"
        # Для дистанций < 1 км показываем в ярдах
        else:
            yards = km_value * 1093.61
            yards_word = pluralize(yards, ('ярд', 'ярда', 'ярдов'))
            return f"{int(round(yards))} {yards_word}"

    # Заменяем все найденные дистанции
    converted = re.sub(pattern, replace_distance, distance_name, flags=re.IGNORECASE)
    return converted


async def convert_distance_name_for_user(distance_name: str, user_id: int) -> str:
    """
    Конвертировать название дистанции согласно настройкам пользователя
    Если конвертация не удалась, возвращает оригинальное название

    Args:
        distance_name: Название дистанции
        user_id: ID пользователя

    Returns:
        Сконвертированное название дистанции или оригинал при ошибке
    """
    try:
        # Получаем настройки пользователя
        from database.queries import get_user_settings

        settings = await get_user_settings(user_id)
        distance_unit = settings.get('distance_unit', 'км') if settings else 'км'

        # Конвертируем с учетом настроек
        return convert_distance_name(distance_name, distance_unit)
    except Exception:
        # При любой ошибке возвращаем оригинал
        return distance_name


def safe_convert_distance_name(distance_name: str, distance_unit: str = 'км') -> str:
    """
    Безопасная конвертация названия дистанции
    Если конвертация не удалась, возвращает оригинальное название

    Args:
        distance_name: Название дистанции
        distance_unit: Единица измерения ('км' или 'мили')

    Returns:
        Сконвертированное название дистанции или оригинал при ошибке
    """
    try:
        # Пытаемся сконвертировать
        return convert_distance_name(distance_name, distance_unit)
    except Exception:
        # При любой ошибке возвращаем оригинал
        return distance_name
