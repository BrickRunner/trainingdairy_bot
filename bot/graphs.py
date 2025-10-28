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

            # Безопасное получение дистанции
            distance_value = w.get('distance') or w.get('calculated_volume') or 0.0
            distance = float(distance_value) if distance_value is not None else 0.0
            grouped_data[group_key]['distance'] += distance
            grouped_data[group_key]['types'][w['type']] += 1
            
            logger.debug(f"Обработка тренировки: {w['type']}, период: {group_key}, дистанция: {distance}")

        # Используем все периоды (включая пустые)
        periods = all_periods
        logger.info(f"Периоды для отображения: {periods}")

        # Форматируем подписи для оси X
        period_labels = [date_formatter(p) for p in periods]

        # Создаём единую фигуру с тремя подграфиками
        # Размещаем графики вертикально (3 строки, 1 столбец)
        fig = plt.figure(figsize=(12, 16))

        # График 1: Усилия (линейный график) + среднее значение
        ax1 = plt.subplot(3, 1, 1)
        
        # Заполняем все периоды, включая пустые (0)
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

        # График 2: Километраж (столбчатая диаграмма) + среднее значение
        ax2 = plt.subplot(3, 1, 2)

        # Получаем дистанции в км из БД
        period_distances_km = [grouped_data[period]['distance'] for period in periods]

        # Конвертируем в единицы пользователя если нужно
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

        # График 3: Круговая диаграмма типов тренировок
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

        # Настраиваем отступы между графиками
        plt.tight_layout(pad=3.0)
        
        # Сохраняем в BytesIO
        combined_img = io.BytesIO()
        fig.savefig(combined_img, format='png', dpi=150, bbox_inches='tight')
        combined_img.seek(0)
        plt.close(fig)
        
        logger.info("Объединенный график успешно создан")
        return combined_img

    except Exception as e:
        logger.error(f"Ошибка при создании графиков: {str(e)}", exc_info=True)
        return None