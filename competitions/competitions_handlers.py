"""
Обработчики для раздела соревнований
"""

import logging
from datetime import datetime, date
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.fsm import CompetitionStates
from competitions.competitions_keyboards import (
    get_competitions_main_menu,
    get_competition_card_keyboard,
    get_distance_selection_keyboard,
    get_my_competitions_menu,
    get_my_competition_keyboard,
    get_cancel_keyboard,
    get_result_input_keyboard,
    format_competition_distance,
    format_time_until_competition
)
from competitions.competitions_queries import (
    get_upcoming_competitions,
    get_competition,
    register_for_competition,
    unregister_from_competition,
    is_user_registered,
    get_user_competitions,
    add_competition_result,
    get_competition_participants_count,
    get_user_personal_records
)
from bot.keyboards import get_main_menu_keyboard
from utils.time_formatter import normalize_time

router = Router()
logger = logging.getLogger(__name__)


# ========== ГЛАВНОЕ МЕНЮ СОРЕВНОВАНИЙ ==========

@router.callback_query(F.data == "competitions")
async def show_competitions_menu(callback: CallbackQuery, state: FSMContext):
    """Показать главное меню соревнований"""
    await state.clear()

    text = (
        "🏆 <b>СОРЕВНОВАНИЯ</b>\n\n"
        "Здесь вы можете:\n"
        "• Найти предстоящие марафоны и забеги\n"
        "• Зарегистрироваться на соревнование\n"
        "• Отслеживать свою подготовку\n"
        "• Добавлять результаты\n"
        "• Вести историю участия\n\n"
        "Выберите раздел:"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_competitions_main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "comp:menu")
async def return_to_comp_menu(callback: CallbackQuery, state: FSMContext):
    """Вернуться в главное меню соревнований"""
    await show_competitions_menu(callback, state)


# ========== ПРЕДСТОЯЩИЕ СОРЕВНОВАНИЯ ==========

@router.callback_query(F.data == "comp:upcoming")
async def show_upcoming_competitions(callback: CallbackQuery, state: FSMContext):
    """Показать список предстоящих соревнований"""
    await state.clear()

    competitions = await get_upcoming_competitions(limit=10)

    if not competitions:
        text = (
            "📅 <b>Предстоящие соревнования</b>\n\n"
            "К сожалению, в базе данных пока нет предстоящих соревнований.\n\n"
            "💡 Соревнования загружаются из Russia Running API.\n\n"
            "Вы можете найти соревнование по городу и дате."
        )

        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🔍 Поиск по городу и дате", callback_data="comp:search")
        )
        builder.row(
            InlineKeyboardButton(text="🔍 Найти вручную", callback_data="comp:create_custom")
        )
        builder.row(
            InlineKeyboardButton(text="◀️ Назад", callback_data="comp:menu")
        )

        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    else:
        text = "📅 <b>Предстоящие соревнования</b>\n\n"

        for i, comp in enumerate(competitions[:5], 1):
            # Форматируем дату
            try:
                comp_date = datetime.strptime(comp['date'], '%Y-%m-%d')
                date_str = comp_date.strftime('%d.%m.%Y')
            except:
                date_str = comp['date']

            time_until = format_time_until_competition(comp['date'])

            # Форматируем дистанции
            try:
                import json
                distances = json.loads(comp['distances']) if isinstance(comp['distances'], str) else comp['distances']
                distances_str = ', '.join([format_competition_distance(float(d)) for d in distances])
            except:
                distances_str = 'Дистанции уточняются'

            text += (
                f"{i}. <b>{comp['name']}</b>\n"
                f"   📍 {comp.get('city', 'Город не указан')}\n"
                f"   📅 {date_str} ({time_until})\n"
                f"   🏃 {distances_str}\n\n"
            )

        # Создаём inline клавиатуру с соревнованиями
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        for i, comp in enumerate(competitions[:5], 1):
            builder.row(
                InlineKeyboardButton(
                    text=f"{i}. {comp['name'][:40]}...",
                    callback_data=f"comp:view:{comp['id']}"
                )
            )

        builder.row(
            InlineKeyboardButton(text="🔍 Поиск по городу и дате", callback_data="comp:search")
        )
        builder.row(
            InlineKeyboardButton(text="◀️ Назад", callback_data="comp:menu")
        )

        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )

    await callback.answer()


@router.callback_query(F.data.startswith("comp:view:"))
async def view_competition(callback: CallbackQuery, state: FSMContext):
    """Показать детальную информацию о соревновании"""
    competition_id = int(callback.data.split(":")[2])
    user_id = callback.from_user.id

    comp = await get_competition(competition_id)
    if not comp:
        await callback.answer("❌ Соревнование не найдено", show_alert=True)
        return

    # Проверяем зарегистрирован ли пользователь
    is_registered = await is_user_registered(user_id, competition_id)

    # Получаем количество участников
    participants_count = await get_competition_participants_count(competition_id)

    # Форматируем дату
    try:
        comp_date = datetime.strptime(comp['date'], '%Y-%m-%d')
        date_str = comp_date.strftime('%d %B %Y')
        month_names = {
            1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
            5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
            9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
        }
        date_str = comp_date.strftime(f'%d {month_names[comp_date.month]} %Y')
    except:
        date_str = comp['date']

    time_until = format_time_until_competition(comp['date'])

    # Форматируем дистанции
    try:
        distances = comp.get('distances', [])
        if isinstance(distances, str):
            import json
            distances = json.loads(distances)

        distances_list = []
        for d in distances:
            distances_list.append(f"  • {format_competition_distance(float(d))}")
        distances_str = '\n'.join(distances_list) if distances_list else '  Дистанции уточняются'
    except Exception as e:
        logger.error(f"Error parsing distances: {e}")
        distances_str = '  Дистанции уточняются'

    # Формируем текст карточки
    text = (
        f"🏃 <b>{comp['name']}</b>\n"
        f"{'=' * 40}\n\n"
        f"📅 Дата: {date_str}\n"
        f"⏳ {time_until}\n"
        f"📍 Место: {comp.get('city', 'Не указано')}\n"
        f"🏢 Организатор: {comp.get('organizer', 'Не указан')}\n\n"
        f"🏃 <b>Дистанции:</b>\n{distances_str}\n\n"
    )

    if comp.get('description'):
        text += f"📝 {comp['description']}\n\n"

    if participants_count > 0:
        text += f"👥 Участников из бота: {participants_count}\n\n"

    if is_registered:
        text += "✅ <b>Вы зарегистрированы на это соревнование</b>"
    else:
        text += "ℹ️ Вы можете зарегистрироваться на это соревнование"

    # Создаём клавиатуру
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()

    has_multiple_distances = len(distances) > 1 if distances else False

    if is_registered:
        builder.row(
            InlineKeyboardButton(
                text="✅ Вы зарегистрированы",
                callback_data=f"comp:my_registration:{competition_id}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="❌ Отменить участие",
                callback_data=f"comp:unregister_confirm:{competition_id}"
            )
        )
    else:
        if has_multiple_distances:
            builder.row(
                InlineKeyboardButton(
                    text="✍️ Зарегистрироваться (выбрать дистанцию)",
                    callback_data=f"comp:select_distance:{competition_id}"
                )
            )
        elif distances and len(distances) == 1:
            builder.row(
                InlineKeyboardButton(
                    text="✍️ Зарегистрироваться",
                    callback_data=f"comp:register_single:{competition_id}:{distances[0]}"
                )
            )

    if comp.get('official_url'):
        builder.row(
            InlineKeyboardButton(
                text="🌐 Официальный сайт",
                url=comp['official_url']
            )
        )

    builder.row(
        InlineKeyboardButton(text="◀️ Назад к списку", callback_data="comp:upcoming")
    )

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


# ========== РЕГИСТРАЦИЯ НА СОРЕВНОВАНИЕ ==========

@router.callback_query(F.data.startswith("comp:select_distance:"))
async def select_distance(callback: CallbackQuery, state: FSMContext):
    """Выбор дистанции для регистрации"""
    competition_id = int(callback.data.split(":")[2])

    comp = await get_competition(competition_id)
    if not comp:
        await callback.answer("❌ Соревнование не найдено", show_alert=True)
        return

    try:
        distances = comp.get('distances', [])
        if isinstance(distances, str):
            import json
            distances = json.loads(distances)

        distances = [float(d) for d in distances]
    except:
        await callback.answer("❌ Ошибка получения дистанций", show_alert=True)
        return

    text = (
        f"🏃 <b>{comp['name']}</b>\n\n"
        "Выберите дистанцию, на которую хотите зарегистрироваться:"
    )

    # Создаём клавиатуру с дистанциями
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()

    for distance in sorted(distances, reverse=True):
        builder.row(
            InlineKeyboardButton(
                text=format_competition_distance(distance),
                callback_data=f"comp:register_dist:{competition_id}:{distance}"
            )
        )

    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data=f"comp:view:{competition_id}")
    )

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("comp:register_single:"))
async def register_single_distance(callback: CallbackQuery, state: FSMContext):
    """Регистрация на соревнование с одной дистанцией"""
    parts = callback.data.split(":")
    competition_id = int(parts[2])
    distance = float(parts[3])

    await register_user_for_competition(callback, state, competition_id, distance)


@router.callback_query(F.data.startswith("comp:register_dist:"))
async def register_with_distance(callback: CallbackQuery, state: FSMContext):
    """Регистрация на соревнование с выбранной дистанцией"""
    parts = callback.data.split(":")
    competition_id = int(parts[2])
    distance = float(parts[3])

    await register_user_for_competition(callback, state, competition_id, distance)


async def register_user_for_competition(callback: CallbackQuery, state: FSMContext, competition_id: int, distance: float):
    """Общая функция регистрации пользователя на соревнование"""
    user_id = callback.from_user.id

    comp = await get_competition(competition_id)
    if not comp:
        await callback.answer("❌ Соревнование не найдено", show_alert=True)
        return

    # Регистрируем пользователя
    try:
        await register_for_competition(user_id, competition_id, distance)

        text = (
            f"✅ <b>Вы успешно зарегистрированы!</b>\n\n"
            f"🏃 Соревнование: {comp['name']}\n"
            f"📏 Дистанция: {format_competition_distance(distance)}\n"
            f"📅 Дата: {comp['date']}\n\n"
            f"💪 Желаем удачной подготовки!\n\n"
            f"Вы можете установить целевое время в разделе 'Мои соревнования'."
        )

        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="📊 Установить целевое время",
                callback_data=f"comp:set_target:{competition_id}:{distance}"
            )
        )
        builder.row(
            InlineKeyboardButton(text="🏆 Мои соревнования", callback_data="comp:my")
        )
        builder.row(
            InlineKeyboardButton(text="🔙 Главное меню", callback_data="comp:menu")
        )

        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        await callback.answer("✅ Регистрация успешна!")

    except Exception as e:
        logger.error(f"Error registering user: {e}")
        await callback.answer("❌ Ошибка регистрации. Возможно, вы уже зарегистрированы.", show_alert=True)


# ========== МОИ СОРЕВНОВАНИЯ ==========

@router.callback_query(F.data == "comp:my")
async def show_my_competitions(callback: CallbackQuery, state: FSMContext):
    """Показать предстоящие соревнования пользователя (без деления)"""
    user_id = callback.from_user.id

    competitions = await get_user_competitions(user_id, status_filter='upcoming')

    if not competitions:
        text = (
            "✅ <b>МОИ СОРЕВНОВАНИЯ</b>\n\n"
            "У вас пока нет запланированных соревнований.\n\n"
            "Перейдите в раздел 'Найти соревнования' чтобы зарегистрироваться на забег!"
        )
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🔍 Найти соревнования", callback_data="comp:search")
        )
        builder.row(
            InlineKeyboardButton(text="◀️ Назад", callback_data="comp:menu")
        )

        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    else:
        text = "✅ <b>МОИ СОРЕВНОВАНИЯ</b>\n\n"

        # Импортируем утилиты для форматирования с учетом настроек пользователя
        from competitions.competitions_utils import format_competition_distance as format_dist_with_units, format_competition_date

        for i, comp in enumerate(competitions[:10], 1):
            time_until = format_time_until_competition(comp['date'])

            # Форматируем дистанцию с учетом единиц измерения пользователя
            dist_str = await format_dist_with_units(comp['distance'], user_id)

            # Форматируем дату с учетом настроек пользователя
            date_str = await format_competition_date(comp['date'], user_id)

            # Форматируем целевое время
            target_time = comp.get('target_time')
            if target_time is None or target_time == 'None' or target_time == '':
                target_time_str = 'Нет цели'
            else:
                target_time_str = target_time

            text += (
                f"{i}. <b>{comp['name']}</b>\n"
                f"   📏 {dist_str}\n"
                f"   📅 {date_str} ({time_until})\n"
                f"   🎯 Цель: {target_time_str}\n\n"
            )

        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        for comp in competitions[:10]:
            builder.row(
                InlineKeyboardButton(
                    text=f"{comp['name'][:40]}..." if len(comp['name']) > 40 else comp['name'],
                    callback_data=f"comp:my_view:{comp['id']}:{comp['distance']}"
                )
            )

        builder.row(
            InlineKeyboardButton(text="◀️ Назад", callback_data="comp:menu")
        )

        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )

    await callback.answer()


@router.callback_query(F.data.startswith("comp:my_view:"))
async def view_my_competition(callback: CallbackQuery, state: FSMContext):
    """Просмотр деталей моего соревнования"""
    user_id = callback.from_user.id
    parts = callback.data.split(":")
    competition_id = int(parts[2])
    distance = float(parts[3])

    # Получаем информацию о соревновании
    competition = await get_competition(competition_id)

    if not competition:
        await callback.answer("❌ Соревнование не найдено", show_alert=True)
        return

    # Получаем данные участия пользователя
    from competitions.competitions_queries import get_user_competitions
    user_comps = await get_user_competitions(user_id)

    # Находим нужную регистрацию
    registration = None
    for comp in user_comps:
        if comp['id'] == competition_id and comp.get('distance') == distance:
            registration = comp
            break

    if not registration:
        await callback.answer("❌ Регистрация не найдена", show_alert=True)
        return

    # Форматируем информацию с учетом настроек пользователя
    from competitions.competitions_utils import format_competition_distance as format_dist_with_units, format_competition_date

    time_until = format_time_until_competition(competition['date'])
    dist_str = await format_dist_with_units(distance, user_id)
    date_str = await format_competition_date(competition['date'], user_id)

    # Форматируем целевое время
    target_time = registration.get('target_time')
    if target_time is None or target_time == 'None' or target_time == '':
        target_time_str = 'Нет цели'
    else:
        target_time_str = target_time

    text = (
        f"🏃 <b>{competition['name']}</b>\n\n"
        f"📍 Город: {competition.get('city', 'не указан')}\n"
        f"📅 Дата: {date_str}\n"
        f"⏰ До старта: {time_until}\n\n"
        f"📏 Ваша дистанция: {dist_str}\n"
        f"🎯 Целевое время: {target_time_str}\n\n"
    )

    if competition.get('description'):
        text += f"ℹ️ {competition['description']}\n\n"

    # Создаём клавиатуру
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()

    # Кнопки действий
    builder.row(
        InlineKeyboardButton(
            text="✏️ Изменить целевое время",
            callback_data=f"comp:edit_target:{competition_id}:{distance}"
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="❌ Отменить участие",
            callback_data=f"comp:cancel_registration:{competition_id}:{distance}"
        )
    )

    if competition.get('official_url'):
        builder.row(
            InlineKeyboardButton(
                text="🌐 Официальный сайт",
                url=competition['official_url']
            )
        )

    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="comp:my")
    )

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


# ========== МОИ РЕЗУЛЬТАТЫ ==========

@router.callback_query(F.data == "comp:my_results")
async def show_my_results(callback: CallbackQuery, state: FSMContext):
    """Показать личные рекорды и статистику пользователя"""
    user_id = callback.from_user.id

    # Получаем статистику
    from competitions.statistics_queries import get_user_competition_stats
    stats = await get_user_competition_stats(user_id)

    # Получаем личные рекорды
    records = await get_user_personal_records(user_id)

    # Получаем завершенные соревнования
    finished_comps = await get_user_competitions(user_id, status_filter='finished')

    if not records and not finished_comps:
        text = (
            "🏅 <b>МОИ РЕЗУЛЬТАТЫ</b>\n\n"
            "У вас пока нет личных рекордов.\n\n"
            "Добавьте результаты своих соревнований, чтобы отслеживать прогресс!"
        )
    else:
        text = "🏅 <b>МОИ РЕЗУЛЬТАТЫ</b>\n\n"

        # Добавляем краткую статистику
        if stats and stats['total_competitions'] > 0:
            text += "📊 <b>СТАТИСТИКА</b>\n"
            text += f"Соревнований: {stats['total_completed']}"

            if stats.get('total_distance_km', 0) > 0:
                text += f" • Дистанция: {stats['total_distance_km']:.1f} км"
            text += "\n\n"

        # Личные рекорды
        if records:
            text += "🏆 <b>ЛИЧНЫЕ РЕКОРДЫ</b>\n\n"

            # Сортируем по дистанции
            sorted_records = sorted(records.items(), key=lambda x: x[0])

            for distance, record in sorted_records:
                dist_name = format_competition_distance(distance)
                text += f"🏃 <b>{dist_name}</b>: {record['best_time']}"
                if record.get('competition_name'):
                    comp_name_short = record['competition_name'][:20] + "..." if len(record['competition_name']) > 20 else record['competition_name']
                    text += f" ({comp_name_short})"
                text += "\n"

            text += "\n"

        # Завершенные соревнования
        if finished_comps:
            text += "🏁 <b>ЗАВЕРШЕННЫЕ СОРЕВНОВАНИЯ</b>\n\n"

            for i, comp in enumerate(finished_comps[:5], 1):
                dist_str = format_competition_distance(comp['distance'])

                text += f"{i}. <b>{comp['name']}</b>\n"
                text += f"   📏 {dist_str} • 📅 {comp['date']}\n"

                if comp.get('finish_time'):
                    normalized_time = normalize_time(comp['finish_time'])
                    result_line = f"   ⏱️ {normalized_time}"
                    if comp.get('place_overall'):
                        result_line += f" • 🏆 {comp['place_overall']} место"
                    text += result_line + "\n"

                text += "\n"

            if len(finished_comps) > 5:
                text += f"<i>... и ещё {len(finished_comps) - 5} соревнований</i>\n"

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()

    # Добавляем кнопки для завершенных соревнований
    if finished_comps:
        for comp in finished_comps[:5]:
            builder.row(
                InlineKeyboardButton(
                    text=f"📊 {comp['name'][:35]}..." if len(comp['name']) > 35 else f"📊 {comp['name']}",
                    callback_data=f"comp:view_result:{comp['id']}"
                )
            )

    # Кнопка добавления прошедшего соревнования
    builder.row(
        InlineKeyboardButton(text="➕ Добавить прошедшее соревнование", callback_data="comp:add_past")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="comp:menu")
    )

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


# ========== ДОБАВЛЕНИЕ РЕЗУЛЬТАТА ==========

@router.callback_query(F.data.startswith("comp:add_result:"))
async def start_add_result(callback: CallbackQuery, state: FSMContext):
    """Начать процесс добавления результата"""
    competition_id = int(callback.data.split(":")[-1])
    user_id = callback.message.chat.id

    # Получаем информацию о соревновании
    comp = await get_competition(competition_id)
    if not comp:
        await callback.answer("❌ Соревнование не найдено", show_alert=True)
        return

    # Сохраняем ID соревнования в состоянии
    await state.update_data(result_competition_id=competition_id)

    # Запрашиваем время
    text = (
        f"🏆 <b>{comp['name']}</b>\n\n"
        "Введите ваше финишное время в формате ЧЧ:ММ:СС или ММ:СС\n"
        "Например: 1:23:45 или 42:30"
    )

    await callback.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(CompetitionStates.waiting_for_finish_time)
    await callback.answer()


@router.message(CompetitionStates.waiting_for_finish_time)
async def process_finish_time(message: Message, state: FSMContext):
    """Обработать финишное время"""
    from utils.time_formatter import validate_time_format

    if message.text == "❌ Отмена":
        await message.answer(
            "❌ Добавление результата отменено",
            reply_markup=get_main_menu_keyboard()
        )
        await state.clear()
        return

    time_text = message.text.strip()

    # Валидация формата
    if not validate_time_format(time_text):
        await message.answer(
            "❌ Некорректный формат времени. Используйте формат ЧЧ:ММ:СС или ММ:СС\n"
            "Например: 1:23:45 или 42:30"
        )
        return

    # Нормализуем и сохраняем время
    normalized_time = normalize_time(time_text)
    await state.update_data(result_finish_time=normalized_time)

    # Запрашиваем место в общем зачёте
    await message.answer(
        "Введите ваше место в общем зачёте (число)\n"
        "Или нажмите \"Пропустить\" если не хотите указывать",
        reply_markup=get_result_input_keyboard()
    )
    await state.set_state(CompetitionStates.waiting_for_place_overall)


@router.message(CompetitionStates.waiting_for_place_overall)
async def process_place_overall(message: Message, state: FSMContext):
    """Обработать место в общем зачёте"""

    if message.text == "❌ Отмена":
        await message.answer(
            "❌ Добавление результата отменено",
            reply_markup=get_main_menu_keyboard()
        )
        await state.clear()
        return

    if message.text == "⏭️ Пропустить":
        await state.update_data(result_place_overall=None)
    else:
        try:
            place = int(message.text.strip())
            if place <= 0:
                await message.answer("❌ Место должно быть положительным числом")
                return
            await state.update_data(result_place_overall=place)
        except ValueError:
            await message.answer(
                "❌ Некорректное значение. Введите число или нажмите \"Пропустить\""
            )
            return

    # Запрашиваем место в категории
    await message.answer(
        "Введите ваше место в возрастной категории (число)\n"
        "Или нажмите \"Пропустить\" если не хотите указывать",
        reply_markup=get_result_input_keyboard()
    )
    await state.set_state(CompetitionStates.waiting_for_place_age)


@router.message(CompetitionStates.waiting_for_place_age)
async def process_place_age_category(message: Message, state: FSMContext):
    """Обработать место в возрастной категории"""

    if message.text == "❌ Отмена":
        await message.answer(
            "❌ Добавление результата отменено",
            reply_markup=get_main_menu_keyboard()
        )
        await state.clear()
        return

    if message.text == "⏭️ Пропустить":
        await state.update_data(result_place_age=None)
    else:
        try:
            place = int(message.text.strip())
            if place <= 0:
                await message.answer("❌ Место должно быть положительным числом")
                return
            await state.update_data(result_place_age=place)
        except ValueError:
            await message.answer(
                "❌ Некорректное значение. Введите число или нажмите \"Пропустить\""
            )
            return

    # Сохраняем результат
    data = await state.get_data()
    user_id = message.from_user.id
    competition_id = data['result_competition_id']

    # Получаем дистанцию из регистрации
    from competitions.competitions_queries import get_user_competition_registration
    registration = await get_user_competition_registration(user_id, competition_id)
    if not registration:
        await message.answer(
            "❌ Не найдена регистрация на это соревнование",
            reply_markup=get_main_menu_keyboard()
        )
        await state.clear()
        return

    distance = registration['distance']

    # Добавляем результат
    success = await add_competition_result(
        user_id=user_id,
        competition_id=competition_id,
        distance=distance,
        finish_time=data['result_finish_time'],
        place_overall=data.get('result_place_overall'),
        place_age_category=data.get('result_place_age')
    )

    if success:
        comp = await get_competition(competition_id)
        text = (
            "✅ <b>РЕЗУЛЬТАТ ДОБАВЛЕН!</b>\n\n"
            f"🏆 <b>{comp['name']}</b>\n"
            f"⏱️ Время: {data['result_finish_time']}\n"
        )
        if data.get('result_place_overall'):
            text += f"🏆 Место общее: {data['result_place_overall']}\n"
        if data.get('result_place_age'):
            text += f"🏆 Место в категории: {data['result_place_age']}\n"

        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await message.answer(
            "❌ Ошибка при добавлении результата",
            reply_markup=get_main_menu_keyboard()
        )

    await state.clear()


# Импортируем InlineKeyboardButton для использования в коде
from aiogram.types import InlineKeyboardButton

# Примечание: обработчик comp:search находится в search_competitions_handlers.py
# Примечание: обработчик comp:statistics находится в custom_competitions_handlers.py
# Примечание: обработчик comp:create_custom находится в custom_competitions_handlers.py
