"""
Модуль для генерации графиков для PDF экспорта
"""

import matplotlib
matplotlib.use('Agg')  # Без GUI
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from collections import defaultdict
import io
import logging

logger = logging.getLogger(__name__)

# Настройка matplotlib для поддержки русского языка
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

def get_strftime_fmt(date_format: str) -> str:
    """
    Преобразует шаблон date_format (например, 'DD.MM.YYYY') в strftime-формат (например, '%d.%m.%Y')
    Поддерживает распространенные шаблоны. Добавьте больше, если нужны другие форматы.
    """
    # Заменяем плейсхолдеры на strftime коды
    fmt = date_format.replace('DD', '%d').replace('MM', '%m').replace('YYYY', '%Y').replace('YY', '%y')
    # Для разделителей: поддерживаем ., /, -
    return fmt

def get_short_strftime_fmt(date_format: str) -> str:
    """
    Получает короткий формат без года (например, для 'DD.MM.YYYY' → '%d.%m')
    """
    # Удаляем часть с годом
    if 'YYYY' in date_format:
        short = date_format.split('YYYY')[0].rstrip('.-/')
    elif 'YY' in date_format:
        short = date_format.split('YY')[0].rstrip('.-/')
    else:
        short = date_format
    return get_strftime_fmt(short)

def generate_weekly_stats(trainings: list, date_format: str) -> list:
    """
    Генерирует статистику по неделям
    
    Args:
        trainings: Список тренировок
        date_format: Шаблон формата даты для вывода
        
    Returns:
        Список словарей со статистикой по неделям
    """
    weekly_data = defaultdict(lambda: {'count': 0, 'distance': 0.0, 'trainings': []})
    input_date_fmt = '%Y-%m-%d'  # Фиксированный формат дат из БД
    output_fmt = get_strftime_fmt(date_format)  # Формат для вывода
    
    for training in trainings:
        try:
            date_str = training['date']
            date = datetime.strptime(date_str, input_date_fmt)
            # Получаем номер недели и год
            week_key = date.strftime('%Y-W%W')
            
            weekly_data[week_key]['count'] += 1
            weekly_data[week_key]['trainings'].append(training)
            
            # Добавляем дистанцию
            if training.get('distance'):
                weekly_data[week_key]['distance'] += float(training['distance'])
            elif training.get('calculated_volume'):
                weekly_data[week_key]['distance'] += float(training['calculated_volume'])
        except ValueError as e:
            logger.error(f"Ошибка формата даты в тренировке '{date_str}': {e}")
            continue
    
    # Преобразуем в отсортированный список
    result = []
    for week_key in sorted(weekly_data.keys()):
        data = weekly_data[week_key]
        # Получаем даты начала и конца недели
        year, week = week_key.split('-W')
        # Первый день недели (понедельник)
        first_day = datetime.strptime(f'{year}-W{week}-1', '%Y-W%W-%w')
        last_day = first_day + timedelta(days=6)
        
        # Форматируем week_label согласно date_format
        first_str = first_day.strftime(output_fmt)
        last_str = last_day.strftime(output_fmt)
        week_label = f'{first_str} - {last_str}'
        
        result.append({
            'week_key': week_key,
            'week_label': week_label,
            'count': data['count'],
            'distance': round(data['distance'], 2),
            'trainings': data['trainings']
        })
    
    return result


def create_pdf_graphs(trainings: list, start_date: str, end_date: str, date_format: str) -> io.BytesIO:
    """
    Создает комбинированное изображение с графиками для PDF
    
    Args:
        trainings: Список тренировок
        start_date: Начальная дата (в формате '%Y-%m-%d')
        end_date: Конечная дата (в формате '%Y-%m-%d')
        date_format: Шаблон формата даты для вывода
        
    Returns:
        BytesIO с изображением графиков
    """
    input_date_fmt = '%Y-%m-%d'  # Фиксированный формат из БД
    short_fmt = get_short_strftime_fmt(date_format)  # Короткий формат для осей (без года)
    
    # Создаем фигуру с 3 графиками (1 строка, 3 колонки)
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('Статистика и анализ тренировок', fontsize=20, fontweight='bold')
    
    # Подготовка данных
    dates = []
    fatigue_levels = []
    distances = []
    
    # Данные по типам
    type_counts = defaultdict(int)
    
    for training in trainings:
        try:
            date_str = training['date']
            date = datetime.strptime(date_str, input_date_fmt)
            dates.append(date)
            
            # Усталость
            fatigue_levels.append(training.get('fatigue_level', 0))
            
            # Дистанция
            if training.get('distance'):
                distances.append(float(training['distance']))
            elif training.get('calculated_volume'):
                distances.append(float(training['calculated_volume']))
            else:
                distances.append(0)
            
            # Типы тренировок
            type_counts[training['type']] += 1
        except ValueError as e:
            logger.error(f"Ошибка формата даты в тренировке '{date_str}': {e}")
            continue
    
    # === ГРАФИК 1: Динамика усталости ===
    valid_fatigue = [(d, f) for d, f in zip(dates, fatigue_levels) if f > 0]
    if valid_fatigue:
        f_dates, f_values = zip(*valid_fatigue)
        ax1.plot(f_dates, f_values, marker='o', linewidth=2, markersize=6, color='#e74c3c')
        ax1.set_title('Динамика усталости', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Уровень усталости', fontsize=12)
        ax1.set_ylim(0, 11)
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter(short_fmt))  # Используем короткий формат
        ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    else:
        ax1.text(0.5, 0.5, 'Нет данных об усталости', 
                ha='center', va='center', transform=ax1.transAxes, fontsize=12)
        ax1.set_title('Динамика усталости', fontsize=14, fontweight='bold')
    
    # === ГРАФИК 2: Километраж по тренировкам ===
    valid_distances = [(d, dist) for d, dist in zip(dates, distances) if dist > 0]
    if valid_distances:
        d_dates, d_values = zip(*valid_distances)
        ax2.bar(d_dates, d_values, color='#3498db', alpha=0.7, width=0.8)
        ax2.set_title('Километраж по тренировкам', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Дистанция (км)', fontsize=12)
        ax2.grid(True, alpha=0.3, axis='y')
        ax2.xaxis.set_major_formatter(mdates.DateFormatter(short_fmt))  # Используем короткий формат
        ax2.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
    else:
        ax2.text(0.5, 0.5, 'Нет данных о дистанции', 
                ha='center', va='center', transform=ax2.transAxes, fontsize=12)
        ax2.set_title('Километраж по тренировкам', fontsize=14, fontweight='bold')
    
    # === ГРАФИК 3: Распределение типов тренировок ===
    if type_counts:
        colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6']
        types = list(type_counts.keys())
        counts = list(type_counts.values())
        
        wedges, texts, autotexts = ax3.pie(
            counts, 
            labels=types, 
            autopct='%1.1f%%',
            startangle=90,
            colors=colors[:len(types)]
        )
        ax3.set_title('Распределение типов тренировок', fontsize=14, fontweight='bold')
        
        # Улучшаем читаемость процентов
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(11)
            autotext.set_fontweight('bold')
    else:
        ax3.text(0.5, 0.5, 'Нет данных о типах', 
                ha='center', va='center', transform=ax3.transAxes, fontsize=12)
        ax3.set_title('Распределение типов тренировок', fontsize=14, fontweight='bold')
    
    # Улучшаем компоновку
    plt.tight_layout()
    
    # Сохраняем в BytesIO
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    plt.close()
    
    logger.info(f"Графики для PDF успешно созданы")
    return buffer