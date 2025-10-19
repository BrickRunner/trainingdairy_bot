"""
Построение графиков для метрик здоровья
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, date
from typing import List, Dict
import io
import logging

logger = logging.getLogger(__name__)

# Настройка шрифтов для поддержки русского языка
plt.rcParams['font.family'] = 'DejaVu Sans'


async def generate_health_graphs(metrics: List[Dict], days: int) -> io.BytesIO:
    """
    Генерирует графики метрик здоровья

    Args:
        metrics: Список метрик за период
        days: Количество дней для отображения

    Returns:
        BytesIO объект с изображением графиков
    """
    try:
        # Подготовка данных
        dates = []
        pulse_values = []
        weight_values = []
        sleep_values = []

        for metric in metrics:
            metric_date = datetime.strptime(metric['date'], '%Y-%m-%d').date()
            dates.append(metric_date)

            pulse_values.append(metric.get('morning_pulse'))
            weight_values.append(metric.get('weight'))
            sleep_values.append(metric.get('sleep_duration'))

        # Создание фигуры с подграфиками
        fig, axes = plt.subplots(3, 1, figsize=(12, 10))
        fig.suptitle(f'Метрики здоровья за {days} дней', fontsize=16, fontweight='bold')

        # График пульса
        _plot_metric(
            axes[0], dates, pulse_values,
            'Утренний пульс', 'уд/мин',
            '#e74c3c', '💗'
        )

        # График веса
        _plot_metric(
            axes[1], dates, weight_values,
            'Вес', 'кг',
            '#3498db', '⚖️'
        )

        # График сна
        _plot_metric(
            axes[2], dates, sleep_values,
            'Длительность сна', 'часы',
            '#9b59b6', '😴'
        )

        # Настройка отступов
        plt.tight_layout()

        # Сохранение в BytesIO
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)

        return buf

    except Exception as e:
        logger.error(f"Ошибка при генерации графиков здоровья: {e}")
        raise


def _plot_metric(ax, dates, values, title, ylabel, color, emoji):
    """Построение одного графика метрики"""
    # Фильтруем None значения
    valid_data = [(d, v) for d, v in zip(dates, values) if v is not None]

    if not valid_data:
        ax.text(0.5, 0.5, 'Нет данных',
                ha='center', va='center',
                transform=ax.transAxes,
                fontsize=14, color='gray')
        ax.set_title(f'{emoji} {title}', fontsize=12, fontweight='bold')
        return

    valid_dates, valid_values = zip(*valid_data)

    # Построение линии и точек
    ax.plot(valid_dates, valid_values,
            color=color, linewidth=2, marker='o',
            markersize=6, markerfacecolor='white',
            markeredgewidth=2, markeredgecolor=color)

    # Заливка под графиком
    ax.fill_between(valid_dates, valid_values,
                     alpha=0.2, color=color)

    # Добавление значений на точках
    for d, v in zip(valid_dates, valid_values):
        ax.annotate(f'{v:.1f}',
                   xy=(d, v),
                   xytext=(0, 10),
                   textcoords='offset points',
                   ha='center',
                   fontsize=8,
                   bbox=dict(boxstyle='round,pad=0.3',
                            facecolor='white',
                            edgecolor=color,
                            alpha=0.7))

    # Настройка осей
    ax.set_title(f'{emoji} {title}', fontsize=12, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=10)
    ax.grid(True, alpha=0.3, linestyle='--')

    # Форматирование оси X
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(valid_dates)//7)))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    # Добавление средней линии
    avg_value = sum(valid_values) / len(valid_values)
    ax.axhline(y=avg_value, color=color, linestyle='--',
               linewidth=1, alpha=0.5,
               label=f'Среднее: {avg_value:.1f}')
    ax.legend(loc='upper right', fontsize=8)


async def generate_sleep_quality_graph(metrics: List[Dict], days: int) -> io.BytesIO:
    """
    Генерирует график качества сна

    Args:
        metrics: Список метрик за период
        days: Количество дней

    Returns:
        BytesIO объект с изображением графика
    """
    try:
        # Подготовка данных
        dates = []
        duration_values = []
        quality_values = []

        for metric in metrics:
            if metric.get('sleep_duration') or metric.get('sleep_quality'):
                metric_date = datetime.strptime(metric['date'], '%Y-%m-%d').date()
                dates.append(metric_date)
                duration_values.append(metric.get('sleep_duration'))
                quality_values.append(metric.get('sleep_quality'))

        if not dates:
            # Создаем пустой график с сообщением
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'Нет данных о сне',
                   ha='center', va='center',
                   fontsize=16, color='gray')
            ax.axis('off')

            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            plt.close(fig)
            return buf

        # Создание фигуры с двумя осями Y
        fig, ax1 = plt.subplots(figsize=(12, 6))
        fig.suptitle(f'😴 Анализ сна за {days} дней', fontsize=16, fontweight='bold')

        # График длительности сна
        color1 = '#3498db'
        ax1.set_xlabel('Дата', fontsize=11)
        ax1.set_ylabel('Длительность (часы)', color=color1, fontsize=11)

        # Фильтруем None для длительности
        valid_duration = [(d, v) for d, v in zip(dates, duration_values) if v is not None]
        if valid_duration:
            dur_dates, dur_values = zip(*valid_duration)
            line1 = ax1.plot(dur_dates, dur_values,
                           color=color1, linewidth=2,
                           marker='o', markersize=8,
                           label='Длительность сна')
            ax1.tick_params(axis='y', labelcolor=color1)
            ax1.fill_between(dur_dates, dur_values, alpha=0.2, color=color1)

            # Линия рекомендуемой нормы (7-9 часов)
            ax1.axhspan(7, 9, alpha=0.1, color='green', label='Норма (7-9 ч)')

        # График качества сна
        ax2 = ax1.twinx()
        color2 = '#e74c3c'
        ax2.set_ylabel('Качество (1-5)', color=color2, fontsize=11)

        # Фильтруем None для качества
        valid_quality = [(d, v) for d, v in zip(dates, quality_values) if v is not None]
        if valid_quality:
            qual_dates, qual_values = zip(*valid_quality)
            line2 = ax2.plot(qual_dates, qual_values,
                           color=color2, linewidth=2,
                           marker='s', markersize=8,
                           label='Качество сна')
            ax2.tick_params(axis='y', labelcolor=color2)
            ax2.set_ylim(0, 6)

        # Форматирование оси X
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
        ax1.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//7)))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')

        # Сетка
        ax1.grid(True, alpha=0.3, linestyle='--')

        # Легенда
        lines1 = line1 if valid_duration else []
        lines2 = line2 if valid_quality else []
        if lines1 or lines2:
            labels1 = [l.get_label() for l in (lines1 if lines1 else [])]
            labels2 = [l.get_label() for l in (lines2 if lines2 else [])]
            ax1.legend(lines1 + lines2 + [plt.Line2D([0], [0], color='green', alpha=0.3, linewidth=10)],
                      labels1 + labels2 + ['Норма (7-9 ч)'],
                      loc='upper left', fontsize=9)

        plt.tight_layout()

        # Сохранение в BytesIO
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)

        return buf

    except Exception as e:
        logger.error(f"Ошибка при генерации графика сна: {e}")
        raise
