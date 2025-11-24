"""
Модуль для расчёта статистики по соревнованиям
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date
from collections import defaultdict
import json
import logging

logger = logging.getLogger(__name__)


def calculate_pace(distance_km: float, time_str: str) -> Optional[str]:
    """
    Рассчитать темп (мин/км) на основе дистанции и времени

    Args:
        distance_km: Дистанция в км
        time_str: Время в формате HH:MM:SS

    Returns:
        Темп в формате MM:SS или None
    """
    if not time_str or not distance_km or distance_km <= 0:
        return None

    try:
        parts = time_str.split(':')
        if len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
            total_seconds = hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:
            minutes, seconds = map(int, parts)
            total_seconds = minutes * 60 + seconds
        else:
            return None

        # Темп в секундах на км
        pace_seconds = total_seconds / distance_km
        pace_minutes = int(pace_seconds // 60)
        pace_secs = int(pace_seconds % 60)

        return f"{pace_minutes:02d}:{pace_secs:02d}"
    except (ValueError, ZeroDivisionError):
        return None


def calculate_competitions_statistics(participants: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Рассчитать статистику по соревнованиям пользователя

    Args:
        participants: Список участий с данными соревнований (JOIN competitions)

    Returns:
        Словарь со статистикой
    """
    if not participants:
        return {
            'total_competitions': 0,
            'finished': 0,
            'dns': 0,
            'dnf': 0,
            'registered': 0,
            'by_type': {},
            'by_distance': {},
            'total_distance': 0,
            'personal_records': {},
            'average_pace_by_distance': {},
            'cities': set(),
            'countries': set(),
            'organizers': set(),
            'best_places_overall': [],
            'best_places_category': []
        }

    # Базовая статистика
    stats = {
        'total_competitions': len(participants),
        'finished': 0,
        'dns': 0,
        'dnf': 0,
        'registered': 0,
        'by_type': defaultdict(int),
        'by_distance': defaultdict(int),
        'total_distance': 0.0,
        'personal_records': {},  # {distance: {'time': ..., 'competition': ..., 'date': ...}}
        'average_pace_by_distance': {},
        'cities': set(),
        'countries': set(),
        'organizers': set(),
        'best_places_overall': [],
        'best_places_category': [],
        'goal_achievement': {'achieved': 0, 'not_achieved': 0, 'no_goal': 0}
    }

    # Для расчёта средних темпов
    pace_data = defaultdict(list)  # {distance: [pace_seconds, ...]}

    for p in participants:
        # Статусы
        status = p.get('status', 'registered')
        if status == 'finished':
            stats['finished'] += 1
        elif status == 'dns':
            stats['dns'] += 1
        elif status == 'dnf':
            stats['dnf'] += 1
        elif status == 'registered':
            stats['registered'] += 1

        # Виды спорта
        sport_type = p.get('sport_type', 'бег')
        stats['by_type'][sport_type] += 1

        # Дистанции
        distance = p.get('distance')
        if distance:
            stats['by_distance'][distance] += 1
            stats['total_distance'] += distance

        # География
        if p.get('city'):
            stats['cities'].add(p['city'])
        if p.get('country'):
            stats['countries'].add(p['country'])

        # Организаторы
        if p.get('organizer'):
            stats['organizers'].add(p['organizer'])

        # Только для финишировавших
        if status == 'finished' and distance and p.get('finish_time'):
            finish_time = p['finish_time']

            # Личные рекорды
            if distance not in stats['personal_records']:
                stats['personal_records'][distance] = {
                    'time': finish_time,
                    'competition': p.get('name', 'Без названия'),
                    'date': p.get('date'),
                    'pace': calculate_pace(distance, finish_time),
                    'qualification': p.get('qualification')
                }
            else:
                # Сравниваем времена
                current_pr = stats['personal_records'][distance]['time']
                if _compare_times(finish_time, current_pr) < 0:
                    stats['personal_records'][distance] = {
                        'time': finish_time,
                        'competition': p.get('name', 'Без названия'),
                        'date': p.get('date'),
                        'pace': calculate_pace(distance, finish_time),
                        'qualification': p.get('qualification')
                    }

            # Собираем данные для среднего темпа
            pace_seconds = _time_to_seconds(finish_time)
            if pace_seconds:
                pace_data[distance].append(pace_seconds / distance)

            # Достижение целей
            target_time = p.get('target_time')
            if target_time:
                if _compare_times(finish_time, target_time) <= 0:
                    stats['goal_achievement']['achieved'] += 1
                else:
                    stats['goal_achievement']['not_achieved'] += 1
            else:
                stats['goal_achievement']['no_goal'] += 1

            # Лучшие места
            place_overall = p.get('place_overall')
            if place_overall:
                stats['best_places_overall'].append({
                    'place': place_overall,
                    'competition': p.get('name', 'Без названия'),
                    'date': p.get('date'),
                    'distance': distance
                })

            place_category = p.get('place_age_category')
            if place_category:
                stats['best_places_category'].append({
                    'place': place_category,
                    'competition': p.get('name', 'Без названия'),
                    'date': p.get('date'),
                    'distance': distance,
                    'category': p.get('age_category', '')
                })

    # Рассчитываем средние темпы
    for distance, paces in pace_data.items():
        if paces:
            avg_pace_seconds = sum(paces) / len(paces)
            pace_minutes = int(avg_pace_seconds // 60)
            pace_secs = int(avg_pace_seconds % 60)
            stats['average_pace_by_distance'][distance] = f"{pace_minutes:02d}:{pace_secs:02d}"

    # Сортируем лучшие места
    stats['best_places_overall'].sort(key=lambda x: x['place'])
    stats['best_places_category'].sort(key=lambda x: x['place'])

    # Ограничиваем топ-5
    stats['best_places_overall'] = stats['best_places_overall'][:5]
    stats['best_places_category'] = stats['best_places_category'][:5]

    # Конвертируем defaultdict в обычный dict для сериализации
    stats['by_type'] = dict(stats['by_type'])
    stats['by_distance'] = dict(stats['by_distance'])

    return stats


def _time_to_seconds(time_str: str) -> Optional[int]:
    """Конвертировать время HH:MM:SS в секунды"""
    if not time_str:
        return None
    try:
        parts = time_str.split(':')
        if len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        return None
    except (ValueError, IndexError):
        return None


def _compare_times(time1: str, time2: str) -> int:
    """
    Сравнить два времени в формате HH:MM:SS

    Returns:
        -1 если time1 < time2
        0 если time1 == time2
        1 если time1 > time2
    """
    sec1 = _time_to_seconds(time1)
    sec2 = _time_to_seconds(time2)

    if sec1 is None or sec2 is None:
        return 0

    if sec1 < sec2:
        return -1
    elif sec1 > sec2:
        return 1
    return 0


def format_statistics_message(stats: Dict[str, Any]) -> str:
    """
    Форматировать статистику в красивое сообщение

    Args:
        stats: Словарь со статистикой

    Returns:
        Отформатированное сообщение
    """
    if stats['total_competitions'] == 0:
        return "📊 У вас пока нет соревнований"

    msg = "📊 <b>Статистика соревнований</b>\n\n"

    # Общая статистика
    msg += f"🏃 <b>Всего соревнований:</b> {stats['total_competitions']}\n"
    msg += f"✅ Финишировано: {stats['finished']}\n"
    if stats['registered'] > 0:
        msg += f"📝 Зарегистрировано: {stats['registered']}\n"
    if stats['dns'] > 0:
        msg += f"❌ DNS: {stats['dns']}\n"
    if stats['dnf'] > 0:
        msg += f"⚠️ DNF: {stats['dnf']}\n"

    msg += f"\n📏 <b>Суммарный километраж:</b> {stats['total_distance']:.1f} км\n"

    # По типам
    if stats['by_type']:
        msg += "\n<b>По типам:</b>\n"
        for comp_type, count in sorted(stats['by_type'].items(), key=lambda x: x[1], reverse=True):
            msg += f"  • {comp_type}: {count}\n"

    # Личные рекорды
    if stats['personal_records']:
        msg += "\n🏆 <b>Личные рекорды:</b>\n"
        for distance in sorted(stats['personal_records'].keys()):
            pr = stats['personal_records'][distance]
            pace_info = f" ({pr['pace']} мин/км)" if pr.get('pace') else ""
            qualification_info = f" - {pr['qualification']}" if pr.get('qualification') else ""
            msg += f"  • {distance} км: {pr['time']}{pace_info}{qualification_info}\n"

    # Лучшие места
    if stats['best_places_overall']:
        msg += "\n🥇 <b>Топ-5 мест (общий зачёт):</b>\n"
        for item in stats['best_places_overall'][:5]:
            msg += f"  • {item['place']} место - {item['competition']} ({item['distance']} км)\n"

    # Достижение целей
    if stats['finished'] > 0:
        total_with_goal = stats['goal_achievement']['achieved'] + stats['goal_achievement']['not_achieved']
        if total_with_goal > 0:
            achievement_rate = (stats['goal_achievement']['achieved'] / total_with_goal) * 100
            msg += f"\n🎯 <b>Достижение целей:</b> {achievement_rate:.0f}%\n"
            msg += f"  • Выполнено: {stats['goal_achievement']['achieved']}\n"
            msg += f"  • Не выполнено: {stats['goal_achievement']['not_achieved']}\n"

    return msg
