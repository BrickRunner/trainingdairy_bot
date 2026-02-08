"""
Database queries для Training Assistant
"""

import aiosqlite
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

DB_PATH = os.getenv('DB_PATH', 'database.sqlite')



async def save_training_plan(
    user_id: int,
    plan_type: str,
    sport_type: str,
    plan_content: Dict[str, Any],
    start_date: str,
    end_date: str,
    **kwargs
) -> Optional[int]:
    """Сохраняет тренировочный план в БД"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO training_plans (
                user_id, plan_type, sport_type, target_distance, target_competition_id,
                current_fitness_level, available_days, goal_description,
                plan_content, ai_explanation, start_date, end_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            plan_type,
            sport_type,
            kwargs.get('target_distance'),
            kwargs.get('target_competition_id'),
            kwargs.get('fitness_level'),
            json.dumps(kwargs.get('available_days', []), ensure_ascii=False),
            kwargs.get('goal_description'),
            json.dumps(plan_content, ensure_ascii=False),
            kwargs.get('ai_explanation'),
            start_date,
            end_date
        ))
        await db.commit()
        return cursor.lastrowid


async def get_active_plan(user_id: int) -> Optional[Dict[str, Any]]:
    """Получает активный план пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM training_plans
            WHERE user_id = ? AND status = 'active'
            ORDER BY created_at DESC LIMIT 1
        """, (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                plan = dict(row)
                plan['plan_content'] = json.loads(plan['plan_content'])
                plan['available_days'] = json.loads(plan['available_days'])
                return plan
            return None


# ==================== TRAINING CORRECTIONS ====================

async def save_training_correction(
    user_id: int,
    training_id: int,
    user_feedback: str,
    ai_analysis: str,
    ai_recommendation: str,
    **kwargs
) -> Optional[int]:
    """Сохраняет корректировку тренировки"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO training_corrections (
                user_id, training_id, plan_id, user_feedback, user_comment,
                ai_analysis, ai_recommendation, correction_applied
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            training_id,
            kwargs.get('plan_id'),
            user_feedback,
            kwargs.get('user_comment'),
            ai_analysis,
            ai_recommendation,
            json.dumps(kwargs.get('correction_applied', {}), ensure_ascii=False)
        ))
        await db.commit()
        return cursor.lastrowid


# ==================== RACE PREPARATIONS ====================

async def save_race_preparation(
    user_id: int,
    competition_id: int,
    days_before: int,
    race_distance: float,
    recommendations: Dict[str, Any],
    **kwargs
) -> Optional[int]:
    """Сохраняет рекомендации по подготовке к соревнованию"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Проверяем, есть ли уже рекомендация
        async with db.execute("""
            SELECT id FROM race_preparations
            WHERE user_id = ? AND competition_id = ? AND days_before = ?
        """, (user_id, competition_id, days_before)) as cursor:
            existing = await cursor.fetchone()

        if existing:
            # Обновляем существующую
            await db.execute("""
                UPDATE race_preparations
                SET recommendations = ?, ai_explanation = ?
                WHERE id = ?
            """, (
                json.dumps(recommendations, ensure_ascii=False),
                kwargs.get('ai_explanation'),
                existing[0]
            ))
            result_id = existing[0]
        else:
            # Создаем новую
            cursor = await db.execute("""
                INSERT INTO race_preparations (
                    user_id, competition_id, days_before, race_distance,
                    target_time, recommendations, ai_explanation
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                competition_id,
                days_before,
                race_distance,
                kwargs.get('target_time'),
                json.dumps(recommendations, ensure_ascii=False),
                kwargs.get('ai_explanation')
            ))
            result_id = cursor.lastrowid

        await db.commit()
        return result_id


# ==================== RACE TACTICS ====================

async def save_race_tactics(
    user_id: int,
    competition_id: int,
    distance: float,
    target_time: str,
    tactics_plan: Dict[str, Any],
    pacing_strategy: str,
    **kwargs
) -> Optional[int]:
    """Сохраняет тактику забега"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Проверяем существующую тактику
        async with db.execute("""
            SELECT id FROM race_tactics
            WHERE user_id = ? AND competition_id = ?
        """, (user_id, competition_id)) as cursor:
            existing = await cursor.fetchone()

        if existing:
            # Обновляем
            await db.execute("""
                UPDATE race_tactics
                SET distance = ?, target_time = ?, tactics_plan = ?,
                    pacing_strategy = ?, key_points = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                distance,
                target_time,
                json.dumps(tactics_plan, ensure_ascii=False),
                pacing_strategy,
                kwargs.get('key_points'),
                existing[0]
            ))
            result_id = existing[0]
        else:
            # Создаем новую
            cursor = await db.execute("""
                INSERT INTO race_tactics (
                    user_id, competition_id, distance, target_time,
                    race_type, tactics_plan, pacing_strategy, key_points
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                competition_id,
                distance,
                target_time,
                kwargs.get('race_type'),
                json.dumps(tactics_plan, ensure_ascii=False),
                pacing_strategy,
                kwargs.get('key_points')
            ))
            result_id = cursor.lastrowid

        await db.commit()
        return result_id


# ==================== AI CONVERSATIONS ====================

async def save_conversation(
    user_id: int,
    conversation_type: str,
    user_message: str,
    ai_response: str,
    context_data: Optional[Dict] = None
) -> Optional[int]:
    """Сохраняет диалог с AI"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO ai_conversations (
                user_id, conversation_type, context_data,
                user_message, ai_response
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            conversation_type,
            json.dumps(context_data or {}, ensure_ascii=False),
            user_message,
            ai_response
        ))
        await db.commit()
        return cursor.lastrowid


async def get_recent_conversations(
    user_id: int,
    conversation_type: str,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """Получает последние сообщения из диалога"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT user_message, ai_response, created_at
            FROM ai_conversations
            WHERE user_id = ? AND conversation_type = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user_id, conversation_type, limit)) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    'user': row['user_message'],
                    'ai': row['ai_response'],
                    'created_at': row['created_at']
                }
                for row in reversed(list(rows))  # Обратный порядок для хронологии
            ]


# ==================== RESULT PREDICTIONS ====================

async def save_result_prediction(
    user_id: int,
    distance: float,
    based_on_period: str,
    predictions: Dict[str, str],
    confidence_level: float,
    ai_explanation: str,
    **kwargs
) -> Optional[int]:
    """Сохраняет прогноз результата"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO result_predictions (
                user_id, distance, based_on_trainings_period,
                predicted_time_realistic, predicted_time_optimistic,
                predicted_time_conservative, confidence_level,
                ai_explanation, key_factors
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            distance,
            based_on_period,
            predictions.get('realistic'),
            predictions.get('optimistic'),
            predictions.get('conservative'),
            confidence_level,
            ai_explanation,
            json.dumps(kwargs.get('key_factors', []), ensure_ascii=False)
        ))
        await db.commit()
        return cursor.lastrowid


# ==================== USER SETTINGS ====================

async def get_or_create_ta_settings(user_id: int) -> Dict[str, Any]:
    """Получает или создает настройки Training Assistant для пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Проверяем существующие настройки
        async with db.execute("""
            SELECT * FROM ta_user_settings WHERE user_id = ?
        """, (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)

        # Создаем настройки по умолчанию
        await db.execute("""
            INSERT INTO ta_user_settings (user_id) VALUES (?)
        """, (user_id,))
        await db.commit()

        # Возвращаем созданные настройки
        async with db.execute("""
            SELECT * FROM ta_user_settings WHERE user_id = ?
        """, (user_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else {}
