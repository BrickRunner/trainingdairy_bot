"""
Обработчики для пользовательских соревнований
Функции:
- Создание своего соревнования
- Напоминания о соревнованиях
- Ввод результатов
- Предложения от тренера
"""

import logging
import json
from datetime import datetime, timedelta, date
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.fsm import CompetitionStates
from competitions.competitions_queries import (
    add_competition,
    register_for_competition,
    get_competition,
    add_competition_result
)

logger = logging.getLogger(__name__)
router = Router()


# ========== СОЗДАНИЕ ПОЛЬЗОВАТЕЛЬСКОГО СОРЕВНОВАНИЯ ==========

@router.callback_query(F.data == "comp:create_custom")
async def start_create_custom_competition(callback: CallbackQuery, state: FSMContext):
    """Начать создание пользовательского соревнования"""

    text = (
        "➕ <b>СОЗДАНИЕ СВОЕГО СОРЕВНОВАНИЯ</b>\n\n"
        "Вы можете добавить своё соревнование вручную.\n\n"
        "📝 <b>Шаг 1 из 5</b>\n\n"
        "Введите <b>название</b> соревнования:\n"
        "<i>Например: Московский марафон 2026</i>"
    )

    await callback.message.edit_text(text, parse_mode="HTML")
    await state.set_state(CompetitionStates.waiting_for_comp_name)
    await callback.answer()


@router.message(CompetitionStates.waiting_for_comp_name)
async def process_comp_name(message: Message, state: FSMContext):
    """Обработать название соревнования"""

    comp_name = message.text.strip()

    if not comp_name or len(comp_name) < 3:
        await message.answer(
            "❌ Название слишком короткое. Введите название минимум из 3 символов."
        )
        return

    # Сохраняем название
    await state.update_data(comp_name=comp_name)

    text = (
        f"✅ Название: <b>{comp_name}</b>\n\n"
        f"📝 <b>Шаг 2 из 5</b>\n\n"
        f"Введите <b>дату</b> соревнования:\n"
        f"<i>Формат: ДД.ММ.ГГГГ\nНапример: 25.09.2026</i>"
    )

    await message.answer(text, parse_mode="HTML")
    await state.set_state(CompetitionStates.waiting_for_comp_date)


@router.message(CompetitionStates.waiting_for_comp_date)
async def process_comp_date(message: Message, state: FSMContext):
    """Обработать дату соревнования"""

    date_text = message.text.strip()

    # Парсим дату
    try:
        comp_date = datetime.strptime(date_text, '%d.%m.%Y').date()

        # Проверяем что дата в будущем
        if comp_date < date.today():
            await message.answer(
                "❌ Дата соревнования должна быть в будущем.\n"
                "Введите корректную дату:"
            )
            return

    except ValueError:
        await message.answer(
            "❌ Неверный формат даты.\n"
            "Используйте формат: ДД.ММ.ГГГГ\n"
            "Например: 25.09.2026"
        )
        return

    # Сохраняем дату
    await state.update_data(comp_date=comp_date.strftime('%Y-%m-%d'))

    # Создаём клавиатуру с типами
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏃 Бег", callback_data="comptype:running"))
    builder.row(InlineKeyboardButton(text="🏊 Плавание", callback_data="comptype:swimming"))
    builder.row(InlineKeyboardButton(text="🚴 Велоспорт", callback_data="comptype:cycling"))
    builder.row(InlineKeyboardButton(text="🏊‍♂️🚴‍♂️🏃 Триатлон", callback_data="comptype:triathlon"))
    builder.row(InlineKeyboardButton(text="⛰️ Трейл", callback_data="comptype:trail"))

    text = (
        f"✅ Дата: <b>{comp_date.strftime('%d.%m.%Y')}</b>\n\n"
        f"📝 <b>Шаг 3 из 5</b>\n\n"
        f"Выберите <b>вид спорта</b>:"
    )

    await message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await state.set_state(CompetitionStates.waiting_for_comp_type)


@router.callback_query(F.data.startswith("comptype:"), CompetitionStates.waiting_for_comp_type)
async def process_comp_type(callback: CallbackQuery, state: FSMContext):
    """Обработать тип соревнования"""

    comp_type_map = {
        "running": "бег",
        "swimming": "плавание",
        "cycling": "велоспорт",
        "triathlon": "триатлон",
        "trail": "трейл"
    }

    comp_type_key = callback.data.split(":")[1]
    comp_type = comp_type_map.get(comp_type_key, "бег")

    # Сохраняем тип
    await state.update_data(comp_type=comp_type)

    text = (
        f"✅ Вид спорта: <b>{comp_type}</b>\n\n"
        f"📝 <b>Шаг 4 из 5</b>\n\n"
        f"Введите <b>дистанцию</b>:\n"
        f"<i>Например: 42.195 (для марафона)\n"
        f"Или: 21.1 (для полумарафона)\n"
        f"Или: 10 (для 10 км)</i>"
    )

    await callback.message.edit_text(text, parse_mode="HTML")
    await state.set_state(CompetitionStates.waiting_for_comp_distance)
    await callback.answer()


@router.message(CompetitionStates.waiting_for_comp_distance)
async def process_comp_distance(message: Message, state: FSMContext):
    """Обработать дистанцию соревнования"""

    distance_text = message.text.strip().replace(',', '.')

    try:
        distance = float(distance_text)

        if distance <= 0 or distance > 500:
            await message.answer(
                "❌ Дистанция должна быть от 0.1 до 500 км.\n"
                "Введите корректное значение:"
            )
            return

    except ValueError:
        await message.answer(
            "❌ Неверный формат дистанции.\n"
            "Введите число (например: 42.195 или 10):"
        )
        return

    # Сохраняем дистанцию
    await state.update_data(comp_distance=distance)

    # Определяем название дистанции
    if distance == 42.195 or distance == 42.2:
        distance_name = "Марафон (42.195 км)"
    elif distance == 21.1 or distance == 21.0975:
        distance_name = "Полумарафон (21.1 км)"
    elif distance == 10:
        distance_name = "10 км"
    elif distance == 5:
        distance_name = "5 км"
    else:
        distance_name = f"{distance} км"

    text = (
        f"✅ Дистанция: <b>{distance_name}</b>\n\n"
        f"📝 <b>Шаг 5 из 5</b>\n\n"
        f"Введите <b>целевое время</b>:\n"
        f"<i>Формат: ЧЧ:ММ:СС\n"
        f"Например: 03:30:00 (3 часа 30 минут)\n"
        f"Или: 00:45:00 (45 минут)</i>\n\n"
        f"Или отправьте <b>0</b>, если не хотите устанавливать цель сейчас."
    )

    await message.answer(text, parse_mode="HTML")
    await state.set_state(CompetitionStates.waiting_for_comp_target)


@router.message(CompetitionStates.waiting_for_comp_target)
async def process_comp_target_and_create(message: Message, state: FSMContext):
    """Обработать целевое время и создать соревнование"""

    target_text = message.text.strip()
    target_time = None

    if target_text != "0":
        # Парсим время
        try:
            # Проверяем формат ЧЧ:ММ:СС
            time_parts = target_text.split(':')
            if len(time_parts) == 3:
                hours, minutes, seconds = map(int, time_parts)
                if 0 <= hours <= 24 and 0 <= minutes < 60 and 0 <= seconds < 60:
                    target_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                else:
                    raise ValueError
            elif len(time_parts) == 2:
                # Формат ММ:СС
                minutes, seconds = map(int, time_parts)
                if 0 <= minutes < 60 and 0 <= seconds < 60:
                    target_time = f"00:{minutes:02d}:{seconds:02d}"
                else:
                    raise ValueError
            else:
                raise ValueError
        except (ValueError, AttributeError):
            await message.answer(
                "❌ Неверный формат времени.\n"
                "Используйте формат: ЧЧ:ММ:СС (например: 03:30:00)\n"
                "Или отправьте 0, чтобы пропустить."
            )
            return

    # Получаем сохранённые данные
    data = await state.get_data()
    comp_name = data.get('comp_name')
    comp_date = data.get('comp_date')
    comp_type = data.get('comp_type')
    comp_distance = data.get('comp_distance')

    user_id = message.from_user.id

    # Создаём соревнование в БД
    try:
        competition_data = {
            'name': comp_name,
            'date': comp_date,
            'type': comp_type,
            'distances': json.dumps([comp_distance]),
            'status': 'upcoming',
            'created_by': user_id,
            'is_official': 0,  # Пользовательское соревнование
            'registration_status': 'open'
        }

        comp_id = await add_competition(competition_data)

        # Регистрируем пользователя на соревнование
        await register_for_competition(
            user_id=user_id,
            competition_id=comp_id,
            distance=comp_distance,
            target_time=target_time
        )

        logger.info(f"User {user_id} created custom competition {comp_id}: {comp_name}")

        # Создаём напоминания
        from competitions.reminder_scheduler import create_reminders_for_competition
        await create_reminders_for_competition(user_id, comp_id, comp_date)

        # Форматируем сообщение об успехе
        text = (
            "✅ <b>Соревнование создано!</b>\n\n"
            f"🏆 <b>{comp_name}</b>\n"
            f"📅 Дата: {datetime.strptime(comp_date, '%Y-%m-%d').strftime('%d.%m.%Y')}\n"
            f"🏃 Вид: {comp_type}\n"
            f"📏 Дистанция: {comp_distance} км\n"
        )

        if target_time:
            text += f"🎯 Цель: {target_time}\n"

        text += (
            "\n🔔 <b>Напоминания настроены</b>\n"
            "Вы будете получать напоминания:\n"
            "• За 30 дней до старта\n"
            "• За 14 дней до старта\n"
            "• За 7 дней до старта\n"
            "• За 3 дня до старта\n"
            "• За 1 день до старта\n"
            "• На следующий день после старта (для ввода результатов)\n\n"
            "Соревнование добавлено в раздел 'Мои соревнования'"
        )

        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="✅ Мои соревнования", callback_data="comp:my"))
        builder.row(InlineKeyboardButton(text="🔙 Главное меню", callback_data="comp:menu"))

        await message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())

        # Очищаем состояние
        await state.clear()

    except Exception as e:
        logger.error(f"Error creating custom competition: {e}")
        await message.answer(
            "❌ Произошла ошибка при создании соревнования.\n"
            "Попробуйте ещё раз позже.",
            parse_mode="HTML"
        )
        await state.clear()


# ========== СТАТИСТИКА СОРЕВНОВАНИЙ ==========

@router.callback_query(F.data == "comp:statistics")
async def show_competition_statistics(callback: CallbackQuery):
    """Показать статистику соревнований пользователя"""

    from competitions.statistics_queries import get_user_competition_stats

    user_id = callback.from_user.id
    stats = await get_user_competition_stats(user_id)

    if not stats or stats['total_competitions'] == 0:
        text = (
            "📊 <b>СТАТИСТИКА СОРЕВНОВАНИЙ</b>\n\n"
            "У вас пока нет завершённых соревнований с результатами.\n\n"
            "Участвуйте в соревнованиях и добавляйте результаты, "
            "чтобы отслеживать свой прогресс!"
        )
    else:
        text = "📊 <b>СТАТИСТИКА СОРЕВНОВАНИЙ</b>\n\n"

        text += f"🏆 <b>Всего соревнований:</b> {stats['total_competitions']}\n"
        text += f"✅ <b>Завершено:</b> {stats['total_completed']}\n\n"

        if stats['total_marathons'] > 0:
            text += f"🏃 <b>Марафоны (42.2 км):</b> {stats['total_marathons']}\n"
            if stats.get('best_marathon_time'):
                text += f"   ⏱️ Лучшее время: {stats['best_marathon_time']}\n"
            text += "\n"

        if stats['total_half_marathons'] > 0:
            text += f"🏃 <b>Полумарафоны (21.1 км):</b> {stats['total_half_marathons']}\n"
            if stats.get('best_half_marathon_time'):
                text += f"   ⏱️ Лучшее время: {stats['best_half_marathon_time']}\n"
            text += "\n"

        if stats['total_10k'] > 0:
            text += f"🏃 <b>10 км:</b> {stats['total_10k']}\n"
            if stats.get('best_10k_time'):
                text += f"   ⏱️ Лучшее время: {stats['best_10k_time']}\n"
            text += "\n"

        if stats['total_5k'] > 0:
            text += f"🏃 <b>5 км:</b> {stats['total_5k']}\n"
            if stats.get('best_5k_time'):
                text += f"   ⏱️ Лучшее время: {stats['best_5k_time']}\n"
            text += "\n"

        if stats.get('total_distance_km', 0) > 0:
            text += f"📏 <b>Общая дистанция:</b> {stats['total_distance_km']:.1f} км\n"

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏅 Мои результаты", callback_data="comp:my_results"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="comp:menu"))

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()
