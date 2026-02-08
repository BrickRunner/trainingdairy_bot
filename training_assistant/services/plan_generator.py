"""
Сервис генерации тренировочных планов
"""

import json
import logging
from typing import Dict, List, Any, Optional
from ai.ai_analyzer import ai_client, _call_with_retry
from training_assistant.prompts.templates import (
    SYSTEM_PROMPT_COACH,
    PROMPT_TRAINING_PLAN,
    format_trainings_for_prompt,
    format_personal_records
)
from training_assistant.services.utils import get_user_preferences

logger = logging.getLogger(__name__)


async def generate_training_plan(
    user_id: int,
    sport_type: str,
    plan_duration: str,
    fitness_level: Optional[str],
    available_days: List[str],
    target_distance: Optional[float] = None,
    goal_description: Optional[str] = None,
    recent_trainings: Optional[List[Dict]] = None,
    personal_records: Optional[Dict] = None,
    competitions: Optional[List[Dict]] = None,
    health_data: Optional[List[Dict]] = None
) -> Optional[Dict[str, Any]]:
    """
    Генерирует персональный тренировочный план с помощью AI

    Args:
        user_id: ID пользователя
        sport_type: Вид спорта ('run', 'swim', 'bike')
        plan_duration: Длительность ('week', 'month')
        fitness_level: Уровень подготовки (None = AI определит сам)
        available_days: Доступные дни для тренировок
        target_distance: Целевая дистанция в км (опционально)
        goal_description: Описание цели (опционально)
        recent_trainings: Последние тренировки (опционально)
        personal_records: Личные рекорды (опционально)
        competitions: Соревнования пользователя (опционально)
        health_data: Данные о здоровье (опционально)

    Returns:
        Dict с планом тренировок или None при ошибке
    """
    if not ai_client:
        logger.warning("AI client not configured")
        return None

    try:
        user_prefs = await get_user_preferences(user_id)

        sport_names = {
            'run': 'бег',
            'swim': 'плавание',
            'bike': 'велоспорт',
            'triathlon': 'триатлон'
        }
        sport_name = sport_names.get(sport_type, sport_type)

        plan_duration_names = {
            'week': 'неделя',
            'month': 'месяц'
        }
        plan_duration_name = plan_duration_names.get(plan_duration, plan_duration)

        if fitness_level is None:
            fitness_level_name = "определи сам на основе данных ниже"
        else:
            fitness_level_names = {
                'beginner': 'новичок',
                'intermediate': 'средний уровень',
                'advanced': 'продвинутый уровень'
            }
            fitness_level_name = fitness_level_names.get(fitness_level, fitness_level)

        recent_trainings_str = format_trainings_for_prompt(recent_trainings or [])
        personal_records_str = format_personal_records(personal_records or {})
        competitions_str = _format_competitions(competitions or [])
        health_str = _format_health_data(health_data or [])

        prompt = PROMPT_TRAINING_PLAN.format(
            distance_unit=user_prefs['distance_unit'],
            weight_unit=user_prefs['weight_unit'],
            date_format=user_prefs['date_format'],
            sport_type=sport_name,
            fitness_level=fitness_level_name,
            plan_duration=plan_duration_name,
            target_distance=target_distance or "не указана",
            goal_description=goal_description or "общая подготовка",
            available_days=", ".join(available_days),
            recent_trainings=recent_trainings_str,
            personal_records=personal_records_str,
            competitions=competitions_str,
            health_data=health_str
        )

        response = await _call_with_retry(
            ai_client,
            model="google/gemini-2.5-flash",  
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_COACH},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000  
        )

        ai_response = response.choices[0].message.content.strip()
        logger.info(f"Training plan generated for user {user_id}")

        json_str = None

        if "```json" in ai_response.lower():
            json_marker_pos = ai_response.lower().find("```json")
            marker_end = json_marker_pos + 7  

            json_start = marker_end
            while json_start < len(ai_response) and ai_response[json_start] in [' ', '\n', '\r', '\t']:
                json_start += 1

            json_end = ai_response.find("```", json_start)
            if json_end != -1 and json_start < json_end:
                json_str = ai_response[json_start:json_end].strip()
        elif "```" in ai_response:
            first_tick = ai_response.find("```")
            json_start = first_tick + 3

            while json_start < len(ai_response) and ai_response[json_start] in [' ', '\n', '\r', '\t']:
                json_start += 1

            json_end = ai_response.find("```", json_start)
            if json_end != -1 and json_start < json_end:
                json_str = ai_response[json_start:json_end].strip()
        elif ai_response.strip().startswith("{") and ai_response.strip().endswith("}"):
            json_str = ai_response.strip()
        else:
            first_brace = ai_response.find("{")
            last_brace = ai_response.rfind("}")
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                json_str = ai_response[first_brace:last_brace+1]

        if json_str:
            try:
                plan_data = json.loads(json_str)
                if isinstance(plan_data, dict):
                    logger.info(f"Successfully parsed training plan with {len(plan_data.get('plan', []))} workouts")
                    return plan_data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse extracted JSON: {e}")
                logger.error(f"JSON parse error at position {e.pos}: {e.msg}")
                logger.debug(f"Extracted JSON string (first 1000 chars): {json_str[:1000]}")
                logger.debug(f"Full AI response length: {len(ai_response)} chars")
        else:
            logger.error("Could not extract JSON string from AI response")

        logger.error(f"Could not extract valid JSON from AI response (showing first 500 chars): {ai_response[:500]}")
        return {
            "plan": [],
            "explanation": "Не удалось сгенерировать план. Попробуйте еще раз.",
            "raw_response": ai_response[:1000]  
        }

    except Exception as e:
        logger.error(f"Error generating training plan: {e}")
        return None


def _format_competitions(competitions: List[Dict]) -> str:
    """Форматирует соревнования пользователя"""
    if not competitions:
        return "Нет данных о соревнованиях"

    formatted = []
    for comp in competitions[:10]:  
        result = comp.get('result_time', 'N/A')
        formatted.append(
            f"- {comp.get('competition_name', 'N/A')}: "
            f"{comp.get('distance', 'N/A')} км, результат {result}"
        )

    return "\n".join(formatted)


def _format_health_data(health_data: List[Dict]) -> str:
    """Форматирует данные о здоровье"""
    if not health_data:
        return "Нет данных о здоровье"

    resting_pulses = [h.get('resting_pulse') for h in health_data if h.get('resting_pulse')]
    weights = [h.get('weight') for h in health_data if h.get('weight')]
    sleep_hours = [h.get('sleep_hours') for h in health_data if h.get('sleep_hours')]

    formatted = []
    if resting_pulses:
        avg_pulse = sum(resting_pulses) / len(resting_pulses)
        formatted.append(f"- Средний пульс покоя: {avg_pulse:.0f} уд/мин")

    if weights:
        avg_weight = sum(weights) / len(weights)
        formatted.append(f"- Средний вес: {avg_weight:.1f} кг")

    if sleep_hours:
        avg_sleep = sum(sleep_hours) / len(sleep_hours)
        formatted.append(f"- Средняя продолжительность сна: {avg_sleep:.1f} ч")

    return "\n".join(formatted) if formatted else "Нет данных о здоровье"
