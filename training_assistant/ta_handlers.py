"""
Handlers для Training Assistant
"""

import logging
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from training_assistant.ta_fsm import (
    TrainingPlanStates,
    CorrectionStates,
    RacePreparationStates,
    RaceTacticsStates,
    PsychologistStates,
    ResultPredictionStates
)
from training_assistant.ta_keyboards import *
from training_assistant.ta_queries import *
from training_assistant.services import *
from database.queries import get_trainings_by_custom_period

logger = logging.getLogger(__name__)
router = Router()


async def _get_user_competitions(user_id: int) -> list:
    """Получить соревнования пользователя с результатами"""
    import aiosqlite
    from database.models import DB_PATH

    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT
                    c.title as competition_name,
                    cp.distance,
                    cp.distance_name,
                    cp.result_time,
                    cp.date_registered
                FROM competition_participants cp
                JOIN competitions c ON cp.competition_id = c.id
                WHERE cp.user_id = ?
                ORDER BY cp.date_registered DESC
                LIMIT 20
                """,
                (user_id,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        logger.debug(f"Could not load competitions: {e}")
        return []


async def _get_health_data(user_id: int, start_date: str, end_date: str) -> list:
    """Получить данные о здоровье за период"""
    import aiosqlite
    from database.models import DB_PATH

    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT
                    resting_pulse,
                    weight,
                    sleep_hours,
                    date
                FROM health_metrics
                WHERE user_id = ? AND date BETWEEN ? AND ?
                ORDER BY date DESC
                """,
                (user_id, start_date, end_date)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        logger.debug(f"Could not load health data: {e}")
        return []


# ==================== ГЛАВНОЕ МЕНЮ ====================

@router.message(Command("ai_assistant", "assistant", "ta"))
async def cmd_training_assistant(message: Message):
    """Главное меню Training Assistant"""
    await message.answer(
        "🤖 <b>Training Assistant - Ваш AI тренер</b>\n\n"
        "Выберите, чем я могу помочь:",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "ta:menu")
async def show_ta_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    await callback.message.edit_text(
        "🤖 <b>Training Assistant - Ваш AI тренер</b>\n\n"
        "Выберите, чем я могу помочь:",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "ta:close")
async def close_ta_menu(callback: CallbackQuery, state: FSMContext):
    """Закрыть меню Training Assistant"""
    await state.clear()
    await callback.message.delete()
    await callback.answer("Меню закрыто")


# ==================== 1️⃣ ПЛАН ТРЕНИРОВОК ====================

@router.callback_query(F.data == "ta:plan")
async def start_plan_generation(callback: CallbackQuery, state: FSMContext):
    """Начало создания тренировочного плана"""
    await state.set_state(TrainingPlanStates.waiting_for_sport_type)
    await callback.message.edit_text(
        "🏃 <b>Создание тренировочного плана</b>\n\n"
        "Выберите вид спорта:",
        reply_markup=get_sport_type_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("ta:sport:"), TrainingPlanStates.waiting_for_sport_type)
async def process_sport_type(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора вида спорта"""
    sport_type = callback.data.split(":")[-1]
    await state.update_data(sport_type=sport_type)
    await state.set_state(TrainingPlanStates.waiting_for_plan_duration)

    await callback.message.edit_text(
        "📅 На какой период создать план?",
        reply_markup=get_plan_duration_keyboard()
    )


@router.callback_query(F.data.startswith("ta:duration:"), TrainingPlanStates.waiting_for_plan_duration)
async def process_plan_duration(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора длительности плана"""
    duration = callback.data.split(":")[-1]
    await state.update_data(plan_duration=duration, available_days=[])
    await state.set_state(TrainingPlanStates.waiting_for_available_days)

    await callback.message.edit_text(
        "📆 <b>Выберите доступные дни для тренировок:</b>\n\n"
        "Нажмите на дни, когда вы сможете тренироваться.\n"
        "Можно выбрать несколько дней.\n\n"
        "После выбора нажмите <b>✅ Готово</b>",
        reply_markup=get_available_days_keyboard([]),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("ta:day:"), TrainingPlanStates.waiting_for_available_days)
async def toggle_day_selection(callback: CallbackQuery, state: FSMContext):
    """Toggle выбора дня недели"""
    day = callback.data.split(":")[-1]
    data = await state.get_data()
    selected_days = data.get('available_days', [])

    # Toggle: если день уже выбран - убираем, если нет - добавляем
    if day in selected_days:
        selected_days.remove(day)
    else:
        selected_days.append(day)

    await state.update_data(available_days=selected_days)

    # Обновляем клавиатуру
    await callback.message.edit_text(
        f"📆 <b>Выберите доступные дни для тренировок:</b>\n\n"
        f"Выбрано дней: <b>{len(selected_days)}</b>\n\n"
        f"Нажмите на дни, когда вы сможете тренироваться.\n"
        f"После выбора нажмите <b>✅ Готово</b>",
        reply_markup=get_available_days_keyboard(selected_days),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "ta:days:done", TrainingPlanStates.waiting_for_available_days)
async def process_days_done(callback: CallbackQuery, state: FSMContext):
    """Обработка завершения выбора дней и генерация плана"""
    data = await state.get_data()
    selected_days = data.get('available_days', [])
    user_id = callback.from_user.id

    if not selected_days:
        await callback.answer("⚠️ Выберите хотя бы один день!", show_alert=True)
        return

    # Показываем процесс
    processing_msg = await callback.message.edit_text("⏳ Анализирую ваши данные и генерирую персональный план...")

    try:
        # Собираем данные пользователя для анализа уровня
        end_date = datetime.now()
        start_date_3months = end_date - timedelta(days=90)

        # Получаем тренировки за 3 месяца для анализа
        recent_trainings = await get_trainings_by_custom_period(
            user_id,
            start_date_3months.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )

        # Получаем соревнования пользователя
        competitions = await _get_user_competitions(user_id)

        # Получаем данные о здоровье за последний месяц
        health_data = await _get_health_data(
            user_id,
            (end_date - timedelta(days=30)).strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )

        # Генерируем план с помощью AI (AI сам определит уровень)
        plan_data = await generate_training_plan(
            user_id=user_id,
            sport_type=data['sport_type'],
            plan_duration=data['plan_duration'],
            fitness_level=None,  # AI определит сам
            available_days=selected_days,
            recent_trainings=[dict(t) for t in recent_trainings],
            competitions=competitions[:10] if competitions else [],
            health_data=health_data if health_data else []
        )

        if not plan_data:
            await processing_msg.edit_text(
                "❌ Произошла ошибка при генерации плана. Попробуйте позже.",
                reply_markup=get_back_to_menu_keyboard()
            )
            await state.clear()
            return

        # Сохраняем план в БД
        start_date_str = datetime.now().strftime("%Y-%m-%d")
        end_date_str = (datetime.now() + timedelta(days=7 if data['plan_duration'] == 'week' else 30)).strftime("%Y-%m-%d")

        await save_training_plan(
            user_id=user_id,
            plan_type=data['plan_duration'],
            sport_type=data['sport_type'],
            plan_content=plan_data,
            start_date=start_date_str,
            end_date=end_date_str,
            fitness_level=data['fitness_level'],
            available_days=days,
            ai_explanation=plan_data.get('explanation')
        )

        # Форматируем и выводим план
        response = "✅ <b>Ваш персональный план тренировок готов!</b>\n\n"

        # Добавляем общую информацию
        if plan_data.get('weekly_volume'):
            response += f"📊 <b>Недельный объем:</b> {plan_data['weekly_volume']}\n"
        if plan_data.get('key_workouts'):
            key_workouts = ", ".join(plan_data['key_workouts'][:3])
            response += f"🎯 <b>Ключевые тренировки:</b> {key_workouts}\n"
        response += "\n"

        # Выводим план тренировок
        if 'plan' in plan_data and plan_data['plan']:
            response += "<b>📋 План тренировок:</b>\n\n"
            for i, workout in enumerate(plan_data['plan'][:7], 1):  # Максимум 7 дней
                response += f"<b>{i}. {workout.get('day', 'День ' + str(i))}</b>\n"
                response += f"🏃 {workout.get('workout_type', 'Тренировка')}\n"
                response += f"📏 {workout.get('volume', 'N/A')}"

                if workout.get('target_pace'):
                    response += f" • ⏱ {workout.get('target_pace')}"
                response += f"\n💪 {workout.get('intensity', 'N/A')}\n"

                # Краткое описание (первые 150 символов)
                if workout.get('description'):
                    desc = workout['description'][:150]
                    if len(workout['description']) > 150:
                        desc += "..."
                    response += f"ℹ️ {desc}\n"
                response += "\n"

        # Добавляем краткое объяснение (первые 300 символов)
        if plan_data.get('explanation'):
            explanation = plan_data['explanation']
            # Берем только первый абзац или 300 символов
            first_paragraph = explanation.split('\n\n')[0] if '\n\n' in explanation else explanation
            short_explanation = first_paragraph[:300]
            if len(first_paragraph) > 300:
                short_explanation += "..."
            response += f"💡 <b>Важно:</b> {short_explanation}\n\n"

        # Советы по восстановлению (если есть)
        if plan_data.get('recovery_tips'):
            recovery = plan_data['recovery_tips'][:200]
            if len(plan_data['recovery_tips']) > 200:
                recovery += "..."
            response += f"🔄 <b>Восстановление:</b> {recovery}\n"

        # Добавляем disclaimer
        response += DISCLAIMER_TEXT

        await processing_msg.edit_text(
            response[:4000],  # Telegram limit
            reply_markup=get_back_to_menu_keyboard(),
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Error in plan generation: {e}")
        await processing_msg.edit_text(
            "❌ Ошибка при создании плана. Попробуйте позже.",
            reply_markup=get_back_to_menu_keyboard()
        )

    await state.clear()


# ==================== 2️⃣ КОРРЕКТИРОВКА ТРЕНИРОВКИ ====================

@router.callback_query(F.data == "ta:correction")
async def start_correction(callback: CallbackQuery, state: FSMContext):
    """Начало коррекции тренировки"""
    user_id = callback.from_user.id

    # Получаем последние тренировки
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    recent_trainings = await get_trainings_by_custom_period(
        user_id,
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d')
    )

    if not recent_trainings:
        await callback.message.edit_text(
            "❌ У вас нет тренировок за последнюю неделю.\n"
            "Сначала добавьте тренировку.",
            reply_markup=get_back_to_menu_keyboard()
        )
        return

    await state.update_data(trainings=recent_trainings)
    await state.set_state(CorrectionStates.waiting_for_feedback)

    # Показываем последнюю тренировку
    last_training = recent_trainings[0]
    text = (
        f"📊 <b>Последняя тренировка:</b>\n\n"
        f"Тип: {last_training['type']}\n"
        f"Дата: {last_training['date']}\n"
        f"Дистанция: {last_training.get('distance', 'N/A')} км\n"
        f"Темп: {last_training.get('avg_pace', 'N/A')}\n"
        f"Пульс: {last_training.get('avg_pulse', 'N/A')}\n\n"
        f"Как прошла тренировка?"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_feedback_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("ta:fb:"), CorrectionStates.waiting_for_feedback)
async def process_feedback(callback: CallbackQuery, state: FSMContext):
    """Обработка обратной связи и генерация рекомендаций"""
    feedback = callback.data.split(":")[-1]
    data = await state.get_data()
    user_id = callback.from_user.id

    processing_msg = await callback.message.edit_text("⏳ Анализирую тренировку...")

    try:
        last_training = data['trainings'][0]

        # Анализируем с помощью AI
        correction_data = await analyze_and_correct_workout(
            user_id=user_id,
            training_data=dict(last_training),
            user_feedback=feedback,
            recent_trainings=[dict(t) for t in data['trainings'][:5]]
        )

        if not correction_data:
            await processing_msg.edit_text(
                "❌ Ошибка анализа. Попробуйте позже.",
                reply_markup=get_back_to_menu_keyboard()
            )
            await state.clear()
            return

        # Сохраняем корректировку
        await save_training_correction(
            user_id=user_id,
            training_id=last_training['id'],
            user_feedback=feedback,
            ai_analysis=correction_data.get('analysis', ''),
            ai_recommendation=str(correction_data.get('recommendations', []))
        )

        # Форматируем ответ
        response = "✅ <b>Анализ тренировки</b>\n\n"
        response += f"<b>Анализ:</b>\n{correction_data.get('analysis', 'N/A')}\n\n"

        if 'recommendations' in correction_data:
            response += "<b>Рекомендации:</b>\n"
            for rec in correction_data['recommendations'][:5]:
                response += f"• {rec.get('text', 'N/A')}\n"

        # Добавляем disclaimer
        response += DISCLAIMER_TEXT

        await processing_msg.edit_text(
            response[:4000],
            reply_markup=get_back_to_menu_keyboard(),
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Error in correction: {e}")
        await processing_msg.edit_text(
            "❌ Ошибка анализа.",
            reply_markup=get_back_to_menu_keyboard()
        )

    await state.clear()


# ==================== 3️⃣ ПОДГОТОВКА К СОРЕВНОВАНИЮ ====================

@router.callback_query(F.data == "ta:race_prep")
async def start_race_prep(callback: CallbackQuery, state: FSMContext):
    """Начало подготовки к соревнованию"""
    await state.set_state(RacePreparationStates.selecting_days_before)
    await callback.message.edit_text(
        "🏆 <b>Подготовка к соревнованию</b>\n\n"
        "За сколько дней до старта нужны рекомендации?",
        reply_markup=get_days_before_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("ta:days:"), RacePreparationStates.selecting_days_before)
async def process_race_prep_days(callback: CallbackQuery, state: FSMContext):
    """Генерация рекомендаций по подготовке"""
    days_before = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id

    processing_msg = await callback.message.edit_text("⏳ Готовлю рекомендации...")

    try:
        # TODO: Получить ближайшие соревнования
        # Временная заглушка
        comp = {
            'name': 'Ближайшее соревнование',
            'date': (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d'),
            'distance': 10.0
        }

        # Генерируем рекомендации
        advice = await get_race_preparation_advice(
            user_id=user_id,
            competition_name=comp.get('name', 'N/A'),
            competition_date=comp.get('date', 'N/A'),
            distance=comp.get('distance', 0),
            days_before=days_before
        )

        if advice:
            response = f"✅ <b>Подготовка за {days_before} дней до старта</b>\n\n"
            response += f"<b>Соревнование:</b> {comp.get('name')}\n\n"

            if 'do_list' in advice:
                response += "<b>✅ Что ДЕЛАТЬ:</b>\n"
                for item in advice['do_list'][:5]:
                    response += f"• {item}\n"
                response += "\n"

            if 'dont_list' in advice:
                response += "<b>❌ Что НЕ ДЕЛАТЬ:</b>\n"
                for item in advice['dont_list'][:5]:
                    response += f"• {item}\n"

            # Добавляем disclaimer
            response += DISCLAIMER_TEXT

            await processing_msg.edit_text(
                response[:4000],
                reply_markup=get_back_to_menu_keyboard(),
                parse_mode="HTML"
            )
        else:
            await processing_msg.edit_text(
                "❌ Ошибка генерации рекомендаций.",
                reply_markup=get_back_to_menu_keyboard()
            )

    except Exception as e:
        logger.error(f"Error in race prep: {e}")
        await processing_msg.edit_text(
            "❌ Ошибка.",
            reply_markup=get_back_to_menu_keyboard()
        )

    await state.clear()


# ==================== 4️⃣ ТАКТИКА ЗАБЕГА ====================

@router.callback_query(F.data == "ta:tactics")
async def start_race_tactics(callback: CallbackQuery, state: FSMContext):
    """Начало планирования тактики забега"""
    await state.set_state(RaceTacticsStates.waiting_for_target_time)
    await callback.message.edit_text(
        "🎯 <b>Тактика забега</b>\n\n"
        "Введите целевое время в формате HH:MM:SS или MM:SS\n\n"
        "Например: <i>1:45:00</i> или <i>45:30</i>",
        parse_mode="HTML"
    )


@router.message(RaceTacticsStates.waiting_for_target_time)
async def process_tactics_time(message: Message, state: FSMContext):
    """Генерация тактики забега"""
    target_time = message.text.strip()
    user_id = message.from_user.id

    processing_msg = await message.answer("⏳ Разрабатываю тактику забега...")

    try:
        # Упрощенно берем дистанцию 10 км (в реальности нужно спросить)
        tactics = await generate_race_tactics(
            user_id=user_id,
            distance=10.0,
            target_time=target_time,
            race_type='flat'
        )

        if tactics:
            response = "✅ <b>Тактический план забега</b>\n\n"
            response += f"<b>Стратегия:</b> {tactics.get('pacing_strategy', 'N/A')}\n\n"

            if 'splits' in tactics:
                response += "<b>Сплиты:</b>\n"
                for split in tactics['splits'][:5]:
                    response += f"• {split.get('segment')}: {split.get('target_pace')}\n"

            # Добавляем disclaimer
            response += DISCLAIMER_TEXT

            await processing_msg.edit_text(
                response[:4000],
                reply_markup=get_back_to_menu_keyboard(),
                parse_mode="HTML"
            )
        else:
            await processing_msg.edit_text(
                "❌ Ошибка создания тактики.",
                reply_markup=get_back_to_menu_keyboard()
            )

    except Exception as e:
        logger.error(f"Error in tactics: {e}")
        await processing_msg.edit_text(
            "❌ Ошибка.",
            reply_markup=get_back_to_menu_keyboard()
        )

    await state.clear()


# ==================== 5️⃣ ПСИХОЛОГ ====================

@router.callback_query(F.data == "ta:psychologist")
async def start_psychologist_chat(callback: CallbackQuery, state: FSMContext):
    """Начало диалога с психологом"""
    await state.set_state(PsychologistStates.waiting_for_problem)
    await callback.message.edit_text(
        "🧠 <b>Спортивный психолог</b>\n\n"
        "Расскажите, что вас беспокоит:\n"
        "• Страх перед стартом?\n"
        "• Сомнения в своих силах?\n"
        "• Потеря мотивации?\n"
        "• Другое?\n\n"
        "Напишите сообщение:",
        parse_mode="HTML"
    )


@router.message(PsychologistStates.waiting_for_problem)
async def process_psychologist_message(message: Message, state: FSMContext):
    """Обработка сообщения психологу"""
    user_id = message.from_user.id
    user_message = message.text

    processing_msg = await message.answer("⏳ Обрабатываю...")

    try:
        # Получаем историю диалога
        history = await get_recent_conversations(user_id, 'psychologist', limit=5)

        # Получаем ответ от AI
        ai_response = await chat_with_psychologist(
            user_id=user_id,
            user_message=user_message,
            conversation_history=history
        )

        if ai_response:
            # Сохраняем диалог
            await save_conversation(
                user_id=user_id,
                conversation_type='psychologist',
                user_message=user_message,
                ai_response=ai_response
            )

            # Добавляем disclaimer
            response = ai_response + DISCLAIMER_TEXT

            await processing_msg.edit_text(
                response[:4000],
                reply_markup=get_continue_chat_keyboard(),
                parse_mode="HTML"
            )

            # Переходим в режим продолжения диалога
            await state.set_state(PsychologistStates.in_conversation)
        else:
            await processing_msg.edit_text(
                "❌ Ошибка. Попробуйте позже.",
                reply_markup=get_back_to_menu_keyboard()
            )
            await state.clear()

    except Exception as e:
        logger.error(f"Error in psychologist chat: {e}")
        await processing_msg.edit_text(
            "❌ Ошибка.",
            reply_markup=get_back_to_menu_keyboard()
        )
        await state.clear()


@router.message(PsychologistStates.in_conversation)
async def continue_psychologist_chat(message: Message, state: FSMContext):
    """Продолжение диалога с психологом"""
    # Повторяем логику из process_psychologist_message
    await process_psychologist_message(message, state)


@router.callback_query(F.data == "ta:chat:end", PsychologistStates.in_conversation)
async def end_psychologist_chat(callback: CallbackQuery, state: FSMContext):
    """Завершение диалога"""
    await state.clear()
    await callback.message.edit_text(
        "✅ Рад был помочь! Обращайтесь, если понадобится поддержка.",
        reply_markup=get_back_to_menu_keyboard()
    )


# ==================== 6️⃣ ПРОГНОЗ РЕЗУЛЬТАТА ====================

@router.callback_query(F.data == "ta:prediction")
async def start_prediction(callback: CallbackQuery, state: FSMContext):
    """Начало прогноза результата"""
    await state.set_state(ResultPredictionStates.waiting_for_distance)
    await callback.message.edit_text(
        "🔮 <b>Прогноз результата</b>\n\n"
        "Введите дистанцию в километрах\n\n"
        "Например: <i>10</i> или <i>21.1</i> или <i>42.195</i>",
        parse_mode="HTML"
    )


@router.message(ResultPredictionStates.waiting_for_distance)
async def process_prediction_distance(message: Message, state: FSMContext):
    """Обработка дистанции и генерация прогноза"""
    try:
        distance = float(message.text.strip())
        await state.update_data(distance=distance)
    except ValueError:
        await message.answer("❌ Неверный формат. Введите число (например: 10 или 21.1)")
        return

    user_id = message.from_user.id
    processing_msg = await message.answer("⏳ Анализирую ваши тренировки и делаю прогноз...")

    try:
        # Получаем тренировки за месяц
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        trainings = await get_trainings_by_custom_period(
            user_id,
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )

        if not trainings:
            await processing_msg.edit_text(
                "❌ Недостаточно данных для прогноза.\n"
                "Добавьте больше тренировок.",
                reply_markup=get_back_to_menu_keyboard()
            )
            await state.clear()
            return

        # Генерируем прогноз
        prediction = await predict_race_result(
            user_id=user_id,
            target_distance=distance,
            analysis_period='month',
            training_data=[dict(t) for t in trainings]
        )

        if prediction:
            response = f"✅ <b>Прогноз результата на {distance} км</b>\n\n"

            if 'predictions' in prediction:
                preds = prediction['predictions']
                response += f"🎯 <b>Реалистичный:</b> {preds.get('realistic', 'N/A')}\n"
                response += f"🚀 <b>Оптимистичный:</b> {preds.get('optimistic', 'N/A')}\n"
                response += f"🛡️ <b>Осторожный:</b> {preds.get('conservative', 'N/A')}\n\n"

            response += f"<b>Объяснение:</b>\n{prediction.get('explanation', 'N/A')}"

            # Добавляем disclaimer
            response += DISCLAIMER_TEXT

            await processing_msg.edit_text(
                response[:4000],
                reply_markup=get_back_to_menu_keyboard(),
                parse_mode="HTML"
            )
        else:
            await processing_msg.edit_text(
                "❌ Ошибка создания прогноза.",
                reply_markup=get_back_to_menu_keyboard()
            )

    except Exception as e:
        logger.error(f"Error in prediction: {e}")
        await processing_msg.edit_text(
            "❌ Ошибка.",
            reply_markup=get_back_to_menu_keyboard()
        )

    await state.clear()
