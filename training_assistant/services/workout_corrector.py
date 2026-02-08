"""
Сервис коррекции тренировок
"""

import json
import logging
from typing import Dict, List, Any, Optional
from ai.ai_analyzer import ai_client, _call_with_retry
from training_assistant.prompts.templates import SYSTEM_PROMPT_COACH, PROMPT_CORRECTION

logger = logging.getLogger(__name__)


async def analyze_and_correct_workout(
    user_id: int,
    training_data: Dict[str, Any],
    user_feedback: str,
    user_comment: Optional[str] = None,
    recent_trainings: Optional[List[Dict]] = None,
    pulse_zones: Optional[Dict] = None
) -> Optional[Dict[str, Any]]:
    """
    Анализирует тренировку и дает рекомендации по корректировке

    Args:
        user_id: ID пользователя
        training_data: Данные выполненной тренировки
        user_feedback: Обратная связь ('too_hard', 'too_easy', 'high_pulse', etc.)
        user_comment: Комментарий пользователя
        recent_trainings: Последние тренировки
        pulse_zones: Пульсовые зоны пользователя

    Returns:
        Dict с анализом и рекомендациями или None при ошибке
    """
    if not ai_client:
        logger.warning("AI client not configured")
        return None

    try:
        feedback_translations = {
            'too_hard': 'Было слишком тяжело',
            'too_easy': 'Было слишком легко',
            'high_pulse': 'Пульс был выше нормы',
            'slow_pace': 'Не уложился в темп',
            'didnt_finish': 'Не закончил тренировку'
        }
        feedback_text = feedback_translations.get(user_feedback, user_feedback)

        prompt = PROMPT_CORRECTION.format(
            training_type=training_data.get('type', 'N/A'),
            planned_volume=training_data.get('planned_volume', 'не указан'),
            actual_volume=f"{training_data.get('distance', 'N/A')} км",
            pace=training_data.get('avg_pace', 'N/A'),
            avg_pulse=training_data.get('avg_pulse', 'N/A'),
            max_pulse=training_data.get('max_pulse', 'N/A'),
            fatigue_level=training_data.get('fatigue_level', 'N/A'),
            user_feedback=feedback_text,
            user_comment=user_comment or "нет",
            recent_trainings=_format_recent_trainings(recent_trainings or []),
            current_plan="не указан",
            pulse_zones=_format_pulse_zones(pulse_zones or {})
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
        logger.info(f"Workout correction generated for user {user_id}")

        try:
            if "```json" in ai_response:
                json_start = ai_response.find("```json") + 7
                json_end = ai_response.find("```", json_start)
                json_str = ai_response[json_start:json_end].strip()
            else:
                json_str = ai_response

            correction_data = json.loads(json_str)
            return correction_data

        except json.JSONDecodeError:
            return {"analysis": ai_response, "raw_response": ai_response}

    except Exception as e:
        logger.error(f"Error analyzing workout: {e}")
        return None


def _format_recent_trainings(trainings: List[Dict]) -> str:
    """Форматирует список тренировок для промпта"""
    if not trainings:
        return "Нет данных"

    formatted = []
    for t in trainings[:5]:  
        formatted.append(
            f"- {t.get('date')}: {t.get('type')}, "
            f"{t.get('distance', 'N/A')} км, "
            f"темп {t.get('avg_pace', 'N/A')}, "
            f"пульс {t.get('avg_pulse', 'N/A')}"
        )
    return "\n".join(formatted)


def _format_pulse_zones(zones: Dict) -> str:
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
