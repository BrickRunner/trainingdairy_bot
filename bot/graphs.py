"""
Модуль для генерации графиков тренировок
"""

import os
import tempfile

os.environ['MPLCONFIGDIR'] = tempfile.gettempdir()

import matplotlib
matplotlib.use('Agg')  
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from collections import defaultdict
import io
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MONTH_NAMES_RU = {
    '01': 'Январь', '02': 'Февраль', '03': 'Март', '04': 'Апрель',
    '05': 'Май', '06': 'Июнь', '07': 'Июль', '08': 'Август',
    '09': 'Сентябрь', '10': 'Октябрь', '11': 'Ноябрь', '12': 'Декабрь'
}

def generate_graphs(workouts: list, period: str, days: int, distance_unit: str = 'км') -> io.BytesIO:
    """
    Генерирует объединенный график с тремя подграфиками для тренировок за выбранный период:
    1. Линейный график усилий с линией среднего значения.
    2. Столбчатая диаграмма километража с линией среднего значения.
    3. Круговая диаграмма с распределением типов тренировок.

    Args:
        workouts: Список словарей с тренировками (уже отфильтрованный по периоду)
        period: Название периода ('week', '2weeks', 'month')
        days: Количество дней в периоде (7, 14, 30)
        distance_unit: Единица измерения дистанции ('км' или 'мили')

    Returns:
        Объект io.BytesIO с объединенным изображением всех графиков или None
    """
    try:
        logger.info(f"Получено тренировок: {len(workouts)} за период: {period} ({days} дней)")

        if not workouts:
            logger.warning(f"Нет тренировок за период {period}")
            return None

        today = datetime.now().date()
        
        if period == 'week':
            start_date = today - timedelta(days=today.weekday())
        elif period == '2weeks':
            start_date = today - timedelta(days=today.weekday() + 7)
        elif period == 'month':
            start_date = today.replace(day=1)
        else:
            start_date = today - timedelta(days=today.weekday())
        
        end_date = today

        if days <= 7:  
            group_format = '%Y-%m-%d'
            x_label = 'День'
            title_suffix = 'за неделю'
            date_formatter = lambda d: datetime.strptime(d, '%Y-%m-%d').strftime('%d.%m')
        elif days <= 14:  
            group_format = '%Y-%m-%d'
            x_label = 'День'
            title_suffix = 'за 2 недели'
            date_formatter = lambda d: datetime.strptime(d, '%Y-%m-%d').strftime('%d.%m')
        elif days <= 31:  
            group_format = '%Y-%m-%d'
            x_label = 'День'
            title_suffix = 'за месяц'
            date_formatter = lambda d: datetime.strptime(d, '%Y-%m-%d').strftime('%d.%m')
        else:  
            group_format = '%Y-%m'
            x_label = 'Месяц'
            title_suffix = 'за период'
            date_formatter = lambda d: f"{MONTH_NAMES_RU[d.split('-')[1]]} {d.split('-')[0]}"

        all_periods = []
        if group_format == '%Y-%m-%d':
            current_date = start_date
            while current_date <= end_date:
                all_periods.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)
        else:
            current_date = start_date
            while current_date <= end_date:
                all_periods.append(current_date.strftime('%Y-%m'))
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
        
        logger.info(f"Полный диапазон периодов: {all_periods}")

        grouped_data = defaultdict(lambda: {'fatigue': [], 'distance': 0.0, 'types': defaultdict(int)})
        
        for w in workouts:
            if group_format == '%Y-%m':
                group_key = w['date'][:7]  
            else:
                group_key = w['date']
            
            if w.get('fatigue_level') is not None:
                grouped_data[group_key]['fatigue'].append(float(w['fatigue_level']))

            distance_value = w.get('distance') or w.get('calculated_volume') or 0.0
            distance = float(distance_value) if distance_value is not None else 0.0
            grouped_data[group_key]['distance'] += distance
            grouped_data[group_key]['types'][w['type']] += 1
            
            logger.debug(f"Обработка тренировки: {w['type']}, период: {group_key}, дистанция: {distance}")

        periods = all_periods
        logger.info(f"Периоды для отображения: {periods}")

        period_labels = [date_formatter(p) for p in periods]

        fig = plt.figure(figsize=(12, 16))

        ax1 = plt.subplot(3, 1, 1)
        
        period_fatigues = [
            sum(grouped_data[period]['fatigue']) / len(grouped_data[period]['fatigue'])
            if grouped_data[period]['fatigue'] else 0
            for period in periods
        ]
        
        avg_fatigue = sum(period_fatigues) / len([f for f in period_fatigues if f > 0]) if any(f > 0 for f in period_fatigues) else 0
        ax1.plot(period_labels, period_fatigues, marker='o', color='b', linewidth=2, markersize=6, label='Средний уровень усилий')
        if avg_fatigue > 0:
            ax1.axhline(y=avg_fatigue, color='r', linestyle='--', linewidth=1.5, label=f'Среднее: {avg_fatigue:.1f}')
        ax1.set_xlabel(x_label, fontsize=11)
        ax1.set_ylabel('Усилия', fontsize=11)
        ax1.set_title(f'Усилия {title_suffix}', fontsize=13, fontweight='bold')
        ax1.set_ylim(0, 10.5)
        ax1.legend(fontsize=10)
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)
        logger.info("График усилий создан")

        ax2 = plt.subplot(3, 1, 2)

        period_distances_km = [grouped_data[period]['distance'] for period in periods]

        if distance_unit == 'мили':
            from utils.unit_converter import km_to_miles
            period_distances = [km_to_miles(d) if d > 0 else 0 for d in period_distances_km]
            distance_label = 'Мили'
            unit_text = 'миль'
        else:
            period_distances = period_distances_km
            distance_label = 'Километры'
            unit_text = 'км'

        avg_distance = sum(period_distances) / len([d for d in period_distances if d > 0]) if any(d > 0 for d in period_distances) else 0
        ax2.bar(period_labels, period_distances, color='#2ecc71', alpha=0.8, label=distance_label)
        if avg_distance > 0:
            ax2.axhline(y=avg_distance, color='r', linestyle='--', linewidth=1.5, label=f'Среднее: {avg_distance:.1f} {unit_text}')
        ax2.set_xlabel(x_label, fontsize=11)
        ax2.set_ylabel(f'{distance_label} ({unit_text})', fontsize=11)
        ax2.set_title(f'{distance_label} {title_suffix}', fontsize=13, fontweight='bold')
        ax2.legend(fontsize=10)
        ax2.grid(True, alpha=0.3, axis='y')
        ax2.tick_params(axis='x', rotation=45)
        logger.info(f"График километража создан ({unit_text})")

        ax3 = plt.subplot(3, 1, 3)
        
        type_counts = defaultdict(int)
        for period_data in grouped_data.values():
            for t, count in period_data['types'].items():
                type_counts[t] += count

        if type_counts:
            labels = [t.capitalize() for t in type_counts.keys()]
            sizes = list(type_counts.values())
            colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6']
            
            ax3.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, 
                   colors=colors[:len(labels)], textprops={'fontsize': 11})
            ax3.set_title(f'Распределение типов тренировок {title_suffix}', 
                         fontsize=13, fontweight='bold')
            logger.info("Круговая диаграмма типов тренировок создана")
        else:
            ax3.text(0.5, 0.5, 'Нет данных для отображения', 
                    ha='center', va='center', fontsize=12)
            ax3.set_title(f'Распределение типов тренировок {title_suffix}', 
                         fontsize=13, fontweight='bold')
            logger.warning("Нет данных для круговой диаграммы")

        plt.tight_layout(pad=3.0)
        
        combined_img = io.BytesIO()
        fig.savefig(combined_img, format='png', dpi=150, bbox_inches='tight')
        combined_img.seek(0)
        plt.close(fig)
        
        logger.info("Объединенный график успешно создан")
        return combined_img

    except Exception as e:
        logger.error(f"Ошибка при создании графиков: {str(e)}", exc_info=True)
        return None