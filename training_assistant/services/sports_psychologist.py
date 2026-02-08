"""
Сервис психологической поддержки
"""

import logging
from typing import List, Dict, Any, Optional
from ai.ai_analyzer import ai_client, _call_with_retry
from training_assistant.prompts.templates import SYSTEM_PROMPT_PSYCHOLOGIST, PROMPT_PSYCHOLOGIST

logger = logging.getLogger(__name__)


async def chat_with_psychologist(
    user_id: int,
    user_message: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    athlete_context: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    Ведет диалог с пользователем как спортивный психолог

    Args:
        user_id: ID пользователя
        user_message: Сообщение от пользователя
        conversation_history: История диалога [{"user": "...", "ai": "..."}, ...]
        athlete_context: Контекст спортсмена (предстоящие соревнования, тренировки и т.д.)

    Returns:
        Ответ AI-психолога или None при ошибке
    """
    if not ai_client:
        logger.warning("AI client not configured")
        return None

    try:
        history_str = _format_conversation_history(conversation_history or [])

        context_str = _format_athlete_context(athlete_context or {})

        prompt = PROMPT_PSYCHOLOGIST.format(
            conversation_history=history_str,
            athlete_context=context_str,
            user_message=user_message
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_PSYCHOLOGIST}
        ]

        if conversation_history:
            for conv in conversation_history[-5:]:  
                messages.append({"role": "user", "content": conv.get("user", "")})
                messages.append({"role": "assistant", "content": conv.get("ai", "")})

        messages.append({"role": "user", "content": prompt})

        response = await _call_with_retry(
            ai_client,
            model="google/gemini-2.5-flash",  
            messages=messages,
            temperature=0.8,  
            max_tokens=1000
        )

        ai_response = response.choices[0].message.content.strip()
        logger.info(f"Psychologist response generated for user {user_id}")

        return ai_response

    except Exception as e:
        logger.error(f"Error generating psychologist response: {e}")
        return None


def _format_conversation_history(history: List[Dict[str, str]]) -> str:
    """Форматирует историю диалога для промпта"""
    if not history:
        return "Это первое сообщение в диалоге"

    formatted = []
    for i, conv in enumerate(history[-5:], 1):  
        formatted.append(f"Сообщение {i}:")
        formatted.append(f"Спортсмен: {conv.get('user', '')}")
        formatted.append(f"Психолог: {conv.get('ai', '')}")
        formatted.append("")

    return "\n".join(formatted)


def _format_athlete_context(context: Dict[str, Any]) -> str:
    """Форматирует контекст спортсмена"""
    if not context:
        return "Контекст не указан"

    parts = []

    if context.get('upcoming_competitions'):
        parts.append(f"Предстоящие соревнования: {context['upcoming_competitions']}")

    if context.get('recent_trainings'):
        parts.append(f"Последние тренировки: {context['recent_trainings']}")

    if context.get('personal_records'):
        parts.append(f"Личные рекорды: {context['personal_records']}")

    return "\n".join(parts) if parts else "Контекст не указан"
