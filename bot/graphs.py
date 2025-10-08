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

def generate_weekly_graphs(workouts: list) -> tuple:
    """
    Генерирует три графика для тренировок за неделю:
    1. Линейный график усталости по дням с линией среднего значения.
    2. Столбчатая диаграмма километража по дням с линией среднего значения.
    3. Круговая диаграмма с распределением типов тренировок.
    
    Args:
        workouts: Список словарей с тренировками, где каждый словарь содержит
                  поля 'date' (YYYY-MM-DD), 'fatigue_level' (int/float), 'distance' (float), 
                  'calculated_volume' (float), 'type' (str).
    
    Returns:
        Кортеж из трех объектов io.BytesIO (или None, если данных нет):
        (fatigue_img, mileage_img, pie_img) — изображения графиков.
    """
    try:
        logger.info(f"Получено тренировок: {len(workouts)}")
        # Фильтруем тренировки за текущую неделю
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())  # Начало недели (понедельник)
        weekly_workouts = [
            w for w in workouts
            if datetime.strptime(w['date'], '%Y-%m-%d').date() >= week_start
        ]
        logger.info(f"Тренировки за неделю: {len(weekly_workouts)}")

        if not weekly_workouts:
            logger.warning("Нет тренировок за текущую неделю")
            return None, None, None

        # Группируем данные по дням
        daily_data = defaultdict(lambda: {'fatigue': [], 'distance': 0.0, 'types': defaultdict(int)})
        for w in weekly_workouts:
            day = w['date']
            if w.get('fatigue_level') is not None:
                daily_data[day]['fatigue'].append(float(w['fatigue_level']))
            distance = float(w.get('distance', 0.0) or w.get('calculated_volume', 0.0))
            daily_data[day]['distance'] += distance
            daily_data[day]['types'][w['type']] += 1
            logger.debug(f"Обработка тренировки: {w['type']}, дата: {day}, дистанция: {distance}, усталость: {w.get('fatigue_level')}")

        days = sorted(daily_data.keys())
        logger.info(f"Дни с тренировками: {days}")

        # График 1: Усталость по дням (линейный график) + среднее значение
        daily_fatigues = [
            sum(daily_data[day]['fatigue']) / len(daily_data[day]['fatigue'])
            if daily_data[day]['fatigue'] else 0
            for day in days
        ]
        if any(daily_fatigues):  # Проверяем, есть ли ненулевые значения
            fig1, ax1 = plt.subplots(figsize=(8, 5))
            avg_fatigue = sum(daily_fatigues) / len([f for f in daily_fatigues if f > 0]) if any(f > 0 for f in daily_fatigues) else 0
            ax1.plot(days, daily_fatigues, marker='o', color='b', label='Средняя усталость')
            ax1.axhline(y=avg_fatigue, color='r', linestyle='--', label=f'Среднее: {avg_fatigue:.1f}')
            ax1.set_xlabel('День')
            ax1.set_ylabel('Усталость')
            ax1.set_title('Усталость за неделю')
            ax1.legend()
            ax1.tick_params(axis='x', rotation=45)
            plt.tight_layout()
            fatigue_img = io.BytesIO()
            fig1.savefig(fatigue_img, format='png', dpi=150, bbox_inches='tight')
            fatigue_img.seek(0)
            plt.close(fig1)
            logger.info("График усталости создан")
        else:
            fatigue_img = None
            logger.warning("Нет данных для графика усталости")

        # График 2: Километраж по дням (столбчатая диаграмма) + среднее значение
        daily_distances = [daily_data[day]['distance'] for day in days]
        if any(daily_distances):  # Проверяем, есть ли ненулевые значения
            fig2, ax2 = plt.subplots(figsize=(8, 5))
            avg_distance = sum(daily_distances) / len([d for d in daily_distances if d > 0]) if any(d > 0 for d in daily_distances) else 0
            ax2.bar(days, daily_distances, color='g', label='Километраж')
            ax2.axhline(y=avg_distance, color='r', linestyle='--', label=f'Среднее: {avg_distance:.1f} км')
            ax2.set_xlabel('День')
            ax2.set_ylabel('Километраж (км)')
            ax2.set_title('Километраж за неделю')
            ax2.legend()
            ax2.tick_params(axis='x', rotation=45)
            plt.tight_layout()
            mileage_img = io.BytesIO()
            fig2.savefig(mileage_img, format='png', dpi=150, bbox_inches='tight')
            mileage_img.seek(0)
            plt.close(fig2)
            logger.info("График километража создан")
        else:
            mileage_img = None
            logger.warning("Нет данных для графика километража")

        # График 3: Круговая диаграмма типов тренировок
        type_counts = defaultdict(int)
        for day in daily_data.values():
            for t, count in day['types'].items():
                type_counts[t] += count

        if type_counts:
            fig3, ax3 = plt.subplots(figsize=(7, 7))
            labels = list(type_counts.keys())
            sizes = list(type_counts.values())
            ax3.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            ax3.set_title('Распределение типов тренировок')
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
        logger.error(f"Ошибка при создании графиков: {str(e)}")
        return None, None, None