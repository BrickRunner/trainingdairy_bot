"""
Сервис тактики забега
"""

import logging
from typing import Dict, Any, Optional
from ai.ai_analyzer import ai_client, _call_with_retry
from training_assistant.prompts.templates import SYSTEM_PROMPT_COACH, PROMPT_RACE_TACTICS
from training_assistant.services.utils import get_user_preferences

logger = logging.getLogger(__name__)


async def generate_race_tactics(
    user_id: int,
    distance: float,
    target_time: str,
    race_type: str = 'flat',
    personal_record: Optional[str] = None,
    recent_trainings: Optional[list] = None,
    pulse_zones: Optional[dict] = None
) -> Optional[Dict[str, Any]]:
    """
    Генерирует тактический план забега

    Args:
        user_id: ID пользователя
        distance: Дистанция в км
        target_time: Целевое время (HH:MM:SS)
        race_type: Тип трассы ('flat', 'hilly', 'trail', 'city')
        personal_record: Личный рекорд
        recent_trainings: Последние тренировки
        pulse_zones: Пульсовые зоны

    Returns:
        Dict с тактикой или None при ошибке
    """
    if not ai_client:
        logger.warning("AI client not configured")
        return None

    try:
        # Получаем настройки пользователя
        user_prefs = await get_user_preferences(user_id)

        # Рассчитываем целевой темп
        target_pace = _calculate_target_pace(target_time, distance)

        # Определяем количество сегментов
        laps = _calculate_laps(distance)

        # Переводим тип трассы
        race_type_names = {
            'flat': 'ровная',
            'hilly': 'холмистая',
            'trail': 'трейл',
            'city': 'городская'
        }
        race_type_name = race_type_names.get(race_type, race_type)

        # Форматируем промпт с настройками пользователя
        prompt = PROMPT_RACE_TACTICS.format(
            distance_unit=user_prefs['distance_unit'],
            date_format=user_prefs['date_format'],
            distance=distance,
            target_time=target_time,
            target_pace=target_pace,
            race_type=race_type_name,
            laps=laps,
            personal_record=personal_record or "нет данных",
            recent_trainings=_format_trainings(recent_trainings or []),
            pulse_zones=_format_pulse_zones(pulse_zones or {})
        )

        # Запрос к AI
        response = await _call_with_retry(
            ai_client,
            model="google/gemini-2.5-flash",  # Бесплатная модель
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_COACH},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )

        ai_response = response.choices[0].message.content.strip()
        logger.info(f"Race tactics generated for user {user_id}, {distance} km")

        # AI теперь возвращает форматированный текст, а не JSON
        return {"raw_response": ai_response}

    except Exception as e:
        logger.error(f"Error generating race tactics: {e}")
        return None


def _calculate_target_pace(target_time: str, distance: float) -> str:
    """Рассчитывает целевой темп мин/км"""
    try:
        # Парсим время HH:MM:SS или MM:SS
        time_parts = target_time.split(':')
        if len(time_parts) == 3:
            hours, minutes, seconds = map(int, time_parts)
            total_seconds = hours * 3600 + minutes * 60 + seconds
        elif len(time_parts) == 2:
            minutes, seconds = map(int, time_parts)
            total_seconds = minutes * 60 + seconds
        else:
            return "N/A"

        # Темп в секундах на км
        pace_seconds = total_seconds / distance

        # Конвертируем в MM:SS
        pace_minutes = int(pace_seconds // 60)
        pace_secs = int(pace_seconds % 60)

        return f"{pace_minutes}:{pace_secs:02d} мин/км"

    except Exception:
        return "N/A"


def _calculate_laps(distance: float) -> str:
    """Определяет примерное количество кругов/сегментов"""
    if distance <= 5:
        return "5 сегментов по 1 км"
    elif distance <= 10:
        return "10 сегментов по 1 км или 5 по 2 км"
    elif distance <= 21.1:
        return "21 сегмент по 1 км или 7 по 3 км"
    else:
        return "42 сегмента по 1 км или 10-12 по 3-4 км"


def _format_trainings(trainings: list) -> str:
    """Форматирует тренировки"""
    if not trainings:
        return "Нет данных"

    formatted = []
    for t in trainings[:10]:
        formatted.append(
            f"- {t.get('date')}: {t.get('type')}, "
            f"{t.get('distance', 'N/A')} км, темп {t.get('avg_pace', 'N/A')}"
        )
    return "\n".join(formatted)


def _format_pulse_zones(zones: dict) -> str:
    """Форматирует пульсовые зоны"""
    if not zones:
        return "Не указаны"

    formatted = []
    for i in range(1, 6):
        zone_min = zones.get(f'zone{i}_min')
        zone_max = zones.get(f'zone{i}_max')
        if zone_min and zone_max:
            formatted.append(f"Зона {i}: {zone_min}-{zone_max} уд/мин")

    return "\n".join(formatted) if formatted else "Не указаны"
