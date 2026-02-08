"""
Модуль для создания графиков статистики соревнований
"""

import os
import tempfile

os.environ['MPLCONFIGDIR'] = tempfile.gettempdir()

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from typing import List, Dict, Any
from collections import defaultdict
import io
import logging

logger = logging.getLogger(__name__)

plt.rcParams['font.family'] = 'DejaVu Sans'


def _time_to_seconds(time_str: str) -> int:
    """Конвертировать время HH:MM:SS в секунды"""
    if not time_str:
        return 0
    try:
        parts = time_str.split(':')
        if len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        return 0
    except (ValueError, IndexError):
        return 0


def _seconds_to_time(seconds: int) -> str:
    """Конвертировать секунды в формат HH:MM:SS"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


async def generate_competitions_graphs(
    participants: List[Dict[str, Any]],
    stats: Dict[str, Any],
    period_text: str,
    distance_unit: str = 'км'
) -> List[io.BytesIO]:
    """
    Генерирует изображения с графиками для соревнований

    Args:
        participants: Список участий с данными соревнований
        stats: Словарь со статистикой
        period_text: Текстовое описание периода
        distance_unit: Единица измерения дистанции ('км' или 'мили')

    Returns:
        Список BytesIO с изображениями графиков
    """
    try:
        logger.info(f"Генерация графиков для {len(participants)} соревнований")

        buffers = []

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle(f'Статистика соревнований за {period_text}', fontsize=20, fontweight='bold')

        _plot_by_type(ax1, stats)

        _plot_by_distance(ax2, stats, distance_unit)

        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        buffers.append(buf)

        standard_distances = {
            42.195,  
            21.1,    
            10.0,    
            5.0,     
            3.0,     
            1.5,     
            0.8,     
            0.4,     
            0.2,     
            0.1,     
            0.06     
        }

        by_distance = defaultdict(list)
        for p in participants:
            if p.get('status') == 'finished' and p.get('finish_time') and p.get('distance') and p.get('date'):
                distance = p['distance']
                if distance not in standard_distances:
                    continue
                date_obj = datetime.strptime(p['date'], '%Y-%m-%d')
                time_seconds = _time_to_seconds(p['finish_time'])
                if time_seconds > 0:
                    by_distance[distance].append((date_obj, time_seconds))

        distances_with_multiple = [(d, data) for d, data in by_distance.items() if len(data) > 1]
        distances_with_multiple.sort(key=lambda x: x[0], reverse=True)  

        if distances_with_multiple:
            for i in range(0, len(distances_with_multiple), 4):
                num_plots = min(4, len(distances_with_multiple) - i)

                if num_plots == 1:
                    fig, ax = plt.subplots(1, 1, figsize=(14, 6))
                    axes_list = [ax]
                elif num_plots == 2:
                    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
                    axes_list = list(axes)
                else:
                    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
                    axes_list = axes.flatten().tolist()

                fig.suptitle(f'Динамика результатов', fontsize=16, fontweight='bold')

                for j, ax in enumerate(axes_list):
                    idx = i + j
                    if idx < len(distances_with_multiple):
                        distance, data = distances_with_multiple[idx]
                        _plot_single_distance_timeline(ax, distance, data, distance_unit)
                    else:
                        ax.axis('off')

                plt.tight_layout()
                buf = io.BytesIO()
                plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
                buf.seek(0)
                plt.close(fig)
                buffers.append(buf)

        logger.info(f"Графики успешно созданы ({len(buffers)} страниц)")
        return buffers

    except Exception as e:
        logger.error(f"Ошибка при генерации графиков: {e}")
        raise


def _plot_single_distance_timeline(ax, distance: float, data: List[tuple], distance_unit: str = 'км'):
    """График динамики результатов для одной дистанции"""
    from utils.unit_converter import km_to_miles

    data = sorted(data)
    dates, times = zip(*data)

    ax.plot(dates, times, marker='o', linewidth=2, markersize=8, color='#3498db')

    ax.invert_yaxis()

    y_ticks = ax.get_yticks()
    ax.set_yticks(y_ticks)
    ax.set_yticklabels([_seconds_to_time(int(y)) for y in y_ticks])

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%y'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    if distance_unit == 'мили':
        distance_miles = km_to_miles(distance)
        distance_label = f'{distance_miles:.1f} миль'
    else:
        distance_label = f'{distance} км'

    ax.set_title(f'Динамика результатов ({distance_label})', fontsize=14, fontweight='bold')
    ax.set_xlabel('Дата соревнования', fontsize=12)
    ax.set_ylabel('Время финиша', fontsize=12)
    ax.grid(True, alpha=0.3, linestyle='--')


def _plot_by_type(ax, stats: Dict[str, Any]):
    """График распределения по видам спорта"""
    by_type = stats.get('by_type', {})

    if not by_type:
        ax.text(0.5, 0.5, 'Нет данных',
                ha='center', va='center',
                transform=ax.transAxes,
                fontsize=14, color='gray')
        ax.set_title('По видам спорта', fontsize=14, fontweight='bold')
        return

    sorted_types = sorted(by_type.items(), key=lambda x: x[1], reverse=True)
    types, counts = zip(*sorted_types)

    colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']

    bars = ax.bar(range(len(types)), counts, color=colors[:len(types)])

    for bar, count in zip(bars, counts):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(count)}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax.set_xticks(range(len(types)))
    ax.set_xticklabels(types, rotation=45, ha='right')
    ax.set_title('По видам спорта', fontsize=14, fontweight='bold')
    ax.set_ylabel('Количество', fontsize=12)
    ax.grid(True, alpha=0.3, axis='y', linestyle='--')


def _plot_by_distance(ax, stats: Dict[str, Any], distance_unit: str = 'км'):
    """График распределения по дистанциям"""
    from utils.unit_converter import km_to_miles

    by_distance = stats.get('by_distance', {})

    if not by_distance:
        ax.text(0.5, 0.5, 'Нет данных',
                ha='center', va='center',
                transform=ax.transAxes,
                fontsize=14, color='gray')
        ax.set_title('По дистанциям', fontsize=14, fontweight='bold')
        return

    sorted_distances = sorted(by_distance.items(), key=lambda x: x[0])
    distances, counts = zip(*sorted_distances)

    if distance_unit == 'мили':
        distance_labels = [f'{km_to_miles(d):.1f} миль' for d in distances]
    else:
        distance_labels = [f'{d} км' for d in distances]

    colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']

    bars = ax.bar(range(len(distances)), counts, color=colors[:len(distances)])

    for bar, count in zip(bars, counts):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(count)}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax.set_xticks(range(len(distances)))
    ax.set_xticklabels(distance_labels, rotation=45, ha='right')
    ax.set_title('По дистанциям', fontsize=14, fontweight='bold')
    ax.set_ylabel('Количество', fontsize=12)
    ax.grid(True, alpha=0.3, axis='y', linestyle='--')
