"""
Handlers для Training Assistant
"""

import logging
import re
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile, ReplyKeyboardRemove
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
from training_assistant.ta_pdf_export import create_training_plan_pdf
from database.queries import get_trainings_by_custom_period

logger = logging.getLogger(__name__)
router = Router()


def clean_html_response(text: str) -> str:
    """
    Очищает HTML ответ от неподдерживаемых Telegram тегов
    """
    if not text:
        return text

    text = re.sub(r'<br\s*/?\s*>', '\n', text, flags=re.IGNORECASE)

    text = re.sub(r'</p>\s*<p>', '\n\n', text, flags=re.IGNORECASE)

    text = re.sub(r'</?p>', '', text, flags=re.IGNORECASE)

    return text


def validate_time_format(time_str: str) -> tuple[bool, str]:
    """
    Проверяет формат времени (HH:MM:SS или MM:SS)

    Returns:
        tuple: (is_valid, normalized_time)
    """
    if not time_str:
        return False, ""

    time_str = time_str.strip()

    pattern_hhmmss = r'^(\d{1,2}):([0-5]\d):([0-5]\d)$'
    pattern_mmss = r'^([0-5]?\d):([0-5]\d)$'

    match = re.match(pattern_hhmmss, time_str)
    if match:
        hours, minutes, seconds = match.groups()
        return True, f"{int(hours)}:{minutes}:{seconds}"

    match = re.match(pattern_mmss, time_str)
    if match:
        minutes, seconds = match.groups()
        return True, f"{int(minutes)}:{seconds}"

    return False, ""


async def _get_user_competitions(user_id: int) -> list:
    """Получить соревнования пользователя с результатами"""
    import aiosqlite
    import os
    DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

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
    import os
    DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

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



@router.message(Command("ai_assistant", "assistant", "ta"))
async def cmd_training_assistant(message: Message):
    """Главное меню Training Assistant"""
    menu_msg = await message.answer(
        "🤖 <b>Training Assistant - Ваш AI тренер</b>\n\n"
        "Выберите, чем я могу помочь:",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )
    try:
        temp_msg = await message.answer(".", reply_markup=ReplyKeyboardRemove())
        await temp_msg.delete()
    except:
        pass  


@router.callback_query(F.data == "ta:menu")
async def show_ta_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()

    menu_text = (
        "🤖 <b>Training Assistant - Ваш AI тренер</b>\n\n"
        "Выберите, чем я могу помочь:"
    )

    if callback.message.text or callback.message.caption:
        try:
            await callback.message.edit_text(
                menu_text,
                reply_markup=get_main_menu_keyboard(),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.debug(f"Could not edit message, sending new: {e}")
            try:
                await callback.message.delete()
            except:
                pass
            await callback.message.answer(
                menu_text,
                reply_markup=get_main_menu_keyboard(),
                parse_mode="HTML"
            )
    else:
        try:
            await callback.message.delete()
        except:
            pass
        await callback.message.answer(
            menu_text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML"
        )

    try:
        temp_msg = await callback.message.answer(".", reply_markup=ReplyKeyboardRemove())
        await temp_msg.delete()
    except:
        pass  

    await callback.answer()


@router.callback_query(F.data == "ta:close")
async def close_ta_menu(callback: CallbackQuery, state: FSMContext):
    """Закрыть меню Training Assistant"""
    await state.clear()
    await callback.message.delete()
    await callback.answer("Меню закрыто")



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

    if day in selected_days:
        selected_days.remove(day)
    else:
        selected_days.append(day)

    await state.update_data(available_days=selected_days)

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

    processing_msg = await callback.message.edit_text("⏳ Анализирую ваши данные и генерирую персональный план...")

    try:
        end_date = datetime.now()
        start_date_3months = end_date - timedelta(days=90)

        recent_trainings = await get_trainings_by_custom_period(
            user_id,
            start_date_3months.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )

        competitions = await _get_user_competitions(user_id)

        health_data = await _get_health_data(
            user_id,
            (end_date - timedelta(days=30)).strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )

        plan_data = await generate_training_plan(
            user_id=user_id,
            sport_type=data['sport_type'],
            plan_duration=data['plan_duration'],
            fitness_level=None,  
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

        start_date_str = datetime.now().strftime("%Y-%m-%d")
        end_date_str = (datetime.now() + timedelta(days=7 if data['plan_duration'] == 'week' else 30)).strftime("%Y-%m-%d")

        await save_training_plan(
            user_id=user_id,
            plan_type=data['plan_duration'],
            sport_type=data['sport_type'],
            plan_content=plan_data,
            start_date=start_date_str,
            end_date=end_date_str,
            fitness_level=None,  
            available_days=selected_days,
            ai_explanation=plan_data.get('explanation')
        )

        if not plan_data.get('plan') and plan_data.get('raw_response'):
            response = "❌ <b>Ошибка генерации плана</b>\n\n"
            response += plan_data.get('explanation', 'Не удалось сгенерировать план.')
            response += "\n\nПопробуйте еще раз."

            await processing_msg.edit_text(
                response,
                reply_markup=get_back_to_menu_keyboard(),
                parse_mode="HTML"
            )
        else:
            try:
                pdf_buffer = await create_training_plan_pdf(
                    plan_data=plan_data,
                    sport_type=data['sport_type'],
                    plan_duration=data['plan_duration'],
                    available_days=selected_days
                )

                sport_names = {
                    'run': 'бег',
                    'swim': 'плавание',
                    'bike': 'велоспорт',
                    'triathlon': 'триатлон'
                }
                sport_name = sport_names.get(data['sport_type'], data['sport_type'])
                duration_names = {
                    'week': 'неделя',
                    'month': 'месяц'
                }
                duration_name = duration_names.get(data['plan_duration'], data['plan_duration'])
                filename = f"plan_{sport_name}_{duration_name}_{datetime.now().strftime('%Y%m%d')}.pdf"

                pdf_file = BufferedInputFile(
                    pdf_buffer.read(),
                    filename=filename
                )

                await processing_msg.delete()

                caption = "✅ <b>Ваш персональный план тренировок готов!</b>\n\n"
                if plan_data.get('weekly_volume'):
                    caption += f"📊 Недельный объем: {plan_data['weekly_volume']}\n"
                if plan_data.get('key_workouts'):
                    key_workouts = ", ".join(plan_data['key_workouts'][:3])
                    caption += f"🎯 Ключевые тренировки: {key_workouts}\n"
                caption += "\n📄 Полный план см. в прикрепленном PDF"

                await callback.message.answer_document(
                    pdf_file,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=get_back_to_menu_keyboard()
                )

            except Exception as e:
                logger.error(f"Error generating PDF: {e}")
                response = "✅ <b>Ваш персональный план тренировок готов!</b>\n\n"

                if plan_data.get('weekly_volume'):
                    response += f"📊 <b>Недельный объем:</b> {plan_data['weekly_volume']}\n"
                if plan_data.get('key_workouts'):
                    key_workouts = ", ".join(plan_data['key_workouts'][:3])
                    response += f"🎯 <b>Ключевые тренировки:</b> {key_workouts}\n"
                response += "\n"

                if 'plan' in plan_data and plan_data['plan']:
                    response += "<b>📋 План тренировок:</b>\n\n"
                    for i, workout in enumerate(plan_data['plan'][:7], 1):  
                        response += f"<b>{i}. {workout.get('day', 'День ' + str(i))}</b>\n"
                        response += f"🏃 {workout.get('workout_type', 'Тренировка')}\n"
                        response += f"📏 {workout.get('volume', 'N/A')}"

                        if workout.get('target_pace'):
                            response += f" • ⏱ {workout.get('target_pace')}"
                        response += f"\n💪 {workout.get('intensity', 'N/A')}\n"

                        if workout.get('description'):
                            desc = workout['description'][:150]
                            if len(workout['description']) > 150:
                                desc += "..."
                            response += f"ℹ️ {desc}\n"
                        response += "\n"

                if plan_data.get('explanation') and not plan_data.get('raw_response'):
                    explanation = plan_data['explanation']
                    first_paragraph = explanation.split('\n\n')[0] if '\n\n' in explanation else explanation
                    short_explanation = first_paragraph[:300]
                    if len(first_paragraph) > 300:
                        short_explanation += "..."
                    response += f"💡 <b>Важно:</b> {short_explanation}\n\n"

                if plan_data.get('recovery_tips'):
                    recovery = plan_data['recovery_tips'][:200]
                    if len(plan_data['recovery_tips']) > 200:
                        recovery += "..."
                    response += f"🔄 <b>Восстановление:</b> {recovery}\n"

                response += DISCLAIMER_TEXT

                await processing_msg.edit_text(
                    response[:4000],  
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



@router.callback_query(F.data == "ta:race_prep")
async def start_race_prep(callback: CallbackQuery, state: FSMContext):
    """Начало подготовки к соревнованию - выбор соревнования"""
    user_id = callback.from_user.id

    from competitions.competitions_queries import get_user_competitions
    user_comps = await get_user_competitions(user_id, status_filter='upcoming')

    if not user_comps:
        await callback.message.edit_text(
            "❌ У вас нет предстоящих соревнований.\n\n"
            "Сначала зарегистрируйтесь на соревнование в разделе 'Соревнования'.",
            reply_markup=get_back_to_menu_keyboard(),
            parse_mode="HTML"
        )
        return

    await state.update_data(user_competitions=user_comps)
    await state.set_state(RacePreparationStates.selecting_competition)

    from training_assistant.ta_keyboards import get_user_competitions_keyboard
    keyboard = await get_user_competitions_keyboard(user_comps, "race_prep", user_id)
    await callback.message.edit_text(
        "🏆 <b>Подготовка к соревнованию</b>\n\n"
        "Выберите соревнование:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("ta:race_prep:comp:"), RacePreparationStates.selecting_competition)
async def select_competition_for_prep(callback: CallbackQuery, state: FSMContext):
    """Выбор соревнования для подготовки"""
    comp_id = callback.data.split(":")[-1]
    data = await state.get_data()
    user_comps = data.get('user_competitions', [])

    selected_comp = next((c for c in user_comps if str(c.get('id', c.get('competition_id'))) == comp_id), None)

    if not selected_comp:
        await callback.answer("Соревнование не найдено", show_alert=True)
        return

    await state.update_data(selected_competition=selected_comp)
    await state.set_state(RacePreparationStates.selecting_days_before)

    comp_title = selected_comp.get('name', selected_comp.get('title', 'Соревнование'))

    await callback.message.edit_text(
        f"🏆 <b>{comp_title}</b>\n\n"
        "За сколько дней до старта нужны рекомендации?",
        reply_markup=get_days_before_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("ta:days:"), RacePreparationStates.selecting_days_before)
async def process_race_prep_days(callback: CallbackQuery, state: FSMContext):
    """Генерация рекомендаций по подготовке"""
    days_before = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    data = await state.get_data()
    selected_comp = data.get('selected_competition')

    if not selected_comp:
        await callback.answer("Ошибка: соревнование не выбрано", show_alert=True)
        return

    comp_name = selected_comp.get('name', selected_comp.get('title', 'Соревнование'))
    comp_date = selected_comp.get('date', selected_comp.get('begin_date', 'N/A'))

    distance = selected_comp.get('distance') or selected_comp.get('selected_distance', 10.0)
    if isinstance(distance, str):
        try:
            distance = float(distance)
        except:
            distance = 10.0

    try:
        from utils.unit_converter import format_distance_for_user
        distance_str = await format_distance_for_user(float(distance), user_id)
    except:
        distance_str = f"{distance} км"

    target_time = selected_comp.get('target_time')

    if not target_time:
        await state.update_data(days_before=days_before)
        await state.set_state(RacePreparationStates.waiting_for_target_time)
        await callback.message.edit_text(
            f"🏆 <b>Подготовка к соревнованию</b>\n\n"
            f"<b>Соревнование:</b> {comp_name}\n"
            f"<b>Дистанция:</b> {distance_str}\n\n"
            f"Введите целевое время в формате:\n"
            f"• <b>Ч:ММ:СС</b> (например: <i>1:45:00</i> = 1 час 45 минут)\n"
            f"• <b>ММ:СС</b> (например: <i>45:30</i> = 45 минут 30 секунд)",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )
        return

    processing_msg = await callback.message.edit_text("⏳ Готовлю рекомендации...")

    try:

        advice = await get_race_preparation_advice(
            user_id=user_id,
            competition_name=comp_name,
            competition_date=comp_date,
            distance=distance,
            days_before=days_before,
            target_time=target_time  
        )

        if advice:
            try:
                from utils.unit_converter import format_distance_for_user
                from utils.date_formatter import DateFormatter, get_user_date_format
                distance_str = await format_distance_for_user(float(distance), user_id)
                date_format = await get_user_date_format(user_id)
                comp_date_str = DateFormatter.format_date(comp_date, date_format)
            except:
                distance_str = f"{distance} км"
                comp_date_str = comp_date

            response = f"✅ <b>Подготовка за {days_before} дней до старта</b>\n\n"
            response += f"<b>Соревнование:</b> {comp_name}\n"
            response += f"<b>Дата:</b> {comp_date_str}\n"
            response += f"<b>Дистанция:</b> {distance_str}\n\n"

            if 'raw_response' in advice or 'advice' in advice:
                advice_text = advice.get('raw_response') or advice.get('advice', '')
                advice_text = clean_html_response(advice_text)
                response += advice_text + "\n\n"
            else:
                if 'do_list' in advice:
                    response += "<b>✅ Что ДЕЛАТЬ:</b>\n"
                    for item in advice['do_list'][:5]:
                        response += f"• {item}\n"
                    response += "\n"

                if 'dont_list' in advice:
                    response += "<b>❌ Что НЕ ДЕЛАТЬ:</b>\n"
                    for item in advice['dont_list'][:5]:
                        response += f"• {item}\n"
                    response += "\n"

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


@router.message(RacePreparationStates.waiting_for_target_time)
async def process_race_prep_target_time(message: Message, state: FSMContext):
    """Обработка целевого времени для подготовки к соревнованию"""
    target_time_input = message.text.strip()
    user_id = message.from_user.id
    data = await state.get_data()
    selected_comp = data.get('selected_competition')
    days_before = data.get('days_before')

    if not selected_comp or not days_before:
        await message.answer("Ошибка: данные не найдены", reply_markup=get_back_to_menu_keyboard())
        await state.clear()
        return

    is_valid, target_time = validate_time_format(target_time_input)
    if not is_valid:
        await message.answer(
            "❌ <b>Неверный формат времени!</b>\n\n"
            "Пожалуйста, введите время в одном из форматов:\n"
            "• <b>Ч:ММ:СС</b> (например: <i>1:45:00</i> = 1 час 45 минут)\n"
            "• <b>ММ:СС</b> (например: <i>45:30</i> = 45 минут 30 секунд)\n\n"
            "Попробуйте еще раз:",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        return

    processing_msg = await message.answer("⏳ Готовлю рекомендации...")

    try:
        comp_name = selected_comp.get('name', selected_comp.get('title', 'Соревнование'))
        comp_date = selected_comp.get('date', selected_comp.get('begin_date', 'N/A'))
        distance = selected_comp.get('distance') or selected_comp.get('selected_distance', 10.0)

        if isinstance(distance, str):
            try:
                distance = float(distance)
            except:
                distance = 10.0

        advice = await get_race_preparation_advice(
            user_id=user_id,
            competition_name=comp_name,
            competition_date=comp_date,
            distance=distance,
            days_before=days_before,
            target_time=target_time
        )

        if advice:
            try:
                from utils.unit_converter import format_distance_for_user
                from utils.date_formatter import DateFormatter, get_user_date_format
                distance_str = await format_distance_for_user(float(distance), user_id)
                date_format = await get_user_date_format(user_id)
                comp_date_str = DateFormatter.format_date(comp_date, date_format)
            except:
                distance_str = f"{distance} км"
                comp_date_str = comp_date

            response = f"✅ <b>Подготовка за {days_before} дней до старта</b>\n\n"
            response += f"<b>Соревнование:</b> {comp_name}\n"
            response += f"<b>Дата:</b> {comp_date_str}\n"
            response += f"<b>Дистанция:</b> {distance_str}\n\n"

            if 'raw_response' in advice or 'advice' in advice:
                advice_text = advice.get('raw_response') or advice.get('advice', '')
                advice_text = clean_html_response(advice_text)
                response += advice_text + "\n\n"
            else:
                if 'do_list' in advice:
                    response += "<b>✅ Что ДЕЛАТЬ:</b>\n"
                    for item in advice['do_list'][:5]:
                        response += f"• {item}\n"
                    response += "\n"

                if 'dont_list' in advice:
                    response += "<b>❌ Что НЕ ДЕЛАТЬ:</b>\n"
                    for item in advice['dont_list'][:5]:
                        response += f"• {item}\n"
                    response += "\n"

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
        logger.error(f"Error in race prep with target time: {e}")
        await processing_msg.edit_text(
            "❌ Ошибка.",
            reply_markup=get_back_to_menu_keyboard()
        )

    await state.clear()



@router.callback_query(F.data == "ta:tactics")
async def start_race_tactics(callback: CallbackQuery, state: FSMContext):
    """Начало планирования тактики забега - выбор соревнования"""
    user_id = callback.from_user.id

    from competitions.competitions_queries import get_user_competitions
    user_comps = await get_user_competitions(user_id, status_filter='upcoming')

    if not user_comps:
        await callback.message.edit_text(
            "❌ У вас нет предстоящих соревнований.\n\n"
            "Сначала зарегистрируйтесь на соревнование в разделе 'Соревнования'.",
            reply_markup=get_back_to_menu_keyboard(),
            parse_mode="HTML"
        )
        return

    await state.update_data(user_competitions=user_comps)
    await state.set_state(RaceTacticsStates.selecting_competition)

    from training_assistant.ta_keyboards import get_user_competitions_keyboard
    keyboard = await get_user_competitions_keyboard(user_comps, "tactics", user_id)
    await callback.message.edit_text(
        "🎯 <b>Тактика забега</b>\n\n"
        "Выберите соревнование:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("ta:tactics:comp:"), RaceTacticsStates.selecting_competition)
async def select_competition_for_tactics(callback: CallbackQuery, state: FSMContext):
    """Выбор соревнования для тактики"""
    comp_id = callback.data.split(":")[-1]
    data = await state.get_data()
    user_comps = data.get('user_competitions', [])
    user_id = callback.from_user.id

    selected_comp = next((c for c in user_comps if str(c.get('id', c.get('competition_id'))) == comp_id), None)

    if not selected_comp:
        await callback.answer("Соревнование не найдено", show_alert=True)
        return

    target_time_from_db = selected_comp.get('target_time')

    await state.update_data(selected_competition=selected_comp)

    comp_name = selected_comp.get('name', selected_comp.get('title', 'Соревнование'))
    distance_km = selected_comp.get('distance') or selected_comp.get('selected_distance', 10.0)

    try:
        from utils.unit_converter import format_distance_for_user
        distance_str = await format_distance_for_user(float(distance_km), user_id)
    except:
        distance_str = f"{distance_km} км"

    if target_time_from_db:
        await callback.message.edit_text("⏳ Разрабатываю тактику забега...")

        try:
            distance = float(distance_km) if isinstance(distance_km, str) else distance_km

            tactics = await generate_race_tactics(
                user_id=user_id,
                distance=distance,
                target_time=target_time_from_db,
                race_type='flat'
            )

            if tactics:
                response = f"✅ <b>Тактический план забега</b>\n\n"
                response += f"<b>Соревнование:</b> {comp_name}\n"
                response += f"<b>Дистанция:</b> {distance_str}\n"
                response += f"<b>Целевое время:</b> {target_time_from_db}\n\n"

                if 'raw_response' in tactics or 'tactics' in tactics:
                    tactics_text = tactics.get('raw_response') or tactics.get('tactics', '')
                    tactics_text = clean_html_response(tactics_text)
                    response += tactics_text + "\n\n"
                else:
                    response += f"<b>Стратегия:</b> {tactics.get('pacing_strategy', 'N/A')}\n\n"

                    if 'splits' in tactics:
                        response += "<b>Сплиты:</b>\n"
                        for split in tactics['splits'][:5]:
                            segment = split.get('segment', 'N/A')
                            pace = split.get('target_pace', 'N/A')
                            response += f"• {segment}: {pace}\n"
                        response += "\n"

                response += DISCLAIMER_TEXT

                await callback.message.edit_text(
                    response[:4000],
                    reply_markup=get_back_to_menu_keyboard(),
                    parse_mode="HTML"
                )
            else:
                await callback.message.edit_text(
                    "❌ Ошибка создания тактики.",
                    reply_markup=get_back_to_menu_keyboard()
                )
        except Exception as e:
            logger.error(f"Error in tactics: {e}")
            await callback.message.edit_text(
                "❌ Ошибка.",
                reply_markup=get_back_to_menu_keyboard()
            )

        await state.clear()
    else:
        await state.set_state(RaceTacticsStates.waiting_for_target_time)
        await callback.message.edit_text(
            f"🎯 <b>Тактика забега</b>\n\n"
            f"<b>Соревнование:</b> {comp_name}\n"
            f"<b>Дистанция:</b> {distance_str}\n\n"
            f"Введите целевое время в формате:\n"
            f"• <b>Ч:ММ:СС</b> (например: <i>1:45:00</i> = 1 час 45 минут)\n"
            f"• <b>ММ:СС</b> (например: <i>45:30</i> = 45 минут 30 секунд)",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )


@router.message(RaceTacticsStates.waiting_for_target_time)
async def process_tactics_time(message: Message, state: FSMContext):
    """Генерация тактики забега"""
    target_time_input = message.text.strip()
    user_id = message.from_user.id
    data = await state.get_data()
    selected_comp = data.get('selected_competition')

    if not selected_comp:
        await message.answer("Ошибка: соревнование не выбрано", reply_markup=get_back_to_menu_keyboard())
        return

    is_valid, target_time = validate_time_format(target_time_input)
    if not is_valid:
        await message.answer(
            "❌ <b>Неверный формат времени!</b>\n\n"
            "Пожалуйста, введите время в одном из форматов:\n"
            "• <b>Ч:ММ:СС</b> (например: <i>1:45:00</i> = 1 час 45 минут)\n"
            "• <b>ММ:СС</b> (например: <i>45:30</i> = 45 минут 30 секунд)\n\n"
            "Попробуйте еще раз:",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        return

    processing_msg = await message.answer("⏳ Разрабатываю тактику забега...")

    try:
        comp_name = selected_comp.get('name', selected_comp.get('title', 'Соревнование'))
        distance = selected_comp.get('distance') or selected_comp.get('selected_distance', 10.0)

        if isinstance(distance, str):
            try:
                distance = float(distance)
            except:
                distance = 10.0

        tactics = await generate_race_tactics(
            user_id=user_id,
            distance=distance,
            target_time=target_time,
            race_type='flat'
        )

        if tactics:
            try:
                from utils.unit_converter import format_distance_for_user
                distance_str = await format_distance_for_user(float(distance), user_id)
            except:
                distance_str = f"{distance} км"

            response = f"✅ <b>Тактический план забега</b>\n\n"
            response += f"<b>Соревнование:</b> {comp_name}\n"
            response += f"<b>Дистанция:</b> {distance_str}\n"
            response += f"<b>Целевое время:</b> {target_time}\n\n"

            if 'raw_response' in tactics or 'tactics' in tactics:
                tactics_text = tactics.get('raw_response') or tactics.get('tactics', '')
                tactics_text = clean_html_response(tactics_text)
                response += tactics_text + "\n\n"
            else:
                response += f"<b>Стратегия:</b> {tactics.get('pacing_strategy', 'N/A')}\n\n"

                if 'splits' in tactics:
                    response += "<b>Сплиты:</b>\n"
                    for split in tactics['splits'][:5]:
                        segment = split.get('segment', 'N/A')
                        pace = split.get('target_pace', 'N/A')
                        response += f"• {segment}: {pace}\n"
                    response += "\n"

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
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(PsychologistStates.waiting_for_problem)
async def process_psychologist_message(message: Message, state: FSMContext):
    """Обработка сообщения психологу"""
    user_id = message.from_user.id
    user_message = message.text

    processing_msg = await message.answer("⏳ Обрабатываю...")

    try:
        history = await get_recent_conversations(user_id, 'psychologist', limit=5)

        ai_response = await chat_with_psychologist(
            user_id=user_id,
            user_message=user_message,
            conversation_history=history
        )

        if ai_response:
            await save_conversation(
                user_id=user_id,
                conversation_type='psychologist',
                user_message=user_message,
                ai_response=ai_response
            )

            response = ai_response + DISCLAIMER_TEXT

            await processing_msg.edit_text(
                response[:4000],
                reply_markup=get_back_to_menu_keyboard(),
                parse_mode="HTML"
            )

            await state.clear()
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



@router.callback_query(F.data == "ta:prediction")
async def start_prediction(callback: CallbackQuery, state: FSMContext):
    """Начало прогноза результата"""
    await state.set_state(ResultPredictionStates.waiting_for_distance)
    await callback.message.edit_text(
        "🔮 <b>Прогноз результата</b>\n\n"
        "Введите дистанцию в километрах\n\n"
        "Например: <i>10</i> или <i>21.1</i> или <i>42.195</i>",
        reply_markup=get_cancel_keyboard(),
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

        prediction = await predict_race_result(
            user_id=user_id,
            target_distance=distance,
            analysis_period='month',
            training_data=[dict(t) for t in trainings]
        )

        if prediction:
            try:
                from utils.unit_converter import format_distance_for_user
                distance_str = await format_distance_for_user(float(distance), user_id)
            except:
                distance_str = f"{distance} км"

            response = f"✅ <b>Прогноз результата на {distance_str}</b>\n\n"

            if 'predictions' in prediction:
                preds = prediction['predictions']
                response += f"🎯 <b>Реалистичный:</b> {preds.get('realistic', 'N/A')}\n"
                response += f"🚀 <b>Оптимистичный:</b> {preds.get('optimistic', 'N/A')}\n"
                response += f"🛡️ <b>Осторожный:</b> {preds.get('conservative', 'N/A')}\n\n"

            response += f"<b>Объяснение:</b>\n{prediction.get('explanation', 'N/A')}"

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
