"""
Сервис прогноза результатов
"""

import json
import logging
from typing import Dict, Any, Optional, List
from ai.ai_analyzer import ai_client, _call_with_retry
from training_assistant.prompts.templates import (
    SYSTEM_PROMPT_COACH,
    PROMPT_RESULT_PREDICTION,
    format_trainings_for_prompt
)

logger = logging.getLogger(__name__)


async def predict_race_result(
    user_id: int,
    target_distance: float,
    analysis_period: str,
    training_data: List[Dict[str, Any]],
    personal_records: Optional[Dict] = None,
    weekly_volume: Optional[float] = None
) -> Optional[Dict[str, Any]]:
    """
    Прогнозирует результат на дистанции на основе тренировок

    Args:
        user_id: ID пользователя
        target_distance: Целевая дистанция в км
        analysis_period: Период анализа ('month', '2weeks')
        training_data: Данные тренировок за период
        personal_records: Личные рекорды
        weekly_volume: Средненедельный объем

    Returns:
        Dict с прогнозом или None при ошибке
    """
    if not ai_client:
        logger.warning("AI client not configured")
        return None

    try:
        # Анализируем тренировки
        training_analysis = _analyze_training_data(training_data)

        # Форматируем период
        period_names = {
            'month': 'последний месяц',
            '2weeks': 'последние 2 недели'
        }
        period_name = period_names.get(analysis_period, analysis_period)

        # Форматируем промпт
        prompt = PROMPT_RESULT_PREDICTION.format(
            target_distance=target_distance,
            analysis_period=period_name,
            training_data=format_trainings_for_prompt(training_data),
            personal_records=_format_personal_records(personal_records or {}),
            weekly_volume=f"{weekly_volume} км" if weekly_volume else "не указан",
            pulse_zone_adherence=training_analysis.get('pulse_adherence', 'нет данных'),
            training_types_distribution=training_analysis.get('types_distribution', 'нет данных')
        )

        # Запрос к AI
        response = await _call_with_retry(
            ai_client,
            model="google/gemini-2.5-flash",  # Бесплатная модель
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_COACH},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,  # Более консервативная температура для прогноза
            max_tokens=1500
        )

        ai_response = response.choices[0].message.content.strip()
        logger.info(f"Result prediction generated for user {user_id}, {target_distance} km")

        # Парсим JSON
        try:
            if "```json" in ai_response:
                json_start = ai_response.find("```json") + 7
                json_end = ai_response.find("```", json_start)
                json_str = ai_response[json_start:json_end].strip()
            else:
                json_str = ai_response

            prediction_data = json.loads(json_str)
            return prediction_data

        except json.JSONDecodeError:
            return {"prediction": ai_response, "raw_response": ai_response}

    except Exception as e:
        logger.error(f"Error predicting result: {e}")
        return None


def _analyze_training_data(trainings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Анализирует тренировочные данные для прогноза"""
    if not trainings:
        return {}

    analysis = {}

    # Распределение по типам тренировок
    types_count = {}
    for t in trainings:
        training_type = t.get('type', 'unknown')
        types_count[training_type] = types_count.get(training_type, 0) + 1

    types_distribution = ", ".join([f"{t}: {c}" for t, c in types_count.items()])
    analysis['types_distribution'] = types_distribution

    # Простой анализ соблюдения пульсовых зон (если есть данные)
    pulse_data = [t.get('avg_pulse') for t in trainings if t.get('avg_pulse')]
    if pulse_data:
        avg_pulse = sum(pulse_data) / len(pulse_data)
        analysis['pulse_adherence'] = f"Средний пульс: {avg_pulse:.0f} уд/мин"
    else:
        analysis['pulse_adherence'] = "Нет данных о пульсе"

    return analysis


def _format_personal_records(records: Dict) -> str:
    """Форматирует личные рекорды"""
    if not records:
        return "Нет данных о личных рекордах"

    formatted = []
    for distance, time in records.items():
        formatted.append(f"- {distance} км: {time}")

    return "\n".join(formatted)
