"""
Модуль для генерации графиков тренировок
"""

import matplotlib
matplotlib.use('Agg')  # Используем Agg backend для серверов
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from collections import defaultdict
import io
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Словарь для перевода месяцев на русский
MONTH_NAMES_RU = {
    '01': 'Январь', '02': 'Февраль', '03': 'Март', '04': 'Апрель',
    '05': 'Май', '06': 'Июнь', '07': 'Июль', '08': 'Август',
    '09': 'Сентябрь', '10': 'Октябрь', '11': 'Ноябрь', '12': 'Декабрь'
}

def generate_graphs(workouts: list, period: str, days: int) -> tuple:
    """
    Генерирует три графика для тренировок за выбранный период:
    1. Линейный график усталости с линией среднего значения.
    2. Столбчатая диаграмма километража с линией среднего значения.
    3. Круговая диаграмма с распределением типов тренировок.
    
    Args:
        workouts: Список словарей с тренировками (уже отфильтрованный по периоду)
        period: Название периода ('week', '2weeks', 'month')
        days: Количество дней в периоде (7, 14, 30)
    
    Returns:
        Кортеж из трех объектов io.BytesIO (или None, если данных нет):
        (fatigue_img, mileage_img, pie_img) — изображения графиков.
    """
    try:
        logger.info(f"Получено тренировок: {len(workouts)} за период: {period} ({days} дней)")

        if not workouts:
            logger.warning(f"Нет тренировок за период {period}")
            return None, None, None

        # Определяем начальную и конечную даты периода
        today = datetime.now().date()
        
        if period == 'week':
            start_date = today - timedelta(days=today.weekday())
        elif period == '2weeks':
            start_date = today - timedelta(days=today.weekday() + 7)
        elif period == 'month':
            start_date = today.replace(day=1)
        else:
            # По умолчанию - неделя
            start_date = today - timedelta(days=today.weekday())
        
        end_date = today

        # Определяем формат группировки данных и заголовки в зависимости от периода
        if days <= 7:  # Неделя - группируем по дням
            group_format = '%Y-%m-%d'
            x_label = 'День'
            title_suffix = 'за неделю'
            date_formatter = lambda d: datetime.strptime(d, '%Y-%m-%d').strftime('%d.%m')
        elif days <= 14:  # 2 недели - группируем по дням
            group_format = '%Y-%m-%d'
            x_label = 'День'
            title_suffix = 'за 2 недели'
            date_formatter = lambda d: datetime.strptime(d, '%Y-%m-%d').strftime('%d.%m')
        elif days <= 31:  # Месяц - группируем по дням
            group_format = '%Y-%m-%d'
            x_label = 'День'
            title_suffix = 'за месяц'
            date_formatter = lambda d: datetime.strptime(d, '%Y-%m-%d').strftime('%d.%m')
        else:  # Более длительный период - группируем по месяцам
            group_format = '%Y-%m'
            x_label = 'Месяц'
            title_suffix = 'за период'
            # Используем русские названия месяцев
            date_formatter = lambda d: f"{MONTH_NAMES_RU[d.split('-')[1]]} {d.split('-')[0]}"

        # Создаём полный список дат/периодов для отображения
        all_periods = []
        if group_format == '%Y-%m-%d':
            # Для дней - создаём список всех дат от start_date до end_date
            current_date = start_date
            while current_date <= end_date:
                all_periods.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)
        else:
            # Для месяцев - создаём список всех месяцев в периоде
            current_date = start_date
            while current_date <= end_date:
                all_periods.append(current_date.strftime('%Y-%m'))
                # Переход к следующему месяцу
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
        
        logger.info(f"Полный диапазон периодов: {all_periods}")

        # Группируем данные из тренировок
        grouped_data = defaultdict(lambda: {'fatigue': [], 'distance': 0.0, 'types': defaultdict(int)})
        
        for w in workouts:
            # Определяем ключ группировки
            if group_format == '%Y-%m':
                # Для года берем год-месяц
                group_key = w['date'][:7]  # YYYY-MM
            else:
                # Для недели и месяца берем полную дату
                group_key = w['date']
            
            if w.get('fatigue_level') is not None:
                grouped_data[group_key]['fatigue'].append(float(w['fatigue_level']))
            
            distance = float(w.get('distance', 0.0) or w.get('calculated_volume', 0.0))
            grouped_data[group_key]['distance'] += distance
            grouped_data[group_key]['types'][w['type']] += 1
            
            logger.debug(f"Обработка тренировки: {w['type']}, период: {group_key}, дистанция: {distance}")

        # Используем все периоды (включая пустые)
        periods = all_periods
        logger.info(f"Периоды для отображения: {periods}")

        # Форматируем подписи для оси X
        period_labels = [date_formatter(p) for p in periods]

        # График 1: Усталость (линейный график) + среднее значение
        # Заполняем все периоды, включая пустые (0)
        period_fatigues = [
            sum(grouped_data[period]['fatigue']) / len(grouped_data[period]['fatigue'])
            if grouped_data[period]['fatigue'] else 0
            for period in periods
        ]
        
        # Создаём график усталости всегда (даже если все значения 0)
        fig1, ax1 = plt.subplots(figsize=(10, 5))
        avg_fatigue = sum(period_fatigues) / len([f for f in period_fatigues if f > 0]) if any(f > 0 for f in period_fatigues) else 0
        ax1.plot(period_labels, period_fatigues, marker='o', color='b', linewidth=2, markersize=6, label='Средняя усталость')
        if avg_fatigue > 0:
            ax1.axhline(y=avg_fatigue, color='r', linestyle='--', linewidth=1.5, label=f'Среднее: {avg_fatigue:.1f}')
        ax1.set_xlabel(x_label, fontsize=11)
        ax1.set_ylabel('Усталость', fontsize=11)
        ax1.set_title(f'Усталость {title_suffix}', fontsize=13, fontweight='bold')
        ax1.set_ylim(0, 10.5)  # Устанавливаем диапазон от 0 до 10
        ax1.legend(fontsize=10)
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)
        plt.tight_layout()
        fatigue_img = io.BytesIO()
        fig1.savefig(fatigue_img, format='png', dpi=150, bbox_inches='tight')
        fatigue_img.seek(0)
        plt.close(fig1)
        logger.info("График усталости создан")

        # График 2: Километраж (столбчатая диаграмма) + среднее значение
        period_distances = [grouped_data[period]['distance'] for period in periods]
        
        # Создаём график километража всегда (даже если все значения 0)
        fig2, ax2 = plt.subplots(figsize=(10, 5))
        avg_distance = sum(period_distances) / len([d for d in period_distances if d > 0]) if any(d > 0 for d in period_distances) else 0
        ax2.bar(period_labels, period_distances, color='#2ecc71', alpha=0.8, label='Километраж')
        if avg_distance > 0:
            ax2.axhline(y=avg_distance, color='r', linestyle='--', linewidth=1.5, label=f'Среднее: {avg_distance:.1f} км')
        ax2.set_xlabel(x_label, fontsize=11)
        ax2.set_ylabel('Километраж (км)', fontsize=11)
        ax2.set_title(f'Километраж {title_suffix}', fontsize=13, fontweight='bold')
        ax2.legend(fontsize=10)
        ax2.grid(True, alpha=0.3, axis='y')
        ax2.tick_params(axis='x', rotation=45)
        plt.tight_layout()
        mileage_img = io.BytesIO()
        fig2.savefig(mileage_img, format='png', dpi=150, bbox_inches='tight')
        mileage_img.seek(0)
        plt.close(fig2)
        logger.info("График километража создан")

        # График 3: Круговая диаграмма типов тренировок
        type_counts = defaultdict(int)
        for period_data in grouped_data.values():
            for t, count in period_data['types'].items():
                type_counts[t] += count

        if type_counts:
            fig3, ax3 = plt.subplots(figsize=(8, 8))
            labels = [t.capitalize() for t in type_counts.keys()]
            sizes = list(type_counts.values())
            colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6']
            
            ax3.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, 
                   colors=colors[:len(labels)], textprops={'fontsize': 11})
            ax3.set_title(f'Распределение типов тренировок {title_suffix}', 
                         fontsize=13, fontweight='bold')
            plt.tight_layout()
            pie_img = io.BytesIO()
            fig3.savefig(pie_img, format='png', dpi=150, bbox_inches='tight')
            pie_img.seek(0)
            plt.close(fig3)
            logger.info("Круговая диаграмма типов тренировок создана")
        else:
            pie_img = None
            logger.warning("Нет данных для круговой диаграммы")

        return fatigue_img, mileage_img, pie_img

    except Exception as e:
        logger.error(f"Ошибка при создании графиков: {str(e)}", exc_info=True)
        return None, None, None