"""
Модуль для расчёта объёма интервальной тренировки по нумерованным пунктам
"""

import re
from typing import Optional


def calculate_interval_volume(description: str) -> Optional[float]:
    """
    Рассчитывает общий объём интервальной тренировки в километрах
    
    Считает ТОЛЬКО пронумерованные пункты (1. 2. 3. и т.д.)
    Ненумерованные строки игнорируются
    
    Args:
        description: Текстовое описание интервальной тренировки
        
    Returns:
        Общий объём в километрах или None если не удалось распарсить
        
    Example:
        >>> description = '''
        ... 1. Разминка - 3000м
        ... 2. ОРУ + СБУ + 2 ускорения по ~80м
        ...     Работа:
        ... 1. 7 х 500м / 300м - ()
        ... 2. Трусца - 600м
        ... 3. 7 х 60м - многоскоки
        ... 4. Заминка - 600м
        ... '''
        >>> calculate_interval_volume(description)
        10.36  # 3000 + 2×80 + 7×(500+300) + 600 + 7×60 + 600
    """
    
    if not description:
        return None
    
    total_meters = 0
    
    # Разбиваем на строки
    lines = description.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Проверяем, начинается ли строка с номера (1. или 2. и т.д.)
        # Нумерация теперь ОПЦИОНАЛЬНА
        line_without_number = line
        if re.match(r'^\d+\.', line):
            # Есть номер - удаляем его для парсинга
            line_without_number = re.sub(r'^\d+\.\s*', '', line)
        
        line_without_number = line_without_number.lower()
        
        # ВАЖНО: Исключаем строки с многоскоками и прыжковыми упражнениями
        # Если строка содержит ТОЛЬКО упражнения (без беговых отрезков) - пропускаем
        exclude_only_keywords = [
            'многоскок', 'прыж', 'выпрыг', 'запрыг', 'подскок'
        ]
        
        # Если строка содержит исключающее слово И не содержит метры/км - пропускаем
        has_exclude = any(keyword in line_without_number for keyword in exclude_only_keywords)
        has_distance = bool(re.search(r'\d+\s*[мк]', line_without_number))
        
        if has_exclude and not has_distance:
            # Это упражнение без метража - пропускаем
            continue
        
        if has_exclude and has_distance:
            # Есть и упражнение и метры - это прыжки с дистанцией, пропускаем полностью
            continue
        
        # Паттерн 1: "Разминка - 3000м" или "Заминка - 600м" или "Трусца - 400м"
        # Ищем: тире и число с "м" (не перед "/" чтобы не путать с интервалами)
        pattern_dash = r'[-–—]\s*(\d+)\s*м(?!\s*[/])'
        matches_dash = re.findall(pattern_dash, line_without_number)
        if matches_dash:
            for match in matches_dash:
                meters = int(match)
                total_meters += meters
            # Продолжаем парсить строку дальше, может быть ещё что-то
        
        # Паттерн 2: "7 х 500м / 300м" - интервалы работа/отдых
        # Ищем: число × число м / число м
        pattern_intervals = r'(\d+)\s*[хxх×]\s*(\d+)\s*м\s*[/]\s*(\d+)\s*м'
        matches_intervals = re.findall(pattern_intervals, line_without_number)
        if matches_intervals:
            for match in matches_intervals:
                repeats = int(match[0])
                work_meters = int(match[1])
                rest_meters = int(match[2])
                total_meters += repeats * (work_meters + rest_meters)
            continue
        
        # Паттерн 3: "2 ускорения по ~80м" или "6 х 200м" - только работа без отдыха
        # Ищем: число × число м (но не перед "/")
        pattern_work_only = r'(\d+)\s*(?:ускорени[яй]|х|x|х|×)\s*(?:по\s*~?)?(\d+)\s*м(?!\s*/)'
        matches_work = re.findall(pattern_work_only, line_without_number)
        if matches_work:
            for match in matches_work:
                repeats = int(match[0])
                work_meters = int(match[1])
                total_meters += repeats * work_meters
            continue
        
        # Паттерн 4: просто "3000м" в пронумерованной строке
        # Только если не было других паттернов
        # НЕ считаем описания типа "СБУ по 40м:" или "упражнения по 50м"
        if not (matches_dash or matches_intervals or matches_work):
            # Проверяем что это не описание с "по Xм"
            if not re.search(r'\bпо\s+~?\d+\s*м', line_without_number):
                pattern_simple = r'(\d+)\s*м'
                matches_simple = re.findall(pattern_simple, line_without_number)
                if matches_simple:
                    for match in matches_simple:
                        meters = int(match)
                        total_meters += meters
    
    # Конвертируем в километры
    if total_meters > 0:
        total_km = total_meters / 1000
        return round(total_km, 2)
    
    return None


def format_volume_message(volume: Optional[float]) -> str:
    """
    Форматирует сообщение об объёме тренировки
    
    Args:
        volume: Объём в километрах
        
    Returns:
        Отформатированное сообщение
    """
    if volume is None:
        return ""
    
    if volume >= 1:
        return f"📊 Общий объём: {volume} км ({int(volume * 1000)} м)"
    else:
        return f"📊 Общий объём: {int(volume * 1000)} м"


def calculate_average_interval_pace(description: str) -> Optional[str]:
    """
    Рассчитывает средний темп интервалов по результатам в скобках
    
    Считает только отрезки с результатами в формате:
    - (MM:SS) - минуты:секунды, например (3:12)
    - (SS,S) - секунды с десятыми, например (50,2; 51,0)
    
    Например: "6 х 300м / 300м - (50,2; 51,0; 51,0; 49,8; 48,9; 45,2)"
    
    Args:
        description: Текстовое описание интервальной тренировки
        
    Returns:
        Средний темп в формате "MM:SS мин/км" или None если нет результатов
    """
    if not description:
        return None
    
    total_seconds = 0
    total_distance_meters = 0
    count = 0
    
    lines = description.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Вариант 1: Результаты в скобках (несколько повторений)
        # Форматы: (50,2; 51,0) или (28.0-29.0-28.4) или (1:15; 1:14)
        match_intervals = re.search(r'(\d+)\s*[хxх×]\s*(\d+)\s*м.*?\(([\d:;,.\s\-–—]+)\)', line)
        if match_intervals:
            distance = int(match_intervals.group(2))
            results_str = match_intervals.group(3)
            
            # Парсим результаты из скобок
            # Разделители: ":", ".", ",", "-", "–", "—" или ";"
            # Формат: либо MM:SS, либо SS.S (секунды с десятыми)
            results = re.findall(r'(\d+)[:\.,\-–—](\d+)', results_str)
            
            for result in results:
                num1 = int(result[0])
                num2 = int(result[1])
                
                # Определяем формат: если num1 < 20 и разделитель ":", то это MM:SS
                # Иначе это SS.S (секунды с десятыми)
                if ':' in results_str and num1 < 20:
                    # Формат MM:SS
                    time_seconds = num1 * 60 + num2
                else:
                    # Формат SS.S (секунды с десятыми)
                    # num2 - это десятые доли секунды
                    time_seconds = num1 + (num2 / 10)
                
                total_seconds += time_seconds
                total_distance_meters += distance
                count += 1
        
        # Вариант 2: Один результат после тире
        # "2000м - 6:46" или "1000м - 3:12"
        match_single = re.search(r'(\d+)\s*м.*?[-–—]\s*(\d+)[:\.,](\d+)', line)
        if match_single and not match_intervals:  # Если не нашли интервалы
            distance = int(match_single.group(1))
            num1 = int(match_single.group(2))
            num2 = int(match_single.group(3))
            
            # Для одиночных результатов всегда формат MM:SS
            time_seconds = num1 * 60 + num2
            
            total_seconds += time_seconds
            total_distance_meters += distance
            count += 1
    
    # Рассчитываем средний темп
    if count > 0 and total_distance_meters > 0:
        # Средний темп = общее время / общая дистанция (в км)
        total_distance_km = total_distance_meters / 1000
        avg_pace_seconds_per_km = total_seconds / total_distance_km
        
        # Конвертируем в мин:сек
        pace_min = int(avg_pace_seconds_per_km // 60)
        pace_sec = int(avg_pace_seconds_per_km % 60)
        
        return f"{pace_min}:{pace_sec:02d} мин/км"
    
    return None

