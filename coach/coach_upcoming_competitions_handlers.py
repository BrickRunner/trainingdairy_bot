"""
Handlers для раздела "Предстоящие соревнования" в меню ученика (кабинет тренера)
Путь: Кабинет тренера → Ученики → [Ученик] → Соревнования → Предстоящие соревнования
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime
import asyncio
import os

from competitions.competitions_fsm import CoachUpcomingCompetitionsStates
from competitions.parser import SPORT_CODES, SPORT_NAMES
from competitions.competitions_fetcher import fetch_all_competitions, SERVICE_CODES, SERVICE_NAMES
from database.queries import get_user_settings
from utils.date_formatter import DateFormatter
from coach.coach_training_queries import can_coach_access_student, get_student_display_name
import logging

logger = logging.getLogger(__name__)

router = Router()


# Список городов для быстрого выбора
POPULAR_CITIES = [
    "Москва",
    "Санкт-Петербург",
]


@router.callback_query(F.data.startswith("coach:comp_upcoming_main:"))
async def start_coach_upcoming_competitions(callback: CallbackQuery, state: FSMContext):
    """Начало поиска предстоящих соревнований для ученика"""
    student_id = int(callback.data.split(":")[2])
    coach_id = callback.from_user.id

    # Проверяем доступ
    if not await can_coach_access_student(coach_id, student_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    # Получаем имя ученика
    display_name = await get_student_display_name(coach_id, student_id)

    # Сохраняем student_id в state
    await state.update_data(student_id=student_id, student_display_name=display_name)

    await callback.message.edit_text(
        f"🏃 <b>ПРЕДСТОЯЩИЕ СОРЕВНОВАНИЯ</b>\n\n"
        f"Ученик: <b>{display_name}</b>\n\n"
        f"Выберите город или введите название:",
        parse_mode="HTML"
    )

    # Показываем клавиатуру с популярными городами
    builder = InlineKeyboardBuilder()

    for city in POPULAR_CITIES:
        builder.row(
            InlineKeyboardButton(text=city, callback_data=f"coach_upc:city:{city}")
        )

    builder.row(
        InlineKeyboardButton(text="🌍 Все города", callback_data="coach_upc:city:all")
    )
    builder.row(
        InlineKeyboardButton(text="✏️ Ввести название", callback_data="coach_upc:city:custom")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data=f"coach:competitions_menu:{student_id}")
    )

    await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("coach_upc:city:"))
async def coach_select_city(callback: CallbackQuery, state: FSMContext):
    """Выбор города для тренера"""
    city_data = callback.data.split(":", 2)[2]

    if city_data == "custom":
        # Пользователь хочет ввести свой город
        data = await state.get_data()
        student_display_name = data.get('student_display_name', '')
        student_id = data.get('student_id')

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="❌ Отменить", callback_data=f"coach:comp_upcoming_main:{student_id}")
        )

        await callback.message.edit_text(
            f"🏃 <b>ПРЕДСТОЯЩИЕ СОРЕВНОВАНИЯ</b>\n\n"
            f"Ученик: <b>{student_display_name}</b>\n\n"
            f"✏️ Введите название города:",
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
        await state.set_state(CoachUpcomingCompetitionsStates.waiting_for_city)
        await callback.answer()
        return

    # Сохраняем выбранный город
    if city_data == "all":
        city = None
        city_display = "Все города"
    else:
        city = city_data
        city_display = city_data

    await state.update_data(city=city, city_display=city_display)

    # Переходим к выбору периода
    await show_coach_period_selection(callback.message, state)
    await callback.answer()


@router.message(CoachUpcomingCompetitionsStates.waiting_for_city)
async def process_coach_custom_city(message: Message, state: FSMContext):
    """Обработка введенного города для тренера"""
    city = message.text.strip()

    if not city:
        await message.answer("❌ Пожалуйста, введите корректное название города.")
        return

    await state.update_data(city=city, city_display=city)

    # Переходим к выбору периода
    await show_coach_period_selection(message, state)


async def show_coach_period_selection(message: Message, state: FSMContext):
    """Показать выбор периода для тренера"""
    data = await state.get_data()
    city_display = data.get('city_display', 'Все города')
    student_display_name = data.get('student_display_name', '')
    student_id = data.get('student_id')

    text = (
        f"🏃 <b>ПРЕДСТОЯЩИЕ СОРЕВНОВАНИЯ</b>\n\n"
        f"Ученик: <b>{student_display_name}</b>\n"
        f"📍 Город: <b>{city_display}</b>\n\n"
        f"Выберите период:"
    )

    builder = InlineKeyboardBuilder()

    # Добавляем периоды
    builder.row(
        InlineKeyboardButton(text="📅 1 месяц", callback_data="coach_upc:period:1")
    )
    builder.row(
        InlineKeyboardButton(text="📅 6 месяцев", callback_data="coach_upc:period:6")
    )
    builder.row(
        InlineKeyboardButton(text="📅 1 год", callback_data="coach_upc:period:12")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data=f"coach:comp_upcoming_main:{student_id}")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ К меню ученика", callback_data=f"coach:competitions_menu:{student_id}")
    )

    try:
        await message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    except:
        # Если не получается редактировать (например, после ввода текста)
        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )

    await state.set_state(CoachUpcomingCompetitionsStates.waiting_for_period)


@router.callback_query(F.data == "coach_upc:back:period")
async def coach_back_to_period(callback: CallbackQuery, state: FSMContext):
    """Вернуться к выбору периода для тренера"""
    await show_coach_period_selection(callback.message, state)
    await callback.answer()


@router.callback_query(F.data == "coach_upc:back:sport")
async def coach_back_to_sport(callback: CallbackQuery, state: FSMContext):
    """Вернуться к выбору спорта для тренера"""
    await show_coach_sport_selection(callback.message, state)
    await callback.answer()


@router.callback_query(F.data.startswith("coach_upc:period:"))
async def coach_select_period(callback: CallbackQuery, state: FSMContext):
    """Выбор периода для тренера"""
    period_data = callback.data.split(":", 2)[2]
    period_months = int(period_data)

    # Сохраняем выбранный период
    period_display = {
        1: "1 месяц",
        6: "6 месяцев",
        12: "1 год"
    }.get(period_months, f"{period_months} мес.")

    await state.update_data(period_months=period_months, period_display=period_display)

    # Переходим к выбору вида спорта
    await show_coach_sport_selection(callback.message, state)
    await callback.answer()


async def show_coach_sport_selection(message: Message, state: FSMContext):
    """Показать выбор вида спорта для тренера"""
    data = await state.get_data()
    city_display = data.get('city_display', 'Все города')
    period_display = data.get('period_display', '1 месяц')
    student_display_name = data.get('student_display_name', '')
    student_id = data.get('student_id')

    text = (
        f"🏃 <b>ПРЕДСТОЯЩИЕ СОРЕВНОВАНИЯ</b>\n\n"
        f"Ученик: <b>{student_display_name}</b>\n"
        f"📍 Город: <b>{city_display}</b>\n"
        f"📅 Период: <b>{period_display}</b>\n\n"
        f"Выберите вид спорта:"
    )

    builder = InlineKeyboardBuilder()

    # Добавляем виды спорта (только основные для фильтра)
    allowed_sports = ["Бег", "Плавание", "Велоспорт", "Все виды спорта"]
    for sport_name, sport_code in SPORT_CODES.items():
        if sport_name in allowed_sports:
            builder.row(
                InlineKeyboardButton(
                    text=sport_name,
                    callback_data=f"coach_upc:sport:{sport_code}"
                )
            )

    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="coach_upc:back:period")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ К меню ученика", callback_data=f"coach:competitions_menu:{student_id}")
    )

    try:
        await message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    except:
        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )

    await state.set_state(CoachUpcomingCompetitionsStates.waiting_for_sport)


async def show_coach_service_selection(message: Message, state: FSMContext):
    """Показать выбор сервиса для тренера"""
    data = await state.get_data()
    city_display = data.get('city_display', 'Все города')
    period_display = data.get('period_display', '1 месяц')
    sport_display = data.get('sport_display', 'Все виды спорта')
    student_display_name = data.get('student_display_name', '')
    student_id = data.get('student_id')

    text = (
        f"🏃 <b>ПРЕДСТОЯЩИЕ СОРЕВНОВАНИЯ</b>\n\n"
        f"Ученик: <b>{student_display_name}</b>\n"
        f"📍 Город: <b>{city_display}</b>\n"
        f"📅 Период: <b>{period_display}</b>\n"
        f"🏃 Спорт: <b>{sport_display}</b>\n\n"
        f"Выберите сервис для регистрации:"
    )

    builder = InlineKeyboardBuilder()

    # Добавляем сервисы
    for service_name, service_code in SERVICE_CODES.items():
        builder.row(
            InlineKeyboardButton(
                text=service_name,
                callback_data=f"coach_upc:service:{service_code}"
            )
        )

    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="coach_upc:back:sport")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ К меню ученика", callback_data=f"coach:competitions_menu:{student_id}")
    )

    try:
        await message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    except:
        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )

    await state.set_state(CoachUpcomingCompetitionsStates.waiting_for_service)


@router.callback_query(F.data.startswith("coach_upc:service:"))
async def coach_select_service(callback: CallbackQuery, state: FSMContext):
    """Выбор сервиса для тренера"""
    service_data = callback.data.split(":", 2)[2]

    # Сохраняем выбранный сервис
    if service_data == "all":
        service = None
        service_display = "Все сервисы"
    else:
        service = service_data
        # Находим название сервиса по коду
        service_display = next(
            (name for name, code in SERVICE_CODES.items() if code == service),
            service_data
        )

    await state.update_data(service=service, service_display=service_display)

    # Показываем результаты
    await show_coach_competitions_results(callback.message, state)
    await callback.answer()


@router.callback_query(F.data.startswith("coach_upc:sport:"))
async def coach_select_sport(callback: CallbackQuery, state: FSMContext):
    """Выбор вида спорта для тренера"""
    sport_data = callback.data.split(":", 2)[2]

    # Сохраняем выбранный вид спорта
    if sport_data == "all":
        sport = None
        sport_display = "Все виды спорта"
    else:
        sport = sport_data
        # Находим название спорта по коду
        sport_display = next(
            (name for name, code in SPORT_CODES.items() if code == sport),
            sport_data
        )

    await state.update_data(sport=sport, sport_display=sport_display)

    # Переходим к выбору сервиса
    await show_coach_service_selection(callback.message, state)
    await callback.answer()


async def show_coach_competitions_results(message: Message, state: FSMContext, page: int = 1):
    """Показать результаты поиска соревнований для тренера"""
    data = await state.get_data()
    city = data.get('city')
    city_display = data.get('city_display', 'Все города')
    sport = data.get('sport')
    sport_display = data.get('sport_display', 'Все виды спорта')
    period_months = data.get('period_months', 1)
    period_display = data.get('period_display', '1 месяц')
    service = data.get('service')
    service_display = data.get('service_display', 'Все сервисы')
    student_display_name = data.get('student_display_name', '')
    student_id = data.get('student_id')

    # Получаем настройки тренера для форматирования
    user_id = message.chat.id
    settings = await get_user_settings(user_id)
    date_format = settings.get('date_format', 'ДД.ММ.ГГГГ') if settings else 'ДД.ММ.ГГГГ'

    # Показываем сообщение о загрузке
    loading_text = (
        f"🔍 <b>Поиск соревнований...</b>\n\n"
        f"Ученик: <b>{student_display_name}</b>\n"
        f"📍 Город: <b>{city_display}</b>\n"
        f"📅 Период: <b>{period_display}</b>\n"
        f"🏃 Спорт: <b>{sport_display}</b>\n"
        f"🌐 Сервис: <b>{service_display}</b>"
    )

    try:
        await message.edit_text(loading_text, parse_mode="HTML")
    except:
        msg = await message.answer(loading_text, parse_mode="HTML")
        message = msg

    # Получаем соревнования из API
    try:
        logger.info(f"Coach fetching competitions: city={city}, sport={sport}, period_months={period_months}, service={service}")

        all_competitions = await fetch_all_competitions(
            city=city,
            sport=sport,
            limit=1000,
            period_months=period_months,
            service=service
        )

        logger.info(f"Received {len(all_competitions)} competitions")

        # Фильтруем соревнования: скрываем те, где у ученика заняты все дистанции
        import aiosqlite
        import json
        DB_PATH = os.getenv('DB_PATH', 'database.sqlite')

        filtered_competitions = []
        async with aiosqlite.connect(DB_PATH) as db:
            for comp in all_competitions:
                comp_id_from_api = comp.get('id')
                # Получаем ID соревнования в БД (если оно там есть)
                async with db.execute(
                    "SELECT id FROM competitions WHERE source_url = ?",
                    (comp.get('url', comp_id_from_api),)
                ) as cursor:
                    comp_row = await cursor.fetchone()

                if not comp_row:
                    # Соревнование еще не в БД - показываем его
                    filtered_competitions.append(comp)
                    continue

                comp_db_id = comp_row[0]

                # Получаем дистанции соревнования
                distances_json = comp.get('distances', [])
                if isinstance(distances_json, str):
                    try:
                        distances = json.loads(distances_json)
                    except:
                        distances = distances_json
                else:
                    distances = distances_json

                if not distances:
                    # Нет дистанций - показываем
                    filtered_competitions.append(comp)
                    continue

                # Считаем сколько дистанций занято учеником
                occupied_count = 0
                for dist in distances:
                    if isinstance(dist, dict):
                        distance_km = dist.get('distance', 0)
                        distance_name = dist.get('name', str(distance_km))
                    else:
                        distance_km = float(dist)
                        distance_name = str(dist)

                    # Проверяем есть ли регистрация на эту дистанцию (включая pending)
                    async with db.execute(
                        """
                        SELECT id FROM competition_participants
                        WHERE user_id = ? AND competition_id = ? AND distance = ? AND distance_name = ?
                        """,
                        (student_id, comp_db_id, distance_km, distance_name)
                    ) as cursor:
                        reg_row = await cursor.fetchone()
                        if reg_row:
                            occupied_count += 1

                # Показываем только если есть свободные дистанции
                if occupied_count < len(distances):
                    filtered_competitions.append(comp)
                else:
                    logger.info(f"Skipping competition '{comp.get('title')}' - all distances occupied for student {student_id}")

        all_competitions = filtered_competitions
        logger.info(f"After filtering: {len(all_competitions)} competitions available")

        # Сохраняем все соревнования в state для пагинации
        await state.update_data(all_competitions=all_competitions)

        # Пагинация: 10 соревнований на страницу
        items_per_page = 10
        total_pages = (len(all_competitions) + items_per_page - 1) // items_per_page

        # Проверяем корректность номера страницы
        if page < 1:
            page = 1
        if page > total_pages and total_pages > 0:
            page = total_pages

        # Вычисляем индексы для текущей страницы
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        competitions = all_competitions[start_idx:end_idx]
    except Exception as e:
        logger.error(f"Error fetching competitions: {e}")

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="◀️ К меню ученика", callback_data=f"coach:competitions_menu:{student_id}")
        )

        await message.edit_text(
            "❌ Произошла ошибка при получении данных.\n"
            "Попробуйте позже.",
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
        await state.clear()
        return

    if not all_competitions:
        # Нет соревнований
        text = (
            f"😔 <b>Соревнования не найдены</b>\n\n"
            f"Ученик: <b>{student_display_name}</b>\n"
            f"📍 Город: <b>{city_display}</b>\n"
            f"📅 Период: <b>{period_display}</b>\n"
            f"🏃 Спорт: <b>{sport_display}</b>\n"
            f"🌐 Сервис: <b>{service_display}</b>\n\n"
            f"Попробуйте изменить параметры поиска."
        )

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="◀️ К меню ученика", callback_data=f"coach:competitions_menu:{student_id}")
        )

        await message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
        await state.clear()
        return

    # Показываем результаты
    text = (
        f"🏆 <b>НАЙДЕНО СОРЕВНОВАНИЙ: {len(all_competitions)}</b>\n"
        f"📄 Страница {page} из {total_pages}\n\n"
        f"Ученик: <b>{student_display_name}</b>\n"
        f"📍 Город: <b>{city_display}</b>\n"
        f"📅 Период: <b>{period_display}</b>\n"
        f"🏃 Спорт: <b>{sport_display}</b>\n"
        f"🌐 Сервис: <b>{service_display}</b>\n\n"
    )

    builder = InlineKeyboardBuilder()

    for i, comp in enumerate(competitions, start_idx + 1):
        # Форматируем дату согласно настройкам пользователя
        try:
            date_obj = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
            date_str = DateFormatter.format_date(date_obj, date_format)
        except:
            date_str = ""

        # Формируем название кнопки
        button_text = f"{comp['title'][:40]}"
        if date_str:
            button_text = f"{date_str} | {button_text}"

        # Кнопка для просмотра деталей
        builder.row(
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"coach_compdetail:{comp['id']}"
            )
        )

    # Кнопки пагинации
    pagination_buttons = []
    if page > 1:
        pagination_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"coach_upc:page:{page-1}")
        )
    if page < total_pages:
        pagination_buttons.append(
            InlineKeyboardButton(text="➡️ Вперед", callback_data=f"coach_upc:page:{page+1}")
        )

    if pagination_buttons:
        builder.row(*pagination_buttons)

    # Кнопки навигации
    builder.row(
        InlineKeyboardButton(text="◀️ К меню ученика", callback_data=f"coach:competitions_menu:{student_id}")
    )

    await message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await state.set_state(CoachUpcomingCompetitionsStates.showing_results)


@router.callback_query(F.data.startswith("coach_upc:page:"))
async def coach_navigate_page(callback: CallbackQuery, state: FSMContext):
    """Навигация по страницам для тренера"""
    page_str = callback.data.split(":", 2)[2]
    page = int(page_str)

    await show_coach_competitions_results(callback.message, state, page)
    await callback.answer()


@router.callback_query(F.data.startswith("coach_compdetail:"))
async def show_coach_competition_detail(callback: CallbackQuery, state: FSMContext):
    """Показать детальную информацию о соревновании для тренера"""
    comp_id = callback.data.split(":", 1)[1]

    # Получаем данные о соревновании из state
    data = await state.get_data()
    all_competitions = data.get('all_competitions', [])
    student_display_name = data.get('student_display_name', '')
    student_id = data.get('student_id')

    try:
        # Ищем соревнование в сохраненных данных
        comp = None
        comp_index = None
        for idx, c in enumerate(all_competitions):
            if c['id'] == comp_id:
                comp = c
                comp_index = idx
                break

        if not comp:
            await callback.answer("❌ Соревнование не найдено", show_alert=True)
            return

        # Сохраняем индекс для использования в коротких callback
        await state.update_data(current_comp_index=comp_index)

        # Получаем настройки тренера
        user_id = callback.from_user.id
        settings = await get_user_settings(user_id)
        date_format = settings.get('date_format', 'ДД.ММ.ГГГГ') if settings else 'ДД.ММ.ГГГГ'
        distance_unit = settings.get('distance_unit', 'км') if settings else 'км'

        # Форматируем информацию
        try:
            begin_date = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(comp['end_date'].replace('Z', '+00:00'))
            date_str = DateFormatter.format_date_range(begin_date, end_date, date_format)
        except:
            date_str = "Дата уточняется"

        # Получаем русское название вида спорта
        sport_code = comp.get('sport_code', '')
        sport_name_ru = SPORT_NAMES.get(sport_code, sport_code)

        text = (
            f"🏆 <b>{comp['title']}</b>\n\n"
            f"Ученик: <b>{student_display_name}</b>\n\n"
            f"📅 Дата: {date_str}\n"
            f"📍 Место: {comp['place']}\n"
            f"🏃 Вид спорта: {sport_name_ru}\n"
        )

        # Дистанции - НЕ показываем для HeroLeague
        service = comp.get('service', '')

        if service != 'HeroLeague':
            if comp.get('distances'):
                from utils.unit_converter import safe_convert_distance_name

                text += f"\n<b>📏 Дистанции:</b>\n"
                for dist in comp['distances'][:10]:
                    distance_name = dist.get('name', 'Дистанция')
                    converted_name = safe_convert_distance_name(distance_name, distance_unit)
                    text += f"  • {converted_name}\n"

        if comp.get('url'):
            text += f"\n🔗 <a href=\"{comp['url']}\">Подробнее на сайте</a>"

        # Проверяем, участвует ли ученик в соревновании
        from database.queries import is_user_participant
        is_participant = await is_user_participant(student_id, comp.get('url', comp_id))
        distances = comp.get('distances', [])
        distances_count = len(distances)

        logger.info(f"Coach view - Student {student_id} button logic: is_participant={is_participant}, distances_count={distances_count}")

        builder = InlineKeyboardBuilder()

        # Логика кнопок зависит от количества дистанций (аналогично глобальному разделу)
        if distances_count > 1:
            # Если несколько дистанций - проверяем зарегистрирован ли на все
            from database.queries import is_user_registered_all_distances, get_user_registered_distances
            is_all_registered = await is_user_registered_all_distances(student_id, comp.get('url', comp_id), distances_count)

            # Для отладки: получаем список зарегистрированных дистанций
            registered_indices = await get_user_registered_distances(student_id, comp.get('url', comp_id), distances)
            logger.info(f"Student {student_id} registered on {len(registered_indices)} out of {distances_count} distances")

            if is_all_registered:
                # Зарегистрирован на все дистанции - показываем "Отменить участие"
                logger.info("Showing: ❌ Отменить участие (registered on all)")
                builder.row(
                    InlineKeyboardButton(text="❌ Отменить участие", callback_data=f"coach_comp:cancel:{comp_index}")
                )
            elif is_participant:
                # Зарегистрирован на некоторые дистанции - показываем "Добавить дистанцию"
                logger.info("Showing: ➕ Добавить дистанцию (registered on some)")
                builder.row(
                    InlineKeyboardButton(text="➕ Добавить дистанцию", callback_data=f"coach_comp:participate:{comp_index}")
                )
            else:
                # Не зарегистрирован вообще - показываем "Предложить ученику"
                logger.info("Showing: 📩 Предложить ученику (not registered)")
                builder.row(
                    InlineKeyboardButton(text="📩 Предложить ученику", callback_data=f"coach_comp:participate:{comp_index}")
                )
        else:
            # Одна дистанция или нет дистанций (HeroLeague, reg.place)
            service = comp.get('service', '')
            sport_code = comp.get('sport_code', '')

            if (service == 'HeroLeague' and sport_code != 'camp') or service == 'reg.place':
                # Для спортивных событий HeroLeague и reg.place показываем "Добавить дистанцию"
                if is_participant:
                    logger.info(f"Showing: ➕ Добавить дистанцию ({service}, registered)")
                    builder.row(
                        InlineKeyboardButton(text="➕ Добавить дистанцию", callback_data=f"coach_comp:participate:{comp_index}")
                    )
                else:
                    logger.info(f"Showing: 📩 Предложить ученику ({service}, not registered)")
                    builder.row(
                        InlineKeyboardButton(text="📩 Предложить ученику", callback_data=f"coach_comp:participate:{comp_index}")
                    )
            else:
                # Для Лиги Путешествий и других сервисов - одна регистрация
                if is_participant:
                    logger.info("Showing: ❌ Отменить участие (single registration)")
                    builder.row(
                        InlineKeyboardButton(text="❌ Отменить участие", callback_data=f"coach_comp:cancel:{comp_index}")
                    )
                else:
                    logger.info("Showing: 📩 Предложить ученику (single registration)")
                    builder.row(
                        InlineKeyboardButton(text="📩 Предложить ученику", callback_data=f"coach_comp:participate:{comp_index}")
                    )

        builder.row(
            InlineKeyboardButton(text="◀️ К списку", callback_data="coach_upc:page:1")
        )
        builder.row(
            InlineKeyboardButton(text="◀️ К меню ученика", callback_data=f"coach:competitions_menu:{student_id}")
        )

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=builder.as_markup(),
            disable_web_page_preview=True
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error showing competition detail: {e}")
        await callback.answer("❌ Ошибка при загрузке данных", show_alert=True)


@router.callback_query(F.data.startswith("coach_comp:participate:"))
async def coach_participate_in_competition(callback: CallbackQuery, state: FSMContext):
    """Начать процесс регистрации ученика на соревнование"""
    comp_index_str = callback.data.split(":", 2)[2]
    comp_index = int(comp_index_str)

    try:
        # Получаем данные из state
        data = await state.get_data()
        all_competitions = data.get('all_competitions', [])
        student_id = data.get('student_id')
        student_display_name = data.get('student_display_name', '')

        # Проверяем доступ
        coach_id = callback.from_user.id
        if not await can_coach_access_student(coach_id, student_id):
            await callback.answer("Нет доступа", show_alert=True)
            return

        # Получаем соревнование по индексу
        if comp_index >= len(all_competitions):
            await callback.answer("❌ Соревнование не найдено", show_alert=True)
            return

        comp = all_competitions[comp_index]
        comp_id = comp['id']

        # Сохраняем comp_id и comp_index в state
        await state.update_data(pending_competition_id=comp_id, current_comp_index=comp_index)

        # Проверяем количество дистанций
        distances = comp.get('distances', [])

        if len(distances) > 1:
            # Множественный выбор дистанций
            settings = await get_user_settings(coach_id)
            distance_unit = settings.get('distance_unit', 'км') if settings else 'км'

            # Получаем список уже зарегистрированных дистанций ученика
            from database.queries import get_user_registered_distances
            registered_indices = await get_user_registered_distances(student_id, comp.get('url', comp_id), distances)

            # Инициализируем список выбранных дистанций
            await state.update_data(selected_distances=[], registered_distances=registered_indices)

            builder = InlineKeyboardBuilder()

            from utils.unit_converter import safe_convert_distance_name

            for i, dist in enumerate(distances[:15]):
                distance_name = dist.get('name', 'Дистанция')
                converted_name = safe_convert_distance_name(distance_name, distance_unit)

                # Проверяем, зарегистрирован ли ученик на эту дистанцию
                if i in registered_indices:
                    button_text = f"🔒 {converted_name} (зарегистрирован)"
                    callback_data = f"coach_comp:already_registered:{i}"
                else:
                    button_text = f"☐ {converted_name}"
                    callback_data = f"coach_comp:toggle_dist:{comp_index}:{i}"

                builder.row(InlineKeyboardButton(
                    text=button_text,
                    callback_data=callback_data
                ))

            builder.row(InlineKeyboardButton(
                text="✅ Продолжить",
                callback_data=f"coach_comp:confirm_distances:{comp_index}"
            ))
            builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data=f"coach_compdetail:{comp_id}"))

            await state.set_state(CoachUpcomingCompetitionsStates.selecting_multiple_distances)

            message_text = f"📏 <b>Выберите дистанции для ученика {student_display_name}:</b>\n\n"
            if registered_indices:
                message_text += "🔒 Ученик уже зарегистрирован на некоторые дистанции (отмечены замком).\n"
                message_text += "Выберите дополнительные дистанции для регистрации.\n\n"
            else:
                message_text += "Выберите одну или несколько дистанций.\n"
                message_text += "Нажмите на дистанцию чтобы выбрать/отменить выбор.\n\n"
            message_text += "После выбора нажмите ✅ Продолжить"

            await callback.message.edit_text(
                message_text,
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
            await callback.answer()

        elif len(distances) == 1:
            # Одна дистанция
            distance_km = distances[0].get('distance', 0)
            selected_distance = distance_km if distance_km is not None and distance_km > 0 else None
            await state.update_data(selected_distance=selected_distance, selected_distance_name=distances[0].get('name', ''))

            # Переходим к вводу целевого времени
            await coach_prompt_for_target_time(callback, state, comp_id)

        else:
            # Нет структурированных дистанций (HeroLeague, reg.place)
            service = comp.get('service', '')

            if service in ('HeroLeague', 'reg.place'):
                # Просим ввести дистанцию вручную
                await state.set_state(CoachUpcomingCompetitionsStates.waiting_for_custom_distance)

                settings = await get_user_settings(coach_id)
                distance_unit = settings.get('distance_unit', 'км') if settings else 'км'

                if distance_unit == 'миль':
                    examples = (
                        f"• 3 {distance_unit}\n"
                        f"• 6 {distance_unit}\n"
                        f"• 13.1 {distance_unit}\n"
                        f"• Марафон\n"
                    )
                else:
                    examples = (
                        f"• 5 {distance_unit}\n"
                        f"• 10 {distance_unit}\n"
                        f"• 21.1 {distance_unit}\n"
                        f"• Марафон\n"
                    )

                message_text = (
                    f"📏 <b>Введите дистанцию для ученика {student_display_name}</b>\n\n"
                    f"Укажите дистанцию, на которой планируется участие.\n\n"
                    f"Примеры:\n"
                    f"{examples}"
                )

                builder = InlineKeyboardBuilder()
                builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data=f"coach_compdetail:{comp_id}"))

                await callback.message.edit_text(
                    message_text,
                    parse_mode="HTML",
                    reply_markup=builder.as_markup()
                )
                await callback.answer()
            else:
                # Сохраняем без дистанции
                await state.update_data(selected_distance=None, selected_distance_name=None)
                await coach_prompt_for_target_time(callback, state, comp_id)

    except Exception as e:
        logger.error(f"Error starting coach participation: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("coach_comp:cancel:"))
async def coach_cancel_participation(callback: CallbackQuery, state: FSMContext):
    """Отменить участие ученика в соревновании"""
    from database.queries import remove_competition_participant

    comp_index_str = callback.data.split(":", 2)[2]
    comp_index = int(comp_index_str)

    try:
        data = await state.get_data()
        all_competitions = data.get('all_competitions', [])
        student_id = data.get('student_id')

        # Проверяем доступ
        coach_id = callback.from_user.id
        if not await can_coach_access_student(coach_id, student_id):
            await callback.answer("Нет доступа", show_alert=True)
            return

        # Получаем соревнование по индексу
        if comp_index >= len(all_competitions):
            await callback.answer("❌ Соревнование не найдено", show_alert=True)
            return

        comp = all_competitions[comp_index]
        comp_id = comp['id']

        # Удаляем ученика из участников
        await remove_competition_participant(student_id, comp.get('url', comp_id))

        await callback.answer(
            "✅ Участие ученика отменено",
            show_alert=True
        )

        # Обновляем отображение
        await show_coach_competition_detail(callback, state)

    except Exception as e:
        logger.error(f"Error canceling coach participation: {e}")
        await callback.answer("❌ Ошибка при отмене", show_alert=True)


@router.callback_query(F.data.startswith("coach_comp:already_registered:"))
async def coach_already_registered_distance(callback: CallbackQuery, state: FSMContext):
    """Обработка нажатия на уже зарегистрированную дистанцию"""
    await callback.answer(
        "⚠️ Ученик уже зарегистрирован на эту дистанцию.\n"
        "Для отмены участия используйте кнопку 'Отменить участие'.",
        show_alert=True
    )


@router.callback_query(F.data.startswith("coach_comp:toggle_dist:"))
async def coach_toggle_distance_selection(callback: CallbackQuery, state: FSMContext):
    """Toggle distance selection для тренера"""
    try:
        parts = callback.data.split(":", 3)
        comp_index = int(parts[2])
        distance_idx = int(parts[3])

        data = await state.get_data()
        selected_distances = data.get('selected_distances', [])
        registered_distances = data.get('registered_distances', [])
        all_competitions = data.get('all_competitions', [])
        student_display_name = data.get('student_display_name', '')

        if comp_index >= len(all_competitions):
            await callback.answer("❌ Соревнование не найдено", show_alert=True)
            return

        competition = all_competitions[comp_index]
        comp_id = competition['id']
        distances = competition.get('distances', [])

        if distance_idx in registered_distances:
            await callback.answer(
                "🔒 Ученик уже зарегистрирован на эту дистанцию.",
                show_alert=True
            )
            return

        # Toggle selection
        if distance_idx in selected_distances:
            selected_distances.remove(distance_idx)
        else:
            selected_distances.append(distance_idx)

        await state.update_data(selected_distances=selected_distances)

        # Rebuild keyboard
        coach_id = callback.from_user.id
        settings = await get_user_settings(coach_id)
        distance_unit = settings.get('distance_unit', 'км') if settings else 'км'

        builder = InlineKeyboardBuilder()

        from utils.unit_converter import safe_convert_distance_name

        for i, dist in enumerate(distances[:15]):
            distance_name = dist.get('name', 'Дистанция')
            converted_name = safe_convert_distance_name(distance_name, distance_unit)

            if i in registered_distances:
                button_text = f"🔒 {converted_name} (зарегистрирован)"
                callback_data = f"coach_comp:already_registered:{i}"
            else:
                checkbox = "✓" if i in selected_distances else "☐"
                button_text = f"{checkbox} {converted_name}"
                callback_data = f"coach_comp:toggle_dist:{comp_index}:{i}"

            builder.row(InlineKeyboardButton(
                text=button_text,
                callback_data=callback_data
            ))

        builder.row(InlineKeyboardButton(
            text="✅ Продолжить",
            callback_data=f"coach_comp:confirm_distances:{comp_index}"
        ))
        builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data=f"coach_compdetail:{comp_id}"))

        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
        await callback.answer()

    except Exception as e:
        logger.error(f"Error toggling coach distance: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("coach_comp:confirm_distances:"))
async def coach_confirm_distances_selection(callback: CallbackQuery, state: FSMContext):
    """Подтверждение выбора дистанций для ученика"""
    try:
        comp_index_str = callback.data.split(":", 2)[2]
        comp_index = int(comp_index_str)

        data = await state.get_data()
        selected_distances = data.get('selected_distances', [])

        if not selected_distances:
            await callback.answer("⚠️ Выберите хотя бы одну дистанцию", show_alert=True)
            return

        all_competitions = data.get('all_competitions', [])

        if comp_index >= len(all_competitions):
            await callback.answer("❌ Соревнование не найдено", show_alert=True)
            return

        competition = all_competitions[comp_index]
        comp_id = competition['id']
        distances = competition.get('distances', [])

        # Store distances to process
        distances_to_process = []
        for idx in selected_distances:
            if idx < len(distances):
                dist = distances[idx]
                # Проверяем тип дистанции - может быть dict, число или текст
                if isinstance(dist, dict):
                    distance_km = dist.get('distance', 0)
                    distance_name = dist.get('name', '')
                else:
                    # Если дистанция - число или текст
                    distance_name = str(dist)

                    # Безопасно извлекаем число из текста
                    try:
                        # Если это число - просто конвертируем
                        distance_km = float(dist)
                    except (ValueError, TypeError):
                        # Если это текст типа "10 км", "21.1 км" - извлекаем число
                        import re
                        match = re.search(r'[\d.]+', str(dist))
                        if match:
                            distance_km = float(match.group())
                        else:
                            distance_km = 0
                            logger.warning(f"Could not parse distance from: {dist}")

                logger.info(f"Processing distance idx={idx}: distance_km={distance_km}, name='{distance_name}'")

                distances_to_process.append({
                    'index': idx,
                    'distance_km': distance_km,
                    'name': distance_name
                })

        await state.update_data(
            distances_to_process=distances_to_process,
            current_distance_index=0,
            competition_id=comp_id,
            current_competition=competition
        )

        # Start with first distance
        await coach_prompt_for_distance_time(callback, state, 0)

    except Exception as e:
        logger.error(f"Error confirming coach distances: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


async def coach_prompt_for_distance_time(callback: CallbackQuery, state: FSMContext, index: int):
    """Запросить целевое время для конкретной дистанции (для тренера)"""
    logger.info(f"coach_prompt_for_distance_time called for index {index}")

    data = await state.get_data()
    distances_to_process = data.get('distances_to_process', [])
    comp_id = data.get('competition_id')
    student_display_name = data.get('student_display_name', '')

    if index >= len(distances_to_process):
        await coach_save_all_distances_and_redirect(callback, state)
        return

    distance_info = distances_to_process[index]
    distance_name = distance_info['name']

    coach_id = callback.from_user.id
    settings = await get_user_settings(coach_id)
    distance_unit = settings.get('distance_unit', 'км') if settings else 'км'

    from utils.unit_converter import safe_convert_distance_name
    converted_name = safe_convert_distance_name(distance_name, distance_unit)

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="⏭ Пропустить",
        callback_data=f"coach_comp:skip_dist_time:{index}"
    ))

    if index > 0:
        builder.row(InlineKeyboardButton(
            text="◀️ К предыдущей дистанции",
            callback_data=f"coach_comp:back_dist_time:{index-1}"
        ))
    elif len(distances_to_process) > 1:
        # Используем current_comp_index вместо comp_id для возврата к выбору дистанций
        comp_index_val = data.get('current_comp_index', 0)
        builder.row(InlineKeyboardButton(
            text="◀️ К выбору дистанций",
            callback_data=f"coach_comp:participate:{comp_index_val}"
        ))
    else:
        builder.row(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=f"coach_compdetail:{comp_id}"
        ))

    await state.set_state(CoachUpcomingCompetitionsStates.waiting_for_target_time)

    total = len(distances_to_process)
    progress = f"[{index + 1}/{total}]"

    await callback.message.edit_text(
        f"⏱ <b>Целевое время для ученика {student_display_name} {progress}</b>\n\n"
        f"Дистанция: <b>{converted_name}</b>\n\n"
        f"Введите целевое время в формате:\n"
        f"• ЧЧ:ММ:СС (например, 01:30:00)\n"
        f"• ММ:СС (например, 45:30)\n\n"
        f"Или нажмите ⏭ Пропустить",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


async def coach_prompt_for_target_time(callback: CallbackQuery, state: FSMContext, comp_id: str):
    """Запросить целевое время для одной дистанции (для тренера)"""
    data = await state.get_data()
    student_display_name = data.get('student_display_name', '')

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⏭ Пропустить", callback_data=f"coach_comp:skip_time:{comp_id}"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data=f"coach_compdetail:{comp_id}"))

    await state.set_state(CoachUpcomingCompetitionsStates.waiting_for_target_time)

    await callback.message.edit_text(
        f"⏱ <b>Введите целевое время для ученика {student_display_name}</b>\n\n"
        f"Формат: ЧЧ:ММ:СС (например, 01:30:00) или ММ:СС (например, 45:30)\n\n"
        f"Вы можете пропустить этот шаг, нажав кнопку ниже.",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


async def coach_save_all_distances_and_redirect(callback_or_message, state: FSMContext):
    """Отправить предложения ученику и перенаправить тренера"""
    try:
        logger.info(f"coach_save_all_distances_and_redirect called")

        data = await state.get_data()
        distances_to_process = data.get('distances_to_process', [])
        comp_id = data.get('competition_id')
        competition = data.get('current_competition')
        distance_times = data.get('distance_times', {})
        student_id = data.get('student_id')
        student_display_name = data.get('student_display_name', '')

        if hasattr(callback_or_message, 'message'):
            coach_id = callback_or_message.from_user.id
            message_obj = callback_or_message.message
            bot = callback_or_message.bot
        else:
            coach_id = callback_or_message.from_user.id
            message_obj = callback_or_message
            bot = callback_or_message.bot

        if not competition:
            if hasattr(callback_or_message, 'message'):
                await callback_or_message.answer("❌ Соревнование не найдено", show_alert=True)
            else:
                await callback_or_message.answer("❌ Соревнование не найдено")
            return

        # Получаем информацию о тренере и соревновании
        from database.queries import get_user, DB_PATH
        from utils.date_formatter import DateFormatter, get_user_date_format
        from utils.unit_converter import safe_convert_distance_name
        import aiosqlite

        # Получаем имя тренера
        coach_settings = await get_user_settings(coach_id)
        coach_name = coach_settings.get('name') if coach_settings else None

        if not coach_name:
            coach = await get_user(coach_id)
            coach_name = coach.get('name') or coach.get('username') or 'Ваш тренер'
        comp_name = competition.get('title', 'Соревнование')
        comp_type = SPORT_NAMES.get(competition.get('sport_code', ''), 'Спорт')

        try:
            comp_date = datetime.fromisoformat(competition['begin_date'].replace('Z', '+00:00'))
        except:
            comp_date = datetime.now()

        # Получаем настройки ученика
        student_settings = await get_user_settings(student_id)
        student_distance_unit = student_settings.get('distance_unit', 'км') if student_settings else 'км'
        student_date_format = await get_user_date_format(student_id)
        formatted_date = DateFormatter.format_date(comp_date, student_date_format)

        # Получаем или создаем соревнование в БД для получения числового ID
        from competitions.competitions_queries import get_or_create_competition_from_api

        # Преобразуем данные соревнования в формат для API функции
        # Используем реальный URL из API или comp_id как fallback
        source_url = competition.get('url', comp_id)
        competition_db_id = await get_or_create_competition_from_api({
            'id': comp_id,
            'title': competition.get('title', ''),
            'date': competition.get('begin_date', ''),
            'url': source_url,
            'city': competition.get('city', ''),
            'place': competition.get('place', ''),
            'distances': competition.get('distances', []),
            'sport_code': competition.get('sport_code', 'run'),
            'description': competition.get('description', '')
        })

        logger.info(f"Competition DB ID: {competition_db_id}")

        # Для каждой дистанции создаем предложение и отправляем ОТДЕЛЬНОЕ сообщение
        sent_count = 0
        for dist_info in distances_to_process:
            idx = dist_info['index']
            distance_km = dist_info['distance_km']
            distance_name = dist_info['name']
            target_time = distance_times.get(idx)

            logger.info(f"Creating proposal for student {student_id}: {distance_name} - time: {target_time}")

            # Создаём запись участия с предложением
            async with aiosqlite.connect(DB_PATH) as db:
                # Проверяем, существует ли уже запись с такими параметрами
                async with db.execute(
                    """
                    SELECT id FROM competition_participants
                    WHERE user_id = ? AND competition_id = ? AND distance = ? AND distance_name = ?
                    """,
                    (student_id, competition_db_id, distance_km, distance_name)
                ) as cursor:
                    existing = await cursor.fetchone()

                if existing:
                    # Обновляем существующую запись
                    await db.execute(
                        """
                        UPDATE competition_participants
                        SET target_time = ?, proposal_status = 'pending',
                            proposed_by_coach = 1, proposed_by_coach_id = ?, reminders_enabled = 0
                        WHERE user_id = ? AND competition_id = ? AND distance = ? AND distance_name = ?
                        """,
                        (target_time, coach_id, student_id, competition_db_id, distance_km, distance_name)
                    )
                else:
                    # Вставляем новую запись с предложением
                    await db.execute(
                        """
                        INSERT INTO competition_participants
                        (user_id, competition_id, distance, distance_name, target_time,
                         proposed_by_coach, proposed_by_coach_id, proposal_status, reminders_enabled)
                        VALUES (?, ?, ?, ?, ?, 1, ?, 'pending', 0)
                        """,
                        (student_id, competition_db_id, distance_km, distance_name, target_time, coach_id)
                    )
                    logger.info(f"Inserted new proposal: student={student_id}, comp_id={competition_db_id}, dist={distance_km}, dist_name={distance_name}, target_time={target_time}")
                await db.commit()
                logger.info(f"Proposal committed to database successfully")

            # Форматируем дистанцию с учетом настроек ученика
            formatted_dist = safe_convert_distance_name(distance_name, student_distance_unit)

            # Добавляем единицу измерения явно, если ее нет
            if student_distance_unit == 'мили' and 'миль' not in formatted_dist and 'миля' not in formatted_dist and 'ярд' not in formatted_dist:
                formatted_dist = f"{formatted_dist} (мили)"
            elif student_distance_unit == 'км' and 'км' not in formatted_dist and 'м' not in formatted_dist:
                formatted_dist = f"{formatted_dist} км"

            # Формируем текст уведомления для ЭТОЙ дистанции
            notification_text = (
                f"🏆 <b>ПРЕДЛОЖЕНИЕ ОТ ТРЕНЕРА</b>\n\n"
                f"<b>{coach_name}</b> предлагает вам участие в соревновании:\n\n"
                f"📌 <b>{comp_name}</b>\n"
                f"📅 Дата: {formatted_date}\n"
                f"🏃 Вид: {comp_type}\n"
                f"📏 Дистанция: <b>{formatted_dist}</b>\n"
            )

            if target_time:
                notification_text += f"⏱ Целевое время: <b>{target_time}</b>\n"
            else:
                notification_text += f"⏱ Целевое время: <i>не указано</i>\n"

            notification_text += "\n<b>Что вы решите?</b>"

            # Кнопки для ЭТОЙ дистанции
            builder = InlineKeyboardBuilder()

            # ВАЖНО: Передаем distance_km а не idx, т.к. idx может быть > len(distances)
            builder.row(InlineKeyboardButton(
                text="✅ Принять",
                callback_data=f"accept_coach_dist:{competition_db_id}:{coach_id}:{distance_km}"
            ))
            builder.row(InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=f"reject_coach_dist:{competition_db_id}:{coach_id}:{distance_km}"
            ))

            # Отправляем отдельное сообщение для этой дистанции
            await bot.send_message(
                student_id,
                notification_text,
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
            sent_count += 1

        # Отправляем ученику редирект в главное меню
        from bot.keyboards import get_main_menu_keyboard
        from coach.coach_queries import is_user_coach

        student_is_coach = await is_user_coach(student_id)
        await bot.send_message(
            student_id,
            "Вы в главном меню",
            reply_markup=get_main_menu_keyboard(is_coach=student_is_coach)
        )

        count = len(distances_to_process)

        await state.clear()

        # Подтверждение тренеру + автоматический редирект в меню соревнований ученика
        from coach.coach_competitions_handlers import show_coach_competitions_menu

        # Создаем объект для редиректа
        class RedirectCallback:
            def __init__(self, msg, user, data_str):
                self.message = msg
                self.from_user = user
                self.data = data_str

            async def answer(self, text="", show_alert=False):
                pass

        if hasattr(callback_or_message, 'message'):
            # Редирект через callback - редактируем текущее сообщение
            redirect_callback = RedirectCallback(
                callback_or_message.message,
                callback_or_message.from_user,
                f"coach:competitions_menu:{student_id}"
            )

            # Сначала показываем успех во всплывающем уведомлении
            await callback_or_message.answer(
                f"✅ Отправлено {sent_count} предложений ученику {student_display_name}!",
                show_alert=True
            )

            # Затем редактируем сообщение на меню соревнований ученика
            await show_coach_competitions_menu(redirect_callback, state)
        else:
            # Редирект через message - отправляем новое сообщение
            await message_obj.answer(
                f"✅ Отправлено {sent_count} предложений ученику {student_display_name}!"
            )

            new_msg = await message_obj.answer("📋 Соревнования ученика")
            redirect_callback = RedirectCallback(
                new_msg,
                message_obj.from_user,
                f"coach:competitions_menu:{student_id}"
            )
            await show_coach_competitions_menu(redirect_callback, state)

    except Exception as e:
        logger.error(f"Error sending coach proposals: {e}")
        if hasattr(callback_or_message, 'message'):
            await callback_or_message.answer("❌ Ошибка при отправке предложений", show_alert=True)
        else:
            await callback_or_message.answer("❌ Ошибка при отправке предложений")


@router.callback_query(F.data.startswith("coach_comp:skip_dist_time:"))
async def coach_skip_distance_target_time(callback: CallbackQuery, state: FSMContext):
    """Пропустить целевое время для дистанции"""
    try:
        current_index = int(callback.data.split(":", 2)[2])

        data = await state.get_data()
        distance_times = data.get('distance_times', {})
        distances_to_process = data.get('distances_to_process', [])

        # КРИТИЧЕСКИ ВАЖНО: Используем real_distance_idx, а не current_index!
        # current_index - это позиция в distances_to_process
        # real_distance_idx - это индекс в исходном массиве distances соревнования
        current_distance_info = distances_to_process[current_index]
        real_distance_idx = current_distance_info['index']

        logger.info(f"Skip: current_index={current_index}, real_distance_idx={real_distance_idx}")
        distance_times[real_distance_idx] = None

        next_index = current_index + 1

        # Сохраняем next_index для следующего шага
        await state.update_data(distance_times=distance_times, current_distance_index=next_index)

        if next_index >= len(distances_to_process):
            await coach_save_all_distances_and_redirect(callback, state)
        else:
            await coach_prompt_for_distance_time(callback, state, next_index)

    except Exception as e:
        logger.error(f"Error skipping coach distance time: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("coach_comp:back_dist_time:"))
async def coach_back_to_previous_distance_time(callback: CallbackQuery, state: FSMContext):
    """Вернуться к предыдущей дистанции"""
    try:
        index = int(callback.data.split(":", 2)[2])

        data = await state.get_data()
        distance_times = data.get('distance_times', {})

        if index in distance_times:
            del distance_times[index]
            await state.update_data(distance_times=distance_times, current_distance_index=index)

        await coach_prompt_for_distance_time(callback, state, index)

    except Exception as e:
        logger.error(f"Error going back to previous coach distance: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("coach_comp:skip_time:"))
async def coach_skip_target_time(callback: CallbackQuery, state: FSMContext):
    """Пропустить ввод целевого времени для одной дистанции и отправить предложение"""
    comp_id = callback.data.split(":", 2)[2]

    try:
        data = await state.get_data()
        all_competitions = data.get('all_competitions', [])
        selected_distance = data.get('selected_distance')
        selected_distance_name = data.get('selected_distance_name')
        student_id = data.get('student_id')
        student_display_name = data.get('student_display_name', '')
        coach_id = callback.from_user.id

        comp = next((c for c in all_competitions if c['id'] == comp_id), None)

        if not comp:
            await callback.answer("❌ Соревнование не найдено", show_alert=True)
            return

        # Получаем информацию о тренере и соревновании
        from database.queries import get_user, DB_PATH
        from utils.date_formatter import DateFormatter, get_user_date_format
        from utils.unit_converter import safe_convert_distance_name
        import aiosqlite

        # Получаем имя тренера
        coach_settings = await get_user_settings(coach_id)
        coach_name = coach_settings.get('name') if coach_settings else None

        if not coach_name:
            coach = await get_user(coach_id)
            coach_name = coach.get('name') or coach.get('username') or 'Ваш тренер'
        comp_name = comp.get('title', 'Соревнование')
        comp_type = SPORT_NAMES.get(comp.get('sport_code', ''), 'Спорт')

        try:
            comp_date = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
        except:
            comp_date = datetime.now()

        # Получаем настройки ученика
        student_settings = await get_user_settings(student_id)
        student_distance_unit = student_settings.get('distance_unit', 'км') if student_settings else 'км'
        student_date_format = await get_user_date_format(student_id)
        formatted_date = DateFormatter.format_date(comp_date, student_date_format)

        # Получаем или создаем соревнование в БД для получения числового ID
        from competitions.competitions_queries import get_or_create_competition_from_api

        # Преобразуем данные соревнования в формат для API функции
        # Используем реальный URL из API или comp_id как fallback
        source_url2 = comp.get('url', comp_id)
        competition_db_id = await get_or_create_competition_from_api({
            'id': comp_id,
            'title': comp.get('title', ''),
            'date': comp.get('begin_date', ''),
            'url': source_url2,
            'city': comp.get('city', ''),
            'place': comp.get('place', ''),
            'distances': comp.get('distances', []),
            'sport_code': comp.get('sport_code', 'run'),
            'description': comp.get('description', '')
        })

        logger.info(f"Competition DB ID: {competition_db_id}")

        # Создаём запись участия с предложением (без целевого времени)
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                """
                SELECT id FROM competition_participants
                WHERE user_id = ? AND competition_id = ? AND distance = ? AND distance_name = ?
                """,
                (student_id, competition_db_id, selected_distance, selected_distance_name)
            ) as cursor:
                existing = await cursor.fetchone()

            if existing:
                await db.execute(
                    """
                    UPDATE competition_participants
                    SET target_time = NULL, proposal_status = 'pending',
                        proposed_by_coach = 1, proposed_by_coach_id = ?, reminders_enabled = 0
                    WHERE user_id = ? AND competition_id = ? AND distance = ? AND distance_name = ?
                    """,
                    (coach_id, student_id, competition_db_id, selected_distance, selected_distance_name)
                )
            else:
                await db.execute(
                    """
                    INSERT INTO competition_participants
                    (user_id, competition_id, distance, distance_name, target_time,
                     proposed_by_coach, proposed_by_coach_id, proposal_status, reminders_enabled)
                    VALUES (?, ?, ?, ?, NULL, 1, ?, 'pending', 0)
                    """,
                    (student_id, competition_db_id, selected_distance, selected_distance_name, coach_id)
                )
            await db.commit()

        # Форматируем дистанцию с учетом настроек ученика
        formatted_dist = safe_convert_distance_name(selected_distance_name, student_distance_unit) if selected_distance_name else "Не указана"

        if selected_distance_name:
            if student_distance_unit == 'мили' and 'миль' not in formatted_dist and 'миля' not in formatted_dist and 'ярд' not in formatted_dist:
                formatted_dist = f"{formatted_dist} (мили)"
            elif student_distance_unit == 'км' and 'км' not in formatted_dist and 'м' not in formatted_dist:
                formatted_dist = f"{formatted_dist} км"

        # Формируем текст уведомления
        notification_text = (
            f"🏆 <b>ПРЕДЛОЖЕНИЕ ОТ ТРЕНЕРА</b>\n\n"
            f"<b>{coach_name}</b> предлагает вам участие в соревновании:\n\n"
            f"📌 <b>{comp_name}</b>\n"
            f"📅 Дата: {formatted_date}\n"
            f"🏃 Вид: {comp_type}\n"
            f"📏 Дистанция: <b>{formatted_dist}</b>\n"
            f"⏱ Целевое время: <i>не указано</i>\n"
            f"\n<b>Что вы решите?</b>"
        )

        # Кнопки для ученика (без "Изменить время", т.к. тренер пропустил целевое время)
        builder = InlineKeyboardBuilder()

        builder.row(InlineKeyboardButton(
            text="✅ Принять",
            callback_data=f"accept_coach_dist:{competition_db_id}:{coach_id}:0"
        ))
        builder.row(InlineKeyboardButton(
            text="❌ Отклонить",
            callback_data=f"reject_coach_dist:{competition_db_id}:{coach_id}:0"
        ))

        # Отправляем предложение ученику
        await callback.bot.send_message(
            student_id,
            notification_text,
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )

        # Отправляем ученику редирект в главное меню
        from bot.keyboards import get_main_menu_keyboard
        from coach.coach_queries import is_user_coach

        student_is_coach = await is_user_coach(student_id)
        await callback.bot.send_message(
            student_id,
            "Вы в главном меню",
            reply_markup=get_main_menu_keyboard(is_coach=student_is_coach)
        )

        # Подтверждение тренеру БЕЗ БЛОКИРУЮЩЕГО АЛЕРТА
        await callback.message.edit_text(
            f"✅ Предложение отправлено ученику {student_display_name}!"
        )

        await state.clear()

        # Redirect to student's menu через новое сообщение
        class FakeCallback:
            def __init__(self, msg, user):
                self.message = msg
                self.from_user = user
                self.data = f"coach:competitions_menu:{student_id}"

            async def answer(self, text="", show_alert=False):
                pass

        new_msg = await callback.message.answer("⏳ Загрузка...")
        await asyncio.sleep(0.2)

        from coach.coach_competitions_handlers import show_coach_competitions_menu
        fake_callback = FakeCallback(new_msg, callback.from_user)
        await show_coach_competitions_menu(fake_callback, state)

    except Exception as e:
        logger.error(f"Error sending coach proposal without target time: {e}")
        await callback.answer("❌ Ошибка при отправке предложения", show_alert=True)


@router.message(CoachUpcomingCompetitionsStates.waiting_for_custom_distance)
async def coach_process_custom_distance(message: Message, state: FSMContext):
    """Обработать введенную дистанцию для HeroLeague"""
    if not message.text:
        await message.answer("❌ Пожалуйста, введите дистанцию в текстовом формате")
        return

    distance_name = message.text.strip()
    data = await state.get_data()
    student_display_name = data.get('student_display_name', '')

    logger.info(f"Coach entered custom distance for student: {distance_name}")

    await state.update_data(
        selected_distance_name=distance_name,
        selected_distance=None
    )

    comp_id = data.get('pending_competition_id')

    if not comp_id:
        await message.answer("❌ Ошибка: не найден ID соревнования")
        return

    await state.set_state(CoachUpcomingCompetitionsStates.waiting_for_target_time)

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⏭ Пропустить", callback_data=f"coach_comp:skip_time:{comp_id}"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data=f"coach_compdetail:{comp_id}"))

    await message.answer(
        f"⏱ <b>Введите целевое время для ученика {student_display_name}</b>\n\n"
        f"Формат: ЧЧ:ММ:СС (например, 01:30:00) или ММ:СС (например, 45:30)\n\n"
        f"Вы можете пропустить этот шаг, нажав кнопку ниже.",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


@router.message(CoachUpcomingCompetitionsStates.waiting_for_target_time)
async def coach_process_target_time(message: Message, state: FSMContext):
    """Обработать введенное целевое время для ученика"""
    from database.queries import add_competition_participant
    from utils.time_formatter import validate_time_format, normalize_time

    logger.info(f"coach_process_target_time handler called! message.text={message.text}")

    if not message.text:
        await message.answer("❌ Пожалуйста, введите время в текстовом формате")
        return

    target_time_text = message.text.strip()

    if not validate_time_format(target_time_text):
        await message.answer(
            "❌ Неверный формат времени!\n\n"
            "Используйте формат ЧЧ:ММ:СС или ММ:СС\n\n"
            "Примеры:\n"
            "• 1:30:05 (1 час 30 минут 5 секунд)\n"
            "• 45:30 (45 минут 30 секунд)"
        )
        return

    target_time = normalize_time(target_time_text)

    try:
        data = await state.get_data()
        distances_to_process = data.get('distances_to_process')
        student_id = data.get('student_id')
        student_display_name = data.get('student_display_name', '')

        if distances_to_process:
            # Multi-distance flow
            current_index = data.get('current_distance_index', 0)
            distance_times = data.get('distance_times', {})

            current_distance_info = distances_to_process[current_index]
            real_distance_idx = current_distance_info['index']

            distance_times[real_distance_idx] = target_time

            next_index = current_index + 1

            await state.update_data(
                distance_times=distance_times,
                current_distance_index=next_index
            )

            await message.answer(f"✅ Целевое время {target_time} сохранено!")

            if next_index >= len(distances_to_process):
                await coach_save_all_distances_and_redirect(message, state)
            else:
                distance_info = distances_to_process[next_index]
                distance_name = distance_info['name']

                coach_id = message.from_user.id
                settings = await get_user_settings(coach_id)
                distance_unit = settings.get('distance_unit', 'км') if settings else 'км'

                from utils.unit_converter import safe_convert_distance_name
                converted_name = safe_convert_distance_name(distance_name, distance_unit)

                total = len(distances_to_process)
                progress = f"[{next_index + 1}/{total}]"

                builder = InlineKeyboardBuilder()
                builder.row(InlineKeyboardButton(
                    text="⏭ Пропустить",
                    callback_data=f"coach_comp:skip_dist_time:{next_index}"
                ))

                comp_id_val = data.get('competition_id')
                if next_index > 0:
                    builder.row(InlineKeyboardButton(
                        text="◀️ К предыдущей дистанции",
                        callback_data=f"coach_comp:back_dist_time:{next_index-1}"
                    ))
                elif len(distances_to_process) > 1:
                    # Используем current_comp_index вместо comp_id для возврата к выбору дистанций
                    comp_index_val2 = data.get('current_comp_index', 0)
                    builder.row(InlineKeyboardButton(
                        text="◀️ К выбору дистанций",
                        callback_data=f"coach_comp:participate:{comp_index_val2}"
                    ))
                else:
                    builder.row(InlineKeyboardButton(
                        text="◀️ Назад",
                        callback_data=f"coach_compdetail:{comp_id_val}"
                    ))

                await state.set_state(CoachUpcomingCompetitionsStates.waiting_for_target_time)

                await message.answer(
                    f"⏱ <b>Целевое время для ученика {student_display_name} {progress}</b>\n\n"
                    f"Дистанция: <b>{converted_name}</b>\n\n"
                    f"Введите целевое время в формате:\n"
                    f"• ЧЧ:ММ:СС (например, 01:30:00)\n"
                    f"• ММ:СС (например, 45:30)\n\n"
                    f"Или нажмите ⏭ Пропустить",
                    parse_mode="HTML",
                    reply_markup=builder.as_markup()
                )

        else:
            # Single distance flow - отправляем предложение ученику
            comp_id = data.get('pending_competition_id')
            all_competitions = data.get('all_competitions', [])
            selected_distance = data.get('selected_distance')
            selected_distance_name = data.get('selected_distance_name', '')
            coach_id = message.from_user.id

            if not comp_id:
                await message.answer("❌ Ошибка: соревнование не найдено")
                return

            comp = next((c for c in all_competitions if c['id'] == comp_id), None)

            if not comp:
                await message.answer("❌ Соревнование не найдено")
                return

            # Получаем информацию о тренере и соревновании
            from database.queries import get_user, DB_PATH
            from utils.date_formatter import DateFormatter, get_user_date_format
            from utils.unit_converter import safe_convert_distance_name
            import aiosqlite

            # Получаем имя тренера
            coach_settings = await get_user_settings(coach_id)
            coach_name = coach_settings.get('name') if coach_settings else None

            if not coach_name:
                coach = await get_user(coach_id)
                coach_name = coach.get('name') or coach.get('username') or 'Ваш тренер'

            comp_name = comp.get('title', 'Соревнование')
            comp_type = SPORT_NAMES.get(comp.get('sport_code', ''), 'Спорт')

            try:
                comp_date = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
            except:
                comp_date = datetime.now()

            # Получаем настройки ученика
            student_settings = await get_user_settings(student_id)
            student_distance_unit = student_settings.get('distance_unit', 'км') if student_settings else 'км'
            student_date_format = await get_user_date_format(student_id)
            formatted_date = DateFormatter.format_date(comp_date, student_date_format)

            # Получаем или создаем соревнование в БД для получения числового ID
            from competitions.competitions_queries import get_or_create_competition_from_api

            # Преобразуем данные соревнования в формат для API функции
            # Используем реальный URL из API или comp_id как fallback
            source_url3 = comp.get('url', comp_id)
            competition_db_id = await get_or_create_competition_from_api({
                'id': comp_id,
                'title': comp.get('title', ''),
                'date': comp.get('begin_date', ''),
                'url': source_url3,
                'city': comp.get('city', ''),
                'place': comp.get('place', ''),
                'distances': comp.get('distances', []),
                'sport_code': comp.get('sport_code', 'run'),
                'description': comp.get('description', '')
            })

            logger.info(f"Competition DB ID: {competition_db_id}")

            # Создаём запись участия с предложением
            async with aiosqlite.connect(DB_PATH) as db:
                async with db.execute(
                    """
                    SELECT id FROM competition_participants
                    WHERE user_id = ? AND competition_id = ? AND distance = ? AND distance_name = ?
                    """,
                    (student_id, competition_db_id, selected_distance, selected_distance_name)
                ) as cursor:
                    existing = await cursor.fetchone()

                if existing:
                    await db.execute(
                        """
                        UPDATE competition_participants
                        SET target_time = ?, proposal_status = 'pending',
                            proposed_by_coach = 1, proposed_by_coach_id = ?, reminders_enabled = 0
                        WHERE user_id = ? AND competition_id = ? AND distance = ? AND distance_name = ?
                        """,
                        (target_time, coach_id, student_id, competition_db_id, selected_distance, selected_distance_name)
                    )
                else:
                    await db.execute(
                        """
                        INSERT INTO competition_participants
                        (user_id, competition_id, distance, distance_name, target_time,
                         proposed_by_coach, proposed_by_coach_id, proposal_status, reminders_enabled)
                        VALUES (?, ?, ?, ?, ?, 1, ?, 'pending', 0)
                        """,
                        (student_id, competition_db_id, selected_distance, selected_distance_name, target_time, coach_id)
                    )
                await db.commit()

            # Форматируем дистанцию с учетом настроек ученика
            formatted_dist = safe_convert_distance_name(selected_distance_name, student_distance_unit) if selected_distance_name else "Не указана"

            if selected_distance_name:
                if student_distance_unit == 'мили' and 'миль' not in formatted_dist and 'миля' not in formatted_dist and 'ярд' not in formatted_dist:
                    formatted_dist = f"{formatted_dist} (мили)"
                elif student_distance_unit == 'км' and 'км' not in formatted_dist and 'м' not in formatted_dist:
                    formatted_dist = f"{formatted_dist} км"

            # Формируем текст уведомления
            notification_text = (
                f"🏆 <b>ПРЕДЛОЖЕНИЕ ОТ ТРЕНЕРА</b>\n\n"
                f"<b>{coach_name}</b> предлагает вам участие в соревновании:\n\n"
                f"📌 <b>{comp_name}</b>\n"
                f"📅 Дата: {formatted_date}\n"
                f"🏃 Вид: {comp_type}\n"
                f"📏 Дистанция: <b>{formatted_dist}</b>\n"
                f"⏱ Целевое время: <b>{target_time}</b>\n"
                f"\n<b>Что вы решите?</b>"
            )

            # Кнопки для ученика
            builder = InlineKeyboardBuilder()

            builder.row(InlineKeyboardButton(
                text="✅ Принять",
                callback_data=f"accept_coach_dist:{competition_db_id}:{coach_id}:0"
            ))
            builder.row(InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=f"reject_coach_dist:{competition_db_id}:{coach_id}:0"
            ))

            # Отправляем предложение ученику
            await message.bot.send_message(
                student_id,
                notification_text,
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )

            # Отправляем ученику редирект в главное меню
            from bot.keyboards import get_main_menu_keyboard
            from coach.coach_queries import is_user_coach

            student_is_coach = await is_user_coach(student_id)
            await message.bot.send_message(
                student_id,
                "Вы в главном меню",
                reply_markup=get_main_menu_keyboard(is_coach=student_is_coach)
            )

            await message.answer(f"✅ Предложение отправлено ученику {student_display_name}!")

            await state.clear()

            # Redirect to student's competitions menu
            class FakeCallback:
                def __init__(self, msg):
                    self.message = msg
                    self.from_user = msg.from_user
                    self.data = f"coach:competitions_menu:{student_id}"

                async def answer(self, text="", show_alert=False):
                    pass

            new_msg = await message.answer("⏳ Загрузка...")
            await asyncio.sleep(0.2)

            from coach.coach_competitions_handlers import show_coach_competitions_menu
            fake_callback = FakeCallback(new_msg)
            await show_coach_competitions_menu(fake_callback, state)

    except Exception as e:
        logger.error(f"Error processing coach target time: {e}")
        await message.answer("❌ Ошибка при сохранении целевого времени")
