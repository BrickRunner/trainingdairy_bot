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
        # Переводим параметры на русский для промпта
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

        # Уровень подготовки - если None, AI определит сам
        if fitness_level is None:
            fitness_level_name = "определи сам на основе данных ниже"
        else:
            fitness_level_names = {
                'beginner': 'новичок',
                'intermediate': 'средний уровень',
                'advanced': 'продвинутый уровень'
            }
            fitness_level_name = fitness_level_names.get(fitness_level, fitness_level)

        # Форматируем данные для промпта
        recent_trainings_str = format_trainings_for_prompt(recent_trainings or [])
        personal_records_str = format_personal_records(personal_records or {})
        competitions_str = _format_competitions(competitions or [])
        health_str = _format_health_data(health_data or [])

        # Формируем промпт
        prompt = PROMPT_TRAINING_PLAN.format(
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
        logger.info(f"Training plan generated for user {user_id}")

        # Парсим JSON ответ
        try:
            # Извлекаем JSON из ответа (может быть обернут в ```json```)
            if "```json" in ai_response:
                json_start = ai_response.find("```json") + 7
                json_end = ai_response.find("```", json_start)
                json_str = ai_response[json_start:json_end].strip()
            elif "```" in ai_response:
                json_start = ai_response.find("```") + 3
                json_end = ai_response.find("```", json_start)
                json_str = ai_response[json_start:json_end].strip()
            else:
                json_str = ai_response

            plan_data = json.loads(json_str)
            return plan_data

        except json.JSONDecodeError:
            logger.error(f"Failed to parse AI response as JSON: {ai_response[:200]}")
            # Возвращаем как текст если не удалось распарсить
            return {
                "plan": [],
                "explanation": ai_response,
                "raw_response": ai_response
            }

    except Exception as e:
        logger.error(f"Error generating training plan: {e}")
        return None


def _format_competitions(competitions: List[Dict]) -> str:
    """Форматирует соревнования пользователя"""
    if not competitions:
        return "Нет данных о соревнованиях"

    formatted = []
    for comp in competitions[:10]:  # Последние 10
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

    # Вычисляем средние значения
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
