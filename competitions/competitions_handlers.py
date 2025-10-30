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
            "💡 Соревнования будут автоматически загружены из источников:\n"
            "• Беговое сообщество\n"
            "• Russia Running\n"
            "• Лига героев\n"
            "• Фруктовые забеги\n"
            "• Timerman\n\n"
            "Вы также можете создать своё соревнование вручную."
        )
        await callback.message.edit_text(
            text,
            reply_markup=get_competitions_main_menu(),
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
async def show_my_competitions_menu(callback: CallbackQuery, state: FSMContext):
    """Показать меню моих соревнований"""
    text = (
        "✅ <b>МОИ СОРЕВНОВАНИЯ</b>\n\n"
        "Здесь вы можете посмотреть соревнования, на которые вы зарегистрированы, "
        "и добавить результаты после участия."
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_my_competitions_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "comp:my:upcoming")
async def show_my_upcoming_competitions(callback: CallbackQuery, state: FSMContext):
    """Показать предстоящие соревнования пользователя"""
    user_id = callback.from_user.id

    competitions = await get_user_competitions(user_id, status_filter='upcoming')

    if not competitions:
        text = (
            "📅 <b>Предстоящие соревнования</b>\n\n"
            "У вас пока нет запланированных соревнований.\n\n"
            "Перейдите в раздел 'Предстоящие соревнования' чтобы зарегистрироваться на забег!"
        )
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="📅 Найти соревнования", callback_data="comp:upcoming")
        )
        builder.row(
            InlineKeyboardButton(text="◀️ Назад", callback_data="comp:my")
        )

        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    else:
        text = "📅 <b>Мои предстоящие соревнования</b>\n\n"

        for i, comp in enumerate(competitions[:5], 1):
            time_until = format_time_until_competition(comp['date'])
            dist_str = format_competition_distance(comp['distance'])

            target_time = comp.get('target_time', 'не установлено')

            text += (
                f"{i}. <b>{comp['name']}</b>\n"
                f"   📏 {dist_str}\n"
                f"   📅 {comp['date']} ({time_until})\n"
                f"   🎯 Цель: {target_time}\n\n"
            )

        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        for comp in competitions[:5]:
            builder.row(
                InlineKeyboardButton(
                    text=f"{comp['name'][:40]}...",
                    callback_data=f"comp:my_view:{comp['id']}"
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


@router.callback_query(F.data == "comp:my:finished")
async def show_my_finished_competitions(callback: CallbackQuery, state: FSMContext):
    """Показать завершённые соревнования пользователя"""
    user_id = callback.from_user.id

    competitions = await get_user_competitions(user_id, status_filter='finished')

    if not competitions:
        text = (
            "🏁 <b>Завершённые соревнования</b>\n\n"
            "У вас пока нет завершённых соревнований."
        )
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="◀️ Назад", callback_data="comp:my")
        )

        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    else:
        text = "🏁 <b>Мои завершённые соревнования</b>\n\n"

        for i, comp in enumerate(competitions[:10], 1):
            dist_str = format_competition_distance(comp['distance'])

            # Проверяем есть ли результат
            if comp.get('finish_time'):
                result = f"⏱️ {comp['finish_time']}"
                if comp.get('place_overall'):
                    result += f" | 📊 {comp['place_overall']} место"
            else:
                result = "⚠️ Результат не добавлен"

            text += (
                f"{i}. <b>{comp['name']}</b>\n"
                f"   📏 {dist_str} | 📅 {comp['date']}\n"
                f"   {result}\n\n"
            )

        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        for comp in competitions[:10]:
            builder.row(
                InlineKeyboardButton(
                    text=f"{comp['name'][:40]}...",
                    callback_data=f"comp:my_view_finished:{comp['id']}"
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
    """Показать личные рекорды пользователя"""
    user_id = callback.from_user.id

    records = await get_user_personal_records(user_id)

    if not records:
        text = (
            "🏅 <b>МОИ РЕЗУЛЬТАТЫ</b>\n\n"
            "У вас пока нет личных рекордов.\n\n"
            "Добавьте результаты своих соревнований, чтобы отслеживать прогресс!"
        )
    else:
        text = "🏅 <b>ЛИЧНЫЕ РЕКОРДЫ</b>\n\n"

        # Сортируем по дистанции
        sorted_records = sorted(records.items(), key=lambda x: x[0])

        for distance, record in sorted_records:
            dist_name = format_competition_distance(distance)
            text += f"🏃 <b>{dist_name}</b>\n"
            text += f"   ⏱️ {record['best_time']}\n"
            text += f"   📅 {record['date']}\n"
            if record.get('competition_name'):
                text += f"   🏆 {record['competition_name']}\n"
            text += "\n"

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🏁 Завершённые соревнования", callback_data="comp:my:finished")
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


# ========== ЗАГЛУШКИ ДЛЯ ОСТАЛЬНЫХ ФУНКЦИЙ ==========

@router.callback_query(F.data == "comp:search")
async def search_competitions(callback: CallbackQuery, state: FSMContext):
    """Поиск соревнований (заглушка)"""
    text = (
        "🔍 <b>ПОИСК СОРЕВНОВАНИЙ</b>\n\n"
        "Эта функция находится в разработке.\n"
        "Скоро здесь можно будет искать соревнования по городу, дате и типу."
    )
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="comp:menu")
    )
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


# Импортируем InlineKeyboardButton для использования в коде
from aiogram.types import InlineKeyboardButton
