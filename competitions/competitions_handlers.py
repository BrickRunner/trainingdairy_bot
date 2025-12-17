"""
Обработчики для раздела соревнований
"""

import logging
from datetime import datetime, date
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, ReplyKeyboardRemove
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
    format_time_until_competition,
    format_qualification
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
    get_user_personal_records,
    get_user_competition_registration
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

    user_id = callback.from_user.id
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

        from utils.date_formatter import DateFormatter

        for i, comp in enumerate(competitions[:5], 1):
            # Форматируем дату
            try:
                date_str = DateFormatter.format_date(comp['date'], user_date_format)
            except:
                date_str = comp['date']

            time_until = format_time_until_competition(comp['date'])

            # Форматируем дистанции
            try:
                import json
                from competitions.competitions_utils import format_competition_distance as format_dist_with_units
                distances = json.loads(comp['distances']) if isinstance(comp['distances'], str) else comp['distances']
                distances_formatted = [await format_dist_with_units(float(d), user_id) for d in distances]
                distances_str = ', '.join(distances_formatted)
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
        from competitions.competitions_utils import format_competition_distance as format_dist_with_units
        distances = comp.get('distances', [])
        if isinstance(distances, str):
            import json
            distances = json.loads(distances)

        distances_list = []
        for d in distances:
            formatted_dist = await format_dist_with_units(float(d), user_id)
            distances_list.append(f"  • {formatted_dist}")
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
    user_id = callback.from_user.id

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
    from competitions.competitions_utils import format_competition_distance as format_dist_with_units
    builder = InlineKeyboardBuilder()

    for distance in sorted(distances, reverse=True):
        dist_text = await format_dist_with_units(distance, user_id)
        builder.row(
            InlineKeyboardButton(
                text=dist_text,
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

        # Создаём напоминания о соревновании
        from competitions.reminder_scheduler import create_reminders_for_competition
        from competitions.competitions_utils import format_competition_distance as format_dist_with_units
        await create_reminders_for_competition(user_id, competition_id, comp['date'])

        dist_text = await format_dist_with_units(distance, user_id)
        text = (
            f"✅ <b>Вы успешно зарегистрированы!</b>\n\n"
            f"🏃 Соревнование: {comp['name']}\n"
            f"📏 Дистанция: {dist_text}\n"
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
    import logging
    logger = logging.getLogger(__name__)

    user_id = callback.from_user.id
    logger.info(f"show_my_competitions called for user_id={user_id}")

    competitions = await get_user_competitions(user_id, status_filter='upcoming')
    logger.info(f"Got {len(competitions)} upcoming competitions for user {user_id}")

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

        try:
            await callback.message.edit_text(
                text,
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
            logger.info("Successfully showed 'no competitions' message")
        except Exception as e:
            logger.error(f"Error editing message (no competitions): {e}")
            # Fallback: send new message
            await callback.message.answer(
                text,
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
    else:
        text = "✅ <b>МОИ СОРЕВНОВАНИЯ</b>\n\n"

        # Импортируем утилиты для форматирования с учетом настроек пользователя
        from competitions.competitions_utils import format_competition_distance as format_dist_with_units, format_competition_date
        from database.queries import get_user_settings
        from utils.unit_converter import safe_convert_distance_name

        # Получаем настройки пользователя один раз
        settings = await get_user_settings(user_id)
        distance_unit = settings.get('distance_unit', 'км')

        # Показываем ВСЕ соревнования (без ограничения на 10)
        for i, comp in enumerate(competitions, 1):
            time_until = format_time_until_competition(comp['date'])

            # Получаем название дистанции и конвертируем его
            distance_value = comp.get('distance', 0)
            distance_name = comp.get('distance_name')  # Сначала пробуем получить из БД

            # Если distance_name нет в БД, ищем в массиве distances
            if not distance_name and comp.get('distances') and isinstance(comp['distances'], list):
                for dist_obj in comp['distances']:
                    # Проверяем, что dist_obj - это словарь
                    if isinstance(dist_obj, dict):
                        if dist_obj.get('distance') == distance_value:
                            distance_name = dist_obj.get('name', '')
                            break

                # Если не нашли по значению и distance_value = 0, берем первую дистанцию
                if not distance_name and distance_value == 0:
                    for dist_obj in comp['distances']:
                        if isinstance(dist_obj, dict):
                            distance_name = dist_obj.get('name', '')
                            distance_value = dist_obj.get('distance', 0)
                            break

            # Если название найдено и содержит сложную дистанцию, конвертируем его
            if distance_name:
                # Проверяем, не является ли distance_name просто числом без единиц
                import re
                if re.match(r'^\d+(\.\d+)?$', distance_name.strip()):
                    # Это просто число - добавляем единицы измерения
                    dist_str = f"{distance_name} {distance_unit}"
                else:
                    dist_str = safe_convert_distance_name(distance_name, distance_unit)
            elif distance_value is not None and distance_value > 0:
                # Если есть числовое значение, форматируем его
                dist_str = await format_dist_with_units(distance_value, user_id)
            else:
                # Если ничего нет, показываем "Не указана"
                dist_str = "Не указана"

            # Форматируем дату с учетом настроек пользователя
            date_str = await format_competition_date(comp['date'], user_id)

            # Форматируем целевое время
            target_time = comp.get('target_time')
            if target_time is None or target_time == 'None' or target_time == '':
                target_time_str = 'Нет цели'
                target_pace_str = ''
            else:
                target_time_str = target_time
                # Рассчитываем темп для целевого времени
                from utils.time_formatter import calculate_pace_with_unit
                target_pace = await calculate_pace_with_unit(target_time, comp['distance'], user_id)
                target_pace_str = f" ({target_pace})" if target_pace else ''

            text += (
                f"{i}. <b>{comp['name']}</b>\n"
                f"   📏 {dist_str}\n"
                f"   📅 {date_str} ({time_until})\n"
                f"   🎯 Цель: {target_time_str}{target_pace_str}\n\n"
            )

        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        # Создаем кнопки для ВСЕХ соревнований (без ограничения на 10)
        for comp in competitions:
            # Используем 0 если distance = None
            distance_for_callback = comp.get('distance') or 0
            builder.row(
                InlineKeyboardButton(
                    text=f"{comp['name'][:40]}..." if len(comp['name']) > 40 else comp['name'],
                    callback_data=f"comp:my_view:{comp['id']}:{distance_for_callback}"
                )
            )

        builder.row(
            InlineKeyboardButton(text="◀️ Назад", callback_data="comp:menu")
        )

        try:
            await callback.message.edit_text(
                text,
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
            logger.info(f"Successfully showed {len(competitions)} competitions")
        except Exception as e:
            logger.error(f"Error editing message (with competitions): {e}")
            logger.error(f"Message text length: {len(text)}, competitions count: {len(competitions)}")
            # Fallback: send new message
            await callback.message.answer(
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
    # Для HeroLeague distance может быть None или 0, поэтому ищем более гибко
    registration = None
    for comp in user_comps:
        comp_distance = comp.get('distance')
        # Сравниваем ID и дистанцию, учитывая что оба могут быть None/0
        if comp['id'] == competition_id:
            # Если обе дистанции None или 0, считаем совпадением
            if (comp_distance == distance) or \
               (comp_distance in (None, 0) and distance in (None, 0)):
                registration = comp
                break

    if not registration:
        # Если не нашли с точным совпадением дистанции, попробуем найти по ID
        # (для случаев когда у соревнования только одна регистрация)
        registrations_for_comp = [c for c in user_comps if c['id'] == competition_id]
        if len(registrations_for_comp) == 1:
            registration = registrations_for_comp[0]
        else:
            await callback.answer("❌ Регистрация не найдена", show_alert=True)
            return

    # Форматируем информацию с учетом настроек пользователя
    from competitions.competitions_utils import format_competition_distance as format_dist_with_units, format_competition_date
    from database.queries import get_user_settings
    from utils.unit_converter import safe_convert_distance_name

    time_until = format_time_until_competition(competition['date'])

    # Получаем distance_name из регистрации (для мультиспортивных событий)
    distance_name = registration.get('distance_name')

    if distance_name:
        # Если есть название дистанции (для мультиспортивных), конвертируем его
        settings = await get_user_settings(user_id)
        distance_unit = settings.get('distance_unit', 'км') if settings else 'км'

        # Проверяем, не является ли distance_name просто числом без единиц
        import re
        if re.match(r'^\d+(\.\d+)?$', distance_name.strip()):
            # Это просто число - добавляем единицы измерения
            dist_str = f"{distance_name} {distance_unit}"
        else:
            dist_str = safe_convert_distance_name(distance_name, distance_unit)
    elif distance is not None and distance > 0:
        # Если только числовое значение, форматируем его
        dist_str = await format_dist_with_units(distance, user_id)
    else:
        # Если дистанция не указана (HeroLeague с ручным вводом)
        dist_str = registration.get('distance_name', 'Не указана')

    date_str = await format_competition_date(competition['date'], user_id)

    # Форматируем целевое время
    target_time = registration.get('target_time')

    # DEBUG: Логируем для отладки
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"DEBUG: target_time = {target_time}, type = {type(target_time)}")

    if target_time is None or target_time == 'None' or target_time == '':
        target_time_str = 'Нет цели'
        target_pace_str = ''
    else:
        target_time_str = target_time
        # Рассчитываем темп для целевого времени
        from utils.time_formatter import calculate_pace_with_unit
        target_pace = await calculate_pace_with_unit(target_time, distance, user_id)
        logger.info(f"DEBUG: target_pace calculated = {target_pace}")
        target_pace_str = f"⚡ Целевой темп: {target_pace}\n" if target_pace else ''
        logger.info(f"DEBUG: target_pace_str = {target_pace_str}")

    text = (
        f"🏃 <b>{competition['name']}</b>\n\n"
        f"📍 Город: {competition.get('city', 'не указан')}\n"
        f"📅 Дата: {date_str}\n"
        f"⏰ До старта: {time_until}\n\n"
        f"📏 Ваша дистанция: {dist_str}\n"
        f"🎯 Целевое время: {target_time_str}\n"
        f"{target_pace_str}"
    )

    if competition.get('description'):
        text += f"ℹ️ {competition['description']}\n\n"

    # Создаём клавиатуру
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from datetime import datetime
    builder = InlineKeyboardBuilder()

    # Проверяем, прошло ли соревнование
    try:
        comp_date = datetime.strptime(competition['date'], '%Y-%m-%d').date()
        today = datetime.now().date()
        is_finished = comp_date < today
    except:
        is_finished = False

    # Если соревнование прошло и результата нет - показываем кнопку добавления
    has_result = registration.get('finish_time') is not None

    if is_finished:
        if not has_result:
            builder.row(
                InlineKeyboardButton(
                    text="🏆 Добавить результат",
                    callback_data=f"comp:add_result:{competition_id}"
                )
            )
        else:
            builder.row(
                InlineKeyboardButton(
                    text="📊 Посмотреть результат",
                    callback_data=f"comp:view_result:{competition_id}"
                )
            )
            builder.row(
                InlineKeyboardButton(
                    text="✏️ Изменить результат",
                    callback_data=f"comp:edit_result:{competition_id}"
                )
            )
    else:
        # Для предстоящих соревнований
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


@router.callback_query(F.data.startswith("comp:view_result:"))
async def view_competition_result(callback: CallbackQuery, state: FSMContext):
    """Просмотр результата соревнования"""
    competition_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id

    # Получаем информацию о соревновании и результате
    from competitions.competitions_queries import get_user_competitions
    user_comps = await get_user_competitions(user_id, competition_id=competition_id)

    if not user_comps:
        await callback.answer("❌ Результат не найден", show_alert=True)
        return

    comp = user_comps[0]
    competition = await get_competition(competition_id)

    if not competition:
        await callback.answer("❌ Соревнование не найдено", show_alert=True)
        return

    # Форматируем результат
    from competitions.competitions_utils import format_competition_distance as format_dist_with_units, format_competition_date
    from utils.date_formatter import get_user_date_format, DateFormatter
    from database.queries import get_user_settings
    from utils.unit_converter import safe_convert_distance_name

    user_date_format = await get_user_date_format(user_id)

    # Получаем distance_name из результата (для мультиспортивных событий)
    distance_name = comp.get('distance_name')

    if distance_name:
        # Если есть название дистанции (для мультиспортивных), конвертируем его
        settings = await get_user_settings(user_id)
        distance_unit = settings.get('distance_unit', 'км') if settings else 'км'
        dist_str = safe_convert_distance_name(distance_name, distance_unit)
    else:
        # Если только числовое значение, форматируем его
        dist_str = await format_dist_with_units(comp['distance'], user_id)

    date_str = await format_competition_date(comp['date'], user_id)

    # Рассчитываем темп
    from utils.time_formatter import calculate_pace_with_unit
    pace = await calculate_pace_with_unit(comp['finish_time'], comp['distance'], user_id)

    text = (
        f"🏆 <b>{competition['name']}</b>\n\n"
        f"📅 Дата: {date_str}\n"
        f"📏 Дистанция: {dist_str}\n"
        f"⏱️ Время: {normalize_time(comp['finish_time'])}\n"
    )

    if pace:
        text += f"⚡ Темп: {pace}\n"

    if comp.get('place_overall'):
        text += f"🏆 Место общее: {comp['place_overall']}\n"
    if comp.get('place_age_category'):
        text += f"🏅 Место в категории: {comp['place_age_category']}\n"
    if comp.get('qualification'):
        text += f"🎖️ Разряд: {format_qualification(comp['qualification'])}\n"
    if comp.get('heart_rate'):
        text += f"❤️ Средний пульс: {comp['heart_rate']} уд/мин\n"

    # Кнопка возврата к карточке соревнования
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="◀️ Назад к событию", callback_data=f"comp:my_view:{competition_id}:{comp['distance']}")
    )

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("comp:edit_result:"))
async def edit_competition_result(callback: CallbackQuery, state: FSMContext):
    """Начать изменение результата соревнования"""
    competition_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id

    # Получаем информацию о соревновании
    competition = await get_competition(competition_id)
    if not competition:
        await callback.answer("❌ Соревнование не найдено", show_alert=True)
        return

    # Сохраняем ID соревнования в состоянии для редактирования
    await state.update_data(edit_result_competition_id=competition_id)

    # Запрашиваем новое время
    text = (
        f"🏆 <b>{competition['name']}</b>\n\n"
        "✏️ Введите новое финишное время в формате ЧЧ:ММ:СС или ММ:СС или Ч:М:С\n"
        "Можно указать сотые: ЧЧ:ММ:СС.сс\n\n"
        "Примеры:\n"
        "• 1:23:45.50\n"
        "• 42:30.25\n"
        "• 1:23:45\n"
        "• 2:0:0"
    )

    await callback.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(CompetitionStates.editing_finish_time)
    await callback.answer()


@router.message(CompetitionStates.editing_finish_time)
async def process_edited_finish_time(message: Message, state: FSMContext):
    """Обработать отредактированное финишное время"""
    from utils.time_formatter import validate_time_format

    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "❌ Изменение результата отменено",
            reply_markup=ReplyKeyboardRemove()
        )
        # Возврат в меню соревнований
        await message.answer(
            "🏆 <b>СОРЕВНОВАНИЯ</b>\n\n"
            "Выберите раздел:",
            parse_mode="HTML",
            reply_markup=get_competitions_main_menu()
        )
        return

    time_text = message.text.strip()

    # Валидация формата
    if not validate_time_format(time_text):
        await message.answer(
            "❌ Некорректный формат времени.\n"
            "Используйте формат ЧЧ:ММ:СС.сс или ММ:СС.сс или Ч:М:С\n\n"
            "Примеры: 1:23:45.50 или 42:30.25 или 1:23:45 или 2:0:0"
        )
        return

    # Нормализуем и обновляем время
    normalized_time = normalize_time(time_text)
    data = await state.get_data()
    competition_id = data['edit_result_competition_id']
    user_id = message.from_user.id

    # Обновляем результат
    from competitions.competitions_queries import update_competition_result
    success = await update_competition_result(
        user_id=user_id,
        competition_id=competition_id,
        finish_time=normalized_time
    )

    await state.clear()

    if success:
        # Получаем дистанцию для редиректа
        from competitions.competitions_queries import get_user_competition_registration
        registration = await get_user_competition_registration(user_id, competition_id)

        if registration:
            distance = registration['distance']

            await message.answer(
                f"✅ Результат обновлён: {normalized_time}",
                reply_markup=ReplyKeyboardRemove()
            )

            # Автоматический редирект к карточке соревнования
            from types import SimpleNamespace
            new_callback = SimpleNamespace(
                message=message,
                from_user=message.from_user,
                data=f"comp:my_view:{competition_id}:{distance}",
                answer=lambda text="", show_alert=False: None
            )
            await view_my_competition(new_callback, None)
        else:
            await message.answer(
                "✅ Результат обновлён, но не удалось найти регистрацию",
                reply_markup=get_main_menu_keyboard()
            )
    else:
        await message.answer(
            "❌ Ошибка при обновлении результата",
            reply_markup=get_main_menu_keyboard()
        )


@router.callback_query(F.data.startswith("comp:edit_target:"))
async def edit_target_time(callback: CallbackQuery, state: FSMContext):
    """Начать изменение целевого времени"""
    parts = callback.data.split(":")
    competition_id = int(parts[2])
    distance = float(parts[3])

    # Получаем информацию о соревновании
    competition = await get_competition(competition_id)

    if not competition:
        await callback.answer("❌ Соревнование не найдено", show_alert=True)
        return

    # Получаем регистрацию пользователя для получения distance_name
    user_id = callback.from_user.id
    from competitions.competitions_queries import get_user_competitions
    user_comps = await get_user_competitions(user_id)

    registration = None
    for comp in user_comps:
        if comp['id'] == competition_id and comp.get('distance') == distance:
            registration = comp
            break

    # Сохраняем данные в состоянии
    await state.update_data(
        edit_target_comp_id=competition_id,
        edit_target_distance=distance
    )

    from competitions.competitions_utils import format_competition_distance as format_dist_with_units
    from database.queries import get_user_settings
    from utils.unit_converter import safe_convert_distance_name

    # Используем distance_name если есть, иначе форматируем числовое значение
    distance_name = registration.get('distance_name') if registration else None
    if distance_name:
        settings = await get_user_settings(user_id)
        distance_unit = settings.get('distance_unit', 'км') if settings else 'км'
        dist_str = safe_convert_distance_name(distance_name, distance_unit)
    else:
        dist_str = await format_dist_with_units(distance, user_id)

    text = (
        f"🏃 <b>{competition['name']}</b>\n"
        f"📏 Дистанция: {dist_str}\n\n"
        f"Введите новое целевое время в формате ЧЧ:ММ:СС или ММ:СС:\n\n"
        f"<i>Например:\n"
        f"• 03:30:00 (3 часа 30 минут)\n"
        f"• 45:00 (45 минут)\n"
        f"• 1:30:15 (1 час 30 минут 15 секунд)</i>"
    )

    await callback.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(CompetitionStates.waiting_for_target_time_edit)
    await callback.answer()


@router.message(CompetitionStates.waiting_for_target_time_edit)
async def process_target_time_edit(message: Message, state: FSMContext):
    """Обработать новое целевое время"""
    from utils.time_formatter import validate_time_format

    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "❌ Изменение целевого времени отменено",
            reply_markup=ReplyKeyboardRemove()
        )
        # Возврат в меню соревнований
        await message.answer(
            "🏆 <b>СОРЕВНОВАНИЯ</b>\n\n"
            "Выберите раздел:",
            parse_mode="HTML",
            reply_markup=get_competitions_main_menu()
        )
        return

    time_text = message.text.strip()

    # Валидация формата
    if not validate_time_format(time_text):
        await message.answer(
            "❌ Некорректный формат времени.\n"
            "Используйте формат ЧЧ:ММ:СС или ММ:СС\n\n"
            "Примеры: 03:30:00 или 45:00 или 1:30:15"
        )
        return

    # Нормализуем время
    normalized_time = normalize_time(time_text)

    # Получаем данные из состояния
    data = await state.get_data()
    competition_id = data.get('edit_target_comp_id')
    distance = data.get('edit_target_distance')
    user_id = message.from_user.id

    # Обновляем целевое время
    from competitions.competitions_queries import update_target_time
    success = await update_target_time(user_id, competition_id, distance, normalized_time)

    await state.clear()

    if success:
        await message.answer(
            f"✅ Целевое время обновлено: {normalized_time}",
            reply_markup=ReplyKeyboardRemove()
        )

        # Возвращаемся к карточке соревнования (меню события)
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        from aiogram.types import InlineKeyboardButton

        # Показываем карточку соревнования с обновленными данными
        competition = await get_competition(competition_id)
        participant = await get_user_competition_registration(user_id, competition_id)

        if competition and participant:
            # Объединяем данные соревнования и участника
            comp = {**competition, **participant}
            from competitions.competitions_utils import format_competition_distance as format_dist_with_units, format_competition_date

            distance_str = await format_dist_with_units(distance, user_id)
            date_str = await format_competition_date(comp['date'], user_id)
            time_until = format_time_until_competition(comp['date'])

            text = (
                f"🏆 <b>{comp['name']}</b>\n\n"
                f"📍 {comp.get('city', 'Не указан')}\n"
                f"📅 Дата: {date_str}\n"
                f"⏱ До старта: {time_until}\n"
                f"📏 Дистанция: {distance_str}\n"
            )

            if comp.get('target_time'):
                text += f"🎯 Целевое время: {comp['target_time']}\n"

            text += f"\n✅ Вы зарегистрированы на это соревнование"

            # Создаем клавиатуру для карточки соревнования
            builder = InlineKeyboardBuilder()
            builder.row(
                InlineKeyboardButton(
                    text="🎯 Изменить цель",
                    callback_data=f"comp:edit_target:{competition_id}:{distance}"
                )
            )
            builder.row(
                InlineKeyboardButton(
                    text="❌ Отменить регистрацию",
                    callback_data=f"comp:unregister:{competition_id}"
                )
            )
            builder.row(
                InlineKeyboardButton(text="◀️ Назад к моим соревнованиям", callback_data="comp:my")
            )

            await message.answer(
                text,
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
    else:
        await message.answer(
            "❌ Ошибка при обновлении целевого времени",
            reply_markup=get_main_menu_keyboard()
        )


@router.callback_query(F.data.startswith("comp:cancel_registration:"))
async def cancel_registration(callback: CallbackQuery, state: FSMContext):
    """Отменить регистрацию на соревнование"""
    parts = callback.data.split(":")
    competition_id = int(parts[2])
    distance = float(parts[3])
    user_id = callback.from_user.id

    # Получаем информацию о соревновании
    competition = await get_competition(competition_id)

    if not competition:
        await callback.answer("❌ Соревнование не найдено", show_alert=True)
        return

    # Получаем регистрацию пользователя для получения distance_name
    from competitions.competitions_queries import get_user_competitions
    user_comps = await get_user_competitions(user_id)

    registration = None
    for comp in user_comps:
        if comp['id'] == competition_id and comp.get('distance') == distance:
            registration = comp
            break

    from competitions.competitions_utils import format_competition_distance as format_dist_with_units
    from database.queries import get_user_settings
    from utils.unit_converter import safe_convert_distance_name

    # Используем distance_name если есть, иначе форматируем числовое значение
    distance_name = registration.get('distance_name') if registration else None
    if distance_name:
        settings = await get_user_settings(user_id)
        distance_unit = settings.get('distance_unit', 'км') if settings else 'км'
        dist_str = safe_convert_distance_name(distance_name, distance_unit)
    else:
        dist_str = await format_dist_with_units(distance, user_id)

    # Показываем подтверждение
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Да, отменить",
            callback_data=f"comp:cancel_registration_confirm:{competition_id}:{distance}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Нет, вернуться",
            callback_data=f"comp:my_view:{competition_id}:{distance}"
        )
    )

    text = (
        f"⚠️ <b>ПОДТВЕРЖДЕНИЕ</b>\n\n"
        f"Вы действительно хотите отменить участие в соревновании?\n\n"
        f"🏆 <b>{competition['name']}</b>\n"
        f"📏 Дистанция: {dist_str}\n\n"
        f"<i>Вы сможете зарегистрироваться снова позже.</i>"
    )

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("comp:cancel_registration_confirm:"))
async def confirm_cancel_registration(callback: CallbackQuery, state: FSMContext):
    """Подтвердить отмену регистрации"""
    parts = callback.data.split(":")
    competition_id = int(parts[2])
    distance = float(parts[3])
    user_id = callback.from_user.id

    # Отменяем регистрацию
    from competitions.competitions_queries import unregister_from_competition_with_distance
    success = await unregister_from_competition_with_distance(user_id, competition_id, distance)

    if success:
        await callback.answer("✅ Регистрация отменена", show_alert=True)

        # Возвращаемся к списку соревнований
        from competitions.competitions_handlers import show_my_competitions
        await show_my_competitions(callback, state)
    else:
        await callback.answer("❌ Ошибка при отмене регистрации", show_alert=True)


# ========== МОИ РЕЗУЛЬТАТЫ ==========

@router.callback_query(F.data == "comp:my_results")
async def show_my_results(callback: CallbackQuery, state: FSMContext):
    """Показать меню выбора периода для просмотра результатов"""
    text = (
        "🏅 <b>МОИ РЕЗУЛЬТАТЫ</b>\n\n"
        "Выберите период для просмотра:\n"
    )

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="📅 За месяц", callback_data="comp:my_results:month")
    )
    builder.row(
        InlineKeyboardButton(text="📅 За полгода", callback_data="comp:my_results:6months"),
        InlineKeyboardButton(text="📅 За год", callback_data="comp:my_results:year")
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


@router.callback_query(F.data.startswith("comp:my_results:"))
async def show_my_results_period(callback: CallbackQuery, state: FSMContext):
    """Показать результаты за определенный период"""
    period = callback.data.split(":")[-1]
    await show_my_results_with_period(callback, state, period)


async def show_my_results_with_period(callback: CallbackQuery, state: FSMContext, period: str = "all"):
    """
    Показать завершенные соревнования за выбранный период

    Args:
        period: "all", "year", "6months", "month"
    """
    user_id = callback.from_user.id
    from competitions.competitions_queries import get_user_competitions_by_period
    from utils.time_formatter import calculate_pace
    from datetime import datetime, timedelta

    # Определяем дату начала периода
    date_from = None
    period_name = "Всё время"

    if period == "month":
        # Месяц - с 1-го числа текущего месяца
        now = datetime.now()
        date_from = datetime(now.year, now.month, 1)
        period_name = "За месяц"
    elif period == "6months":
        # 6 месяцев - с 1-го числа 6 месяцев назад
        now = datetime.now()
        month = now.month - 5  # -5 потому что текущий месяц + 5 назад = 6 месяцев
        year = now.year
        if month <= 0:
            month += 12
            year -= 1
        date_from = datetime(year, month, 1)
        period_name = "За полгода"
    elif period == "year":
        # Год - с 1-го числа 12 месяцев назад
        now = datetime.now()
        year = now.year - 1
        date_from = datetime(year, now.month, 1)
        period_name = "За год"

    # Получаем завершенные соревнования с учетом периода
    if period == "all":
        from competitions.competitions_queries import get_user_competitions
        finished_comps = await get_user_competitions(user_id, status_filter='finished')
    else:
        finished_comps = await get_user_competitions_by_period(user_id, date_from)

    if not finished_comps:
        text = (
            "🏅 <b>МОИ РЕЗУЛЬТАТЫ</b>\n\n"
            "У вас пока нет завершенных соревнований.\n\n"
            "Добавьте результаты своих соревнований, чтобы отслеживать прогресс!"
        )
    else:
        text = f"🏅 <b>МОИ РЕЗУЛЬТАТЫ - {period_name}</b>\n\n"

        # Завершенные соревнования
        if finished_comps:
            text += f"🏁 <b>ЗАВЕРШЕННЫЕ СОРЕВНОВАНИЯ</b> ({len(finished_comps)})\n\n"

            # Получаем формат даты пользователя
            from utils.date_formatter import get_user_date_format, DateFormatter
            from competitions.competitions_utils import format_competition_distance as format_dist_with_units
            from database.queries import get_user_settings
            from utils.unit_converter import safe_convert_distance_name

            user_date_format = await get_user_date_format(user_id)
            settings = await get_user_settings(user_id)
            distance_unit = settings.get('distance_unit', 'км') if settings else 'км'

            for i, comp in enumerate(finished_comps, 1):
                # Используем distance_name если есть, иначе форматируем числовое значение
                distance_name = comp.get('distance_name')
                if distance_name:
                    dist_str = safe_convert_distance_name(distance_name, distance_unit)
                else:
                    dist_str = await format_dist_with_units(comp['distance'], user_id)

                # Форматируем дату согласно настройкам пользователя
                formatted_date = DateFormatter.format_date(comp['date'], user_date_format)

                text += f"{i}. <b>{comp['name']}</b>\n"
                text += f"   📏 {dist_str}\n"
                text += f"   📅 {formatted_date}\n"

                if comp.get('finish_time'):
                    normalized_time = normalize_time(comp['finish_time'])
                    result_line = f"   ⏱️ {normalized_time}"

                    # Добавляем темп с учетом единиц измерения
                    from utils.time_formatter import calculate_pace_with_unit
                    pace = await calculate_pace_with_unit(comp['finish_time'], comp['distance'], user_id)
                    if pace:
                        result_line += f" • 🏃 {pace}"

                    # Добавляем места
                    if comp.get('place_overall'):
                        result_line += f"\n   🏆 Общее: {comp['place_overall']}"
                    if comp.get('place_age_category'):
                        result_line += f" • 🏅 Категория: {comp['place_age_category']}"

                    # Добавляем разряд (рассчитываем если не сохранён)
                    qualification = comp.get('qualification')
                    if not qualification and comp.get('distance'):
                        try:
                            from utils.qualifications import get_qualification, time_to_seconds
                            sport_type = comp.get('sport_type', 'бег')
                            from database.queries import get_connection
                            async with get_connection() as db:
                                async with db.execute(
                                    "SELECT gender FROM user_settings WHERE user_id = ?",
                                    (user_id,)
                                ) as cursor:
                                    row = await cursor.fetchone()
                                    gender = row[0] if row and row[0] else 'male'
                            time_sec = time_to_seconds(comp['finish_time'])
                            qualification = get_qualification(sport_type, comp['distance'], time_sec, gender)
                        except Exception:
                            pass

                    if qualification:
                        result_line += f"\n   🎖️ Разряд: {format_qualification(qualification)}"

                    # Добавляем пульс
                    if comp.get('heart_rate'):
                        result_line += f"\n   ❤️ Пульс: {comp['heart_rate']} уд/мин"

                    text += result_line + "\n"

                text += "\n"

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()

    # Кнопка добавления прошедшего соревнования с сохранением периода
    builder.row(
        InlineKeyboardButton(text="➕ Добавить прошедшее соревнование", callback_data=f"comp:add_past:{period}")
    )

    # Если есть результаты, добавляем кнопку удаления
    if finished_comps:
        builder.row(
            InlineKeyboardButton(text="🗑️ Удалить результат", callback_data="comp:delete_result_menu")
        )

    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="comp:my_results")
    )

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


# ========== ЛИЧНЫЕ РЕКОРДЫ ==========

@router.callback_query(F.data == "comp:personal_records")
async def show_personal_records(callback: CallbackQuery, state: FSMContext):
    """Показать личные рекорды пользователя"""
    user_id = callback.from_user.id
    from utils.time_formatter import calculate_pace

    # Получаем личные рекорды
    records = await get_user_personal_records(user_id)

    if not records:
        text = (
            "🏆 <b>ЛИЧНЫЕ РЕКОРДЫ</b>\n\n"
            "У вас пока нет личных рекордов.\n\n"
            "Добавьте результаты своих соревнований, чтобы установить рекорды!"
        )
    else:
        text = "🏆 <b>ЛИЧНЫЕ РЕКОРДЫ</b>\n\n"

        # Получаем формат даты пользователя
        from utils.date_formatter import get_user_date_format, DateFormatter
        from competitions.competitions_utils import format_competition_distance as format_dist_with_units
        user_date_format = await get_user_date_format(user_id)

        # Сортируем по дистанции
        sorted_records = sorted(records.items(), key=lambda x: x[0])

        for distance, record in sorted_records:
            # Форматируем дистанцию с учетом единиц измерения пользователя
            dist_name = await format_dist_with_units(distance, user_id)
            normalized_time = normalize_time(record['best_time'])
            text += f"🏃 <b>{dist_name}</b>\n"
            text += f"⏱️ Время: {normalized_time}\n"

            # Добавляем темп с учетом единиц измерения
            from utils.time_formatter import calculate_pace_with_unit
            pace = await calculate_pace_with_unit(record['best_time'], distance, user_id)
            if pace:
                text += f"⚡ Темп: {pace}\n"

            # Добавляем разряд
            if record.get('qualification'):
                text += f"🎖️ Разряд: {format_qualification(record['qualification'])}\n"

            if record.get('competition_name'):
                comp_name_short = record['competition_name'][:30] + "..." if len(record['competition_name']) > 30 else record['competition_name']
                # Форматируем дату согласно настройкам пользователя
                formatted_date = DateFormatter.format_date(record['date'], user_date_format)
                text += f"📅 Дата: {formatted_date}\n"
                text += f"🏆 Соревнование: {comp_name_short}\n"
            text += "\n"

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="comp:menu")
    )

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


# ========== УДАЛЕНИЕ РЕЗУЛЬТАТА ==========

@router.callback_query(F.data == "comp:delete_result_menu")
async def show_delete_result_menu(callback: CallbackQuery, state: FSMContext):
    """Показать меню для выбора результата для удаления"""
    user_id = callback.from_user.id

    # Получаем завершенные соревнования
    from competitions.competitions_queries import get_user_competitions
    finished_comps = await get_user_competitions(user_id, status_filter='finished')

    if not finished_comps:
        await callback.answer("❌ Нет результатов для удаления", show_alert=True)
        return

    text = (
        "🗑️ <b>УДАЛЕНИЕ РЕЗУЛЬТАТА</b>\n\n"
        "Выберите соревнование для удаления результата:\n\n"
    )

    # Получаем формат даты пользователя
    from utils.date_formatter import get_user_date_format, DateFormatter
    from competitions.competitions_utils import format_competition_distance as format_dist_with_units
    from database.queries import get_user_settings
    from utils.unit_converter import safe_convert_distance_name

    user_date_format = await get_user_date_format(user_id)
    settings = await get_user_settings(user_id)
    distance_unit = settings.get('distance_unit', 'км') if settings else 'км'

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()

    # Кнопки для удаления - показываем название и дату
    for comp in finished_comps[:10]:
        # Используем distance_name если есть, иначе форматируем числовое значение
        distance_name = comp.get('distance_name')
        if distance_name:
            dist_str = safe_convert_distance_name(distance_name, distance_unit)
        else:
            dist_str = await format_dist_with_units(comp['distance'], user_id)
        formatted_date = DateFormatter.format_date(comp['date'], user_date_format)

        # Формируем короткое название для кнопки
        short_name = comp['name'][:20] + "..." if len(comp['name']) > 20 else comp['name']
        button_text = f"{short_name} • {dist_str}"

        builder.row(
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"comp:delete_result:{comp['id']}"
            )
        )

    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="comp:my_results")
    )

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("comp:delete_result:"))
async def confirm_delete_result(callback: CallbackQuery, state: FSMContext):
    """Подтверждение удаления результата"""
    competition_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id

    # Получаем информацию о соревновании
    comp = await get_competition(competition_id)
    if not comp:
        await callback.answer("❌ Соревнование не найдено", show_alert=True)
        return

    # Получаем информацию об участнике
    from competitions.competitions_queries import get_user_competitions
    user_comps = await get_user_competitions(user_id, status_filter='finished')
    user_comp = next((c for c in user_comps if c['id'] == competition_id), None)

    if not user_comp:
        await callback.answer("❌ Результат не найден", show_alert=True)
        return

    from competitions.competitions_utils import format_competition_distance as format_dist_with_units
    dist_text = await format_dist_with_units(user_comp['distance'], user_id)

    text = (
        "⚠️ <b>ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ</b>\n\n"
        f"Вы действительно хотите удалить результат?\n\n"
        f"🏆 <b>{comp['name']}</b>\n"
        f"📅 {comp['date']}\n"
        f"📏 {dist_text}\n"
    )

    if user_comp.get('finish_time'):
        text += f"⏱️ Время: {normalize_time(user_comp['finish_time'])}\n"

    if user_comp.get('qualification'):
        text += f"🎖️ Разряд: {format_qualification(user_comp['qualification'])}\n"

    text += "\n❗️ <i>Результат будет удалён, но регистрация сохранится</i>"

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="🗑️ Удалить результат", callback_data=f"comp:delete_confirmed:{competition_id}")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Отмена", callback_data="comp:delete_result_menu")
    )

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("comp:delete_confirmed:"))
async def delete_result_confirmed(callback: CallbackQuery, state: FSMContext):
    """Удалить результат после подтверждения"""
    competition_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id

    try:
        # Удаляем результат (очищаем поля времени и места)
        from competitions.competitions_queries import delete_competition_result, get_user_competition_registration
        success = await delete_competition_result(user_id, competition_id)

        if success:
            await callback.answer("✅ Результат удалён", show_alert=True)

            # Получаем дистанцию из регистрации для редиректа
            registration = await get_user_competition_registration(user_id, competition_id)
            if registration:
                distance = registration['distance']
                # Имитируем callback для перехода к просмотру соревнования
                from types import SimpleNamespace
                new_callback = SimpleNamespace(
                    message=callback.message,
                    from_user=callback.from_user,
                    data=f"comp:my_view:{competition_id}:{distance}",
                    answer=callback.answer
                )
                await view_my_competition(new_callback, None)
            else:
                # Если регистрация не найдена, возвращаемся к списку
                await show_my_competitions(callback)
        else:
            await callback.answer("❌ Ошибка при удалении", show_alert=True)

    except Exception as e:
        logger.error(f"Error deleting result: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


# ========== ДОБАВЛЕНИЕ РЕЗУЛЬТАТА ==========

@router.callback_query(F.data.startswith("comp:add_result:"))
async def start_add_result(callback: CallbackQuery, state: FSMContext):
    """Начать процесс добавления результата"""
    competition_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id

    # Получаем информацию о соревновании
    comp = await get_competition(competition_id)
    if not comp:
        await callback.answer("❌ Соревнование не найдено", show_alert=True)
        return

    # Сохраняем ID соревнования в состоянии (не очищаем return_period!)
    data = await state.get_data()
    return_period = data.get('return_period', 'all')
    await state.update_data(result_competition_id=competition_id, return_period=return_period)

    # Запрашиваем время
    text = (
        f"🏆 <b>{comp['name']}</b>\n\n"
        "Введите ваше финишное время в формате ЧЧ:ММ:СС или ММ:СС или Ч:М:С\n"
        "Можно указать сотые: ЧЧ:ММ:СС.сс\n\n"
        "Примеры:\n"
        "• 1:23:45.50\n"
        "• 42:30.25\n"
        "• 1:23:45\n"
        "• 2:0:0"
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
        # Получаем сохраненный period для возврата
        data = await state.get_data()
        return_period = data.get('return_period', 'all')

        await state.clear()
        await message.answer(
            "❌ Добавление результата отменено",
            reply_markup=ReplyKeyboardRemove()
        )

        # Возврат к списку прошедших соревнований
        from competitions.competitions_queries import get_user_competitions
        from competitions.competitions_utils import format_competition_date, format_competition_distance
        from aiogram.utils.keyboard import InlineKeyboardBuilder

        user_id = message.from_user.id

        # Получаем завершенные соревнования пользователя
        all_comps = await get_user_competitions(user_id, status_filter='finished')

        # Фильтруем только те, где нет результата
        comps_without_results = [comp for comp in all_comps if not comp.get('finish_time')]

        if comps_without_results:
            # Показываем список соревнований без результатов
            text = (
                "🏁 <b>ДОБАВЛЕНИЕ РЕЗУЛЬТАТА</b>\n\n"
                "У вас есть соревнования без результатов:\n\n"
            )

            builder = InlineKeyboardBuilder()

            # Получаем настройки пользователя
            from database.queries import get_user_settings
            from utils.unit_converter import safe_convert_distance_name
            settings = await get_user_settings(user_id)
            distance_unit = settings.get('distance_unit', 'км') if settings else 'км'

            for i, comp in enumerate(comps_without_results[:10], 1):
                formatted_date = await format_competition_date(comp['date'], user_id)

                # Используем distance_name если есть, иначе форматируем числовое значение
                distance_name = comp.get('distance_name')
                if distance_name:
                    dist_str = safe_convert_distance_name(distance_name, distance_unit)
                else:
                    dist_str = await format_competition_distance(comp['distance'], user_id)

                short_name = comp['name'][:30] + "..." if len(comp['name']) > 30 else comp['name']
                button_text = f"{short_name} • {dist_str}"

                text += f"{i}. <b>{comp['name']}</b>\n   📏 {dist_str} • 📅 {formatted_date}\n\n"

                builder.row(
                    InlineKeyboardButton(
                        text=button_text,
                        callback_data=f"comp:add_result:{comp['id']}"
                    )
                )

            # Кнопка для создания нового соревнования
            builder.row(
                InlineKeyboardButton(text="➕ Добавить новое соревнование", callback_data="comp:add_past_manual")
            )
            builder.row(
                InlineKeyboardButton(text="◀️ Назад", callback_data="comp:my_results")
            )

            await message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())
        else:
            # Если нет соревнований без результатов, показываем сообщение
            builder = InlineKeyboardBuilder()
            builder.row(
                InlineKeyboardButton(text="➕ Добавить новое соревнование", callback_data="comp:add_past_manual")
            )
            builder.row(
                InlineKeyboardButton(text="◀️ К моим результатам", callback_data="comp:my_results")
            )
            await message.answer(
                "У вас нет соревнований без результатов.\n\n"
                "Используйте кнопку ниже для добавления нового соревнования:",
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )

        return

    time_text = message.text.strip()

    # Валидация формата
    if not validate_time_format(time_text):
        await message.answer(
            "❌ Некорректный формат времени.\n"
            "Используйте формат ЧЧ:ММ:СС.сс или ММ:СС.сс или Ч:М:С\n\n"
            "Примеры: 1:23:45.50 или 42:30.25 или 1:23:45 или 2:0:0"
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
        await state.clear()
        await message.answer(
            "❌ Добавление результата отменено",
            reply_markup=ReplyKeyboardRemove()
        )
        # Возврат в меню соревнований
        await message.answer(
            "🏆 <b>СОРЕВНОВАНИЯ</b>\n\n"
            "Выберите раздел:",
            parse_mode="HTML",
            reply_markup=get_competitions_main_menu()
        )
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
        await state.clear()
        await message.answer(
            "❌ Добавление результата отменено",
            reply_markup=ReplyKeyboardRemove()
        )
        # Возврат в меню соревнований
        await message.answer(
            "🏆 <b>СОРЕВНОВАНИЯ</b>\n\n"
            "Выберите раздел:",
            parse_mode="HTML",
            reply_markup=get_competitions_main_menu()
        )
        return

    if message.text == "⏭️ Пропустить":
        await state.update_data(result_place_age=None)
    else:
        try:
            place = int(message.text.strip())
            if place <= 0:
                await message.answer("❌ Место должно быть положительным числом")
                return

            # Проверяем, что место в категории не больше места в общем зачёте
            data = await state.get_data()
            place_overall = data.get('result_place_overall')

            if place_overall is not None and place > place_overall:
                await message.answer(
                    f"❌ Место в возрастной категории ({place}) не может быть больше "
                    f"места в общем зачёте ({place_overall}).\n\n"
                    f"Введите корректное значение или нажмите \"Пропустить\""
                )
                return

            await state.update_data(result_place_age=place)
        except ValueError:
            await message.answer(
                "❌ Некорректное значение. Введите число или нажмите \"Пропустить\""
            )
            return

    # Запрашиваем средний пульс
    await message.answer(
        "Введите ваш средний пульс за соревнование (уд/мин)\n"
        "Или нажмите \"Пропустить\" если не хотите указывать",
        reply_markup=get_result_input_keyboard()
    )
    await state.set_state(CompetitionStates.waiting_for_heart_rate)


@router.message(CompetitionStates.waiting_for_heart_rate)
async def process_heart_rate(message: Message, state: FSMContext):
    """Обработать средний пульс"""

    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "❌ Добавление результата отменено",
            reply_markup=ReplyKeyboardRemove()
        )
        # Возврат в меню соревнований
        await message.answer(
            "🏆 <b>СОРЕВНОВАНИЯ</b>\n\n"
            "Выберите раздел:",
            parse_mode="HTML",
            reply_markup=get_competitions_main_menu()
        )
        return

    if message.text == "⏭️ Пропустить":
        await state.update_data(result_heart_rate=None)
    else:
        try:
            hr = int(message.text.strip())
            if hr <= 0 or hr > 250:
                await message.answer("❌ Пульс должен быть в диапазоне 1-250 уд/мин")
                return
            await state.update_data(result_heart_rate=hr)
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
        place_age_category=data.get('result_place_age'),
        heart_rate=data.get('result_heart_rate')
    )

    # Рассчитываем разряд для отображения
    qualification = None
    if success:
        try:
            from utils.qualifications import get_qualification, time_to_seconds
            comp = await get_competition(competition_id)
            sport_type = comp.get('sport_type', 'бег')

            # Получаем пол пользователя
            from database.queries import get_connection
            async with get_connection() as db:
                async with db.execute(
                    "SELECT gender FROM user_settings WHERE user_id = ?",
                    (user_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    gender = row[0] if row and row[0] else 'male'

            time_seconds = time_to_seconds(data['result_finish_time'])
            qualification = get_qualification(sport_type, distance, time_seconds, gender)
        except Exception as e:
            logger.error(f"Error calculating qualification for display: {e}")

    if success:
        comp = await get_competition(competition_id)

        # Форматируем дистанцию с учетом единиц пользователя
        from competitions.competitions_utils import format_competition_distance as format_dist_with_units
        dist_text = await format_dist_with_units(distance, user_id)

        # Форматируем дату
        from utils.date_formatter import get_user_date_format, DateFormatter
        user_date_format = await get_user_date_format(user_id)
        formatted_date = DateFormatter.format_date(comp['date'], user_date_format)

        # Рассчитываем темп
        from utils.time_formatter import calculate_pace_with_unit
        pace = await calculate_pace_with_unit(data['result_finish_time'], distance, user_id)

        text = (
            "✅ <b>РЕЗУЛЬТАТ ДОБАВЛЕН!</b>\n\n"
            f"🏆 <b>{comp['name']}</b>\n"
            f"📅 Дата: {formatted_date}\n"
            f"📏 Дистанция: {dist_text}\n"
            f"⏱️ Время: {data['result_finish_time']}\n"
        )

        if pace:
            text += f"⚡ Темп: {pace}\n"

        if data.get('result_place_overall'):
            text += f"🏆 Место общее: {data['result_place_overall']}\n"
        if data.get('result_place_age'):
            text += f"🏅 Место в категории: {data['result_place_age']}\n"
        if qualification:
            text += f"🎖️ Разряд: {format_qualification(qualification)}\n"
        if data.get('result_heart_rate'):
            text += f"❤️ Средний пульс: {data['result_heart_rate']} уд/мин\n"

        # Показываем сообщение об успехе
        from aiogram.types import ReplyKeyboardRemove
        await message.answer(text, parse_mode="HTML", reply_markup=ReplyKeyboardRemove())

        # Определяем период на основе даты соревнования
        from datetime import datetime, timedelta
        comp_date = datetime.strptime(comp['date'], '%Y-%m-%d')
        now = datetime.now()

        # Определяем период
        if comp_date >= datetime(now.year, now.month, 1):
            period = "month"  # Текущий месяц
        elif comp_date >= datetime(now.year - 1 if now.month <= 6 else now.year, now.month - 5 if now.month > 6 else now.month + 7, 1):
            period = "6months"  # Последние полгода
        elif comp_date >= datetime(now.year - 1, now.month, 1):
            period = "year"  # Последний год
        else:
            period = "year"  # По умолчанию показываем год

        # Автоматически переходим к результатам с нужным периодом
        temp_msg = await message.answer("⏳ Загрузка результатов...")

        # Создаем объект callback для show_my_results_with_period
        class CallbackProxy:
            def __init__(self, message, user):
                self.message = message
                self.from_user = user
            async def answer(self):
                pass

        proxy_callback = CallbackProxy(temp_msg, message.from_user)
        await show_my_results_with_period(proxy_callback, state, period)
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
