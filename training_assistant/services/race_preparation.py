"""
Сервис подготовки к соревнованиям
"""

import logging
from typing import Dict, Any, Optional
from ai.ai_analyzer import ai_client, _call_with_retry
from training_assistant.prompts.templates import SYSTEM_PROMPT_COACH, PROMPT_RACE_PREPARATION
from training_assistant.services.utils import get_user_preferences

logger = logging.getLogger(__name__)


async def get_race_preparation_advice(
    user_id: int,
    competition_name: str,
    competition_date: str,
    distance: float,
    days_before: int,
    target_time: Optional[str] = None,
    recent_trainings: Optional[list] = None,
    personal_record: Optional[str] = None,
    weekly_volume: Optional[float] = None
) -> Optional[Dict[str, Any]]:
    """
    Дает рекомендации по подготовке к соревнованию

    Args:
        user_id: ID пользователя
        competition_name: Название соревнования
        competition_date: Дата соревнования
        distance: Дистанция в км
        days_before: За сколько дней до старта (7, 5, 3, 1)
        target_time: Целевое время
        recent_trainings: Последние тренировки
        personal_record: Личный рекорд на дистанции
        weekly_volume: Средний недельный объем

    Returns:
        Dict с рекомендациями или None при ошибке
    """
    if not ai_client:
        logger.warning("AI client not configured")
        return None

    try:
        user_prefs = await get_user_preferences(user_id)

        prompt = PROMPT_RACE_PREPARATION.format(
            distance_unit=user_prefs['distance_unit'],
            date_format=user_prefs['date_format'],
            competition_name=competition_name,
            competition_date=competition_date,
            distance=distance,
            target_time=target_time or "не указано",
            days_before=days_before,
            recent_trainings=_format_trainings(recent_trainings or []),
            personal_record=personal_record or "нет данных",
            weekly_volume=f"{weekly_volume} км" if weekly_volume else "не указан"
        )

        response = await _call_with_retry(
            ai_client,
            model="google/gemini-2.5-flash",  
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_COACH},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )

        ai_response = response.choices[0].message.content.strip()
        logger.info(f"Race preparation advice generated for user {user_id}, {days_before} days before")

        return {"raw_response": ai_response}

    except Exception as e:
        logger.error(f"Error generating race preparation advice: {e}")
        return None


def _format_trainings(trainings: list) -> str:
    """Форматирует тренировки для промпта"""
    if not trainings:
        return "Нет данных"

    formatted = []
    for t in trainings[:10]:  
        formatted.append(
            f"- {t.get('date')}: {t.get('type')}, {t.get('distance', 'N/A')} км"
        )
    return "\n".join(formatted)
