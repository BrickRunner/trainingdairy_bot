"""
AI анализатор данных тренировок и здоровья через OpenRouter API
"""

import os
import asyncio
import logging
from typing import Dict, List, Any, Optional
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# Настройки retry для rate limit (429)
MAX_RETRIES = 3
RETRY_DELAYS = [3, 6, 12]  # секунды между повторными попытками


async def _call_with_retry(client, **kwargs):
    """Выполняет запрос к API с повторными попытками при rate limit (429)"""
    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            return await client.chat.completions.create(**kwargs)
        except Exception as e:
            last_error = e
            if "429" in str(e) and attempt < MAX_RETRIES:
                delay = RETRY_DELAYS[attempt]
                logger.info(f"Rate limit (429), waiting {delay}s before retry {attempt + 1}/{MAX_RETRIES}...")
                await asyncio.sleep(delay)
            else:
                raise
    raise last_error

# Инициализация OpenRouter клиента
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

# Создаем клиент OpenRouter через OpenAI-совместимый API
ai_client = None
if OPENROUTER_API_KEY:
    ai_client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
        default_headers={
            "HTTP-Referer": "https://github.com/trainingdiary-bot",  # Опциональное поле для OpenRouter
        }
    )


async def analyze_training_statistics(
    statistics: Dict[str, Any],
    trainings: List[Dict[str, Any]],
    period: str,
    distance_unit: str = "км"
) -> Optional[str]:
    """
    Анализирует статистику тренировок с помощью AI

    Args:
        statistics: Словарь со статистикой (из get_training_statistics)
        trainings: Список тренировок за период
        period: Период ("week", "2weeks", "month")
        distance_unit: Единица измерения расстояния

    Returns:
        Короткий текстовый анализ простыми словами или None при ошибке
    """
    if not ai_client:
        logger.warning("OpenRouter API key not configured")
        return None

    try:
        # Формируем данные для анализа
        period_names = {
            "week": "неделю",
            "2weeks": "2 недели",
            "month": "месяц"
        }
        period_name = period_names.get(period, period)

        # Подготовка данных о тренировках
        training_types = statistics.get('types_count', {})
        types_str = ", ".join([f"{t}: {c}" for t, c in training_types.items()])

        # Создаем промпт для AI
        prompt = f"""Ты спортивный аналитик. Проанализируй данные тренировок спортсмена за {period_name}.

Данные:
- Всего тренировок: {statistics.get('total_count', 0)}
- Общий километраж: {statistics.get('total_distance', 0):.1f} {distance_unit}
- Типы тренировок: {types_str}
- Средний уровень усилий: {statistics.get('avg_fatigue', 0):.1f}/10

Напиши КОРОТКИЙ анализ (максимум 4-5 предложений) ПРОСТЫМИ словами:
1. Общая оценка тренировочной нагрузки
2. Что хорошо
3. На что обратить внимание или рекомендация

Пиши как дружелюбный тренер, без сложных терминов. Используй эмодзи для наглядности."""

        # Запрос к OpenRouter API с retry при rate limit
        response = await _call_with_retry(
            ai_client,
            model="google/gemini-2.0-flash-exp:free",
            messages=[
                {
                    "role": "system",
                    "content": "Ты дружелюбный спортивный тренер, который объясняет статистику простыми словами."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=500
        )

        analysis = response.choices[0].message.content.strip()
        logger.info(f"AI analysis generated successfully for training stats")
        return analysis

    except Exception as e:
        logger.error(f"Error generating AI analysis for trainings: {e}")
        return None


async def analyze_health_statistics(
    statistics: Dict[str, Any],
    metrics: List[Dict[str, Any]],
    period_name: str,
    weight_unit: str = "кг"
) -> Optional[str]:
    """
    Анализирует статистику здоровья с помощью AI

    Args:
        statistics: Словарь со статистикой (из get_health_statistics)
        metrics: Список метрик здоровья за период
        period_name: Название периода (например, "7 дней")
        weight_unit: Единица измерения веса

    Returns:
        Короткий текстовый анализ простыми словами или None при ошибке
    """
    if not ai_client:
        logger.warning("OpenRouter API key not configured")
        return None

    try:
        # Подготовка данных
        pulse_data = statistics.get('pulse', {})
        weight_data = statistics.get('weight', {})
        sleep_data = statistics.get('sleep', {})

        # Формируем строки с данными
        pulse_str = ""
        if pulse_data.get('avg'):
            pulse_str = f"Средний: {pulse_data['avg']:.0f} уд/мин, Диапазон: {pulse_data.get('min', 0):.0f}-{pulse_data.get('max', 0):.0f}"

        weight_str = ""
        if weight_data.get('current'):
            change = weight_data.get('change', 0)
            change_str = f"{change:+.1f} {weight_unit}" if change else "без изменений"
            weight_str = f"Текущий: {weight_data['current']:.1f} {weight_unit}, Изменение: {change_str}"

        sleep_str = ""
        if sleep_data.get('avg'):
            sleep_str = f"Среднее: {sleep_data['avg']:.1f} ч, Диапазон: {sleep_data.get('min', 0):.1f}-{sleep_data.get('max', 0):.1f} ч"

        # Создаем промпт для AI
        prompt = f"""Ты врач спортивной медицины. Проанализируй показатели здоровья спортсмена за {period_name}.

Данные:
- Дней с записями: {statistics.get('total_days', 0)}
- Утренний пульс: {pulse_str if pulse_str else 'нет данных'}
- Вес: {weight_str if weight_str else 'нет данных'}
- Сон: {sleep_str if sleep_str else 'нет данных'}

Напиши КОРОТКИЙ анализ (максимум 4-5 предложений) ПРОСТЫМИ словами:
1. Общая оценка состояния здоровья
2. Положительные моменты
3. На что обратить внимание или простая рекомендация

Пиши как дружелюбный врач, без медицинских терминов. Используй эмодзи для наглядности."""

        # Запрос к OpenRouter API с retry при rate limit
        response = await _call_with_retry(
            ai_client,
            model="google/gemini-2.0-flash-exp:free",
            messages=[
                {
                    "role": "system",
                    "content": "Ты дружелюбный врач спортивной медицины, который объясняет показатели здоровья простыми словами."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=500
        )

        analysis = response.choices[0].message.content.strip()
        logger.info(f"AI analysis generated successfully for health stats")
        return analysis

    except Exception as e:
        logger.error(f"Error generating AI analysis for health: {e}")
        return None


def is_ai_available() -> bool:
    """Проверяет, доступен ли AI анализ"""
    return ai_client is not None
