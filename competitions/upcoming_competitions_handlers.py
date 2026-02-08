"""
Handlers для раздела "Предстоящие соревнования"
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime
import asyncio

from competitions.competitions_fsm import UpcomingCompetitionsStates
from competitions.parser import SPORT_CODES, SPORT_NAMES
from competitions.competitions_fetcher import fetch_all_competitions, SERVICE_CODES, SERVICE_NAMES
from database.queries import get_user_settings, add_competition_participant, is_user_participant, get_user_participant_competition_urls
from utils.date_formatter import DateFormatter
from utils.unit_converter import format_distance
import logging

logger = logging.getLogger(__name__)

router = Router()


POPULAR_CITIES = [
    "Москва",
    "Санкт-Петербург",
]


@router.callback_query(F.data == "comp:upcoming")
async def start_upcoming_competitions(callback: CallbackQuery, state: FSMContext):
    """Начало поиска предстоящих соревнований"""
    await callback.message.edit_text(
        "🏃 <b>ПРЕДСТОЯЩИЕ СОРЕВНОВАНИЯ</b>\n\n"
        "Выберите город или введите название:",
        parse_mode="HTML"
    )

    builder = InlineKeyboardBuilder()

    for city in POPULAR_CITIES:
        builder.row(
            InlineKeyboardButton(text=city, callback_data=f"upc:city:{city}")
        )

    builder.row(
        InlineKeyboardButton(text="🌍 Все города", callback_data="upc:city:all")
    )
    builder.row(
        InlineKeyboardButton(text="✏️ Ввести название", callback_data="upc:city:custom")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="comp:menu")
    )

    await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("upc:city:"))
async def select_city(callback: CallbackQuery, state: FSMContext):
    """Выбор города"""
    city_data = callback.data.split(":", 2)[2]

    if city_data == "custom":
        await callback.message.edit_text(
            "✏️ Введите название города:",
            parse_mode="HTML"
        )
        await state.set_state(UpcomingCompetitionsStates.waiting_for_city)
        await callback.answer()
        return

    if city_data == "all":
        city = None
        city_display = "Все города"
    else:
        city = city_data
        city_display = city_data

    await state.update_data(city=city, city_display=city_display)

    await show_period_selection(callback.message, state)
    await callback.answer()


@router.message(UpcomingCompetitionsStates.waiting_for_city)
async def process_custom_city(message: Message, state: FSMContext):
    """Обработка введенного города"""
    city = message.text.strip()

    if not city:
        await message.answer("❌ Пожалуйста, введите корректное название города.")
        return

    await state.update_data(city=city, city_display=city)

    await show_period_selection(message, state)


async def show_period_selection(message: Message, state: FSMContext):
    """Показать выбор периода"""
    data = await state.get_data()
    city_display = data.get('city_display', 'Все города')

    text = (
        f"🏃 <b>ПРЕДСТОЯЩИЕ СОРЕВНОВАНИЯ</b>\n\n"
        f"📍 Город: <b>{city_display}</b>\n\n"
        f"Выберите период:\n"
    )

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="📅 1 месяц", callback_data="upc:period:1")
    )
    builder.row(
        InlineKeyboardButton(text="📅 6 месяцев", callback_data="upc:period:6")
    )
    builder.row(
        InlineKeyboardButton(text="📅 1 год", callback_data="upc:period:12")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="comp:upcoming")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад в меню", callback_data="comp:menu")
    )

    try:
        await message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    except:
        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )

    await state.set_state(UpcomingCompetitionsStates.waiting_for_period)


@router.callback_query(F.data == "upc:back:period")
async def back_to_period(callback: CallbackQuery, state: FSMContext):
    """Вернуться к выбору периода"""
    await show_period_selection(callback.message, state)
    await callback.answer()


@router.callback_query(F.data == "upc:back:sport")
async def back_to_sport(callback: CallbackQuery, state: FSMContext):
    """Вернуться к выбору спорта"""
    await show_sport_selection(callback.message, state)
    await callback.answer()


@router.callback_query(F.data.startswith("upc:period:"))
async def select_period(callback: CallbackQuery, state: FSMContext):
    """Выбор периода"""
    period_data = callback.data.split(":", 2)[2]
    period_months = int(period_data)

    period_display = {
        1: "1 месяц",
        6: "6 месяцев",
        12: "1 год"
    }.get(period_months, f"{period_months} мес.")

    await state.update_data(period_months=period_months, period_display=period_display)

    await show_sport_selection(callback.message, state)
    await callback.answer()


async def show_sport_selection(message: Message, state: FSMContext):
    """Показать выбор вида спорта"""
    data = await state.get_data()
    city_display = data.get('city_display', 'Все города')
    period_display = data.get('period_display', '1 месяц')

    text = (
        f"🏃 <b>ПРЕДСТОЯЩИЕ СОРЕВНОВАНИЯ</b>\n\n"
        f"📍 Город: <b>{city_display}</b>\n"
        f"📅 Период: <b>{period_display}</b>\n\n"
        f"Выберите вид спорта:"
    )

    builder = InlineKeyboardBuilder()

    allowed_sports = ["Бег", "Плавание", "Велоспорт", "Все виды спорта"]
    for sport_name, sport_code in SPORT_CODES.items():
        if sport_name in allowed_sports:
            builder.row(
                InlineKeyboardButton(
                    text=sport_name,
                    callback_data=f"upc:sport:{sport_code}"
                )
            )

    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="upc:back:period")  
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад в меню", callback_data="comp:menu")
    )

    try:
        await message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    except:
        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )

    await state.set_state(UpcomingCompetitionsStates.waiting_for_sport)


async def show_service_selection(message: Message, state: FSMContext):
    """Показать выбор сервиса для регистрации"""
    data = await state.get_data()
    city_display = data.get('city_display', 'Все города')
    period_display = data.get('period_display', '1 месяц')
    sport_display = data.get('sport_display', 'Все виды спорта')

    text = (
        f"🏃 <b>ПРЕДСТОЯЩИЕ СОРЕВНОВАНИЯ</b>\n\n"
        f"📍 Город: <b>{city_display}</b>\n"
        f"📅 Период: <b>{period_display}</b>\n"
        f"🏃 Спорт: <b>{sport_display}</b>\n\n"
        f"Выберите сервис для регистрации:"
    )

    builder = InlineKeyboardBuilder()

    for service_name, service_code in SERVICE_CODES.items():
        builder.row(
            InlineKeyboardButton(
                text=service_name,
                callback_data=f"upc:service:{service_code}"
            )
        )

    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="upc:back:sport")  
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад в меню", callback_data="comp:menu")
    )

    try:
        await message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    except:
        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )

    await state.set_state(UpcomingCompetitionsStates.waiting_for_service)


@router.callback_query(F.data.startswith("upc:service:"))
async def select_service(callback: CallbackQuery, state: FSMContext):
    """Выбор сервиса и показ результатов"""
    service_data = callback.data.split(":", 2)[2]

    if service_data == "all":
        service = None
        service_display = "Все сервисы"
    else:
        service = service_data
        service_display = next(
            (name for name, code in SERVICE_CODES.items() if code == service),
            service_data
        )

    await state.update_data(service=service, service_display=service_display)

    await show_competitions_results(callback.message, state)
    await callback.answer()


@router.callback_query(F.data.startswith("upc:sport:"))
async def select_sport(callback: CallbackQuery, state: FSMContext):
    """Выбор вида спорта и переход к выбору сервиса"""
    sport_data = callback.data.split(":", 2)[2]

    if sport_data == "all":
        sport = None
        sport_display = "Все виды спорта"
    else:
        sport = sport_data
        sport_display = next(
            (name for name, code in SPORT_CODES.items() if code == sport),
            sport_data
        )

    await state.update_data(sport=sport, sport_display=sport_display)

    await show_service_selection(callback.message, state)
    await callback.answer()


async def show_competitions_results(message: Message, state: FSMContext, page: int = 1):
    """Показать результаты поиска соревнований"""
    data = await state.get_data()
    city = data.get('city')
    city_display = data.get('city_display', 'Все города')
    sport = data.get('sport')
    sport_display = data.get('sport_display', 'Все виды спорта')
    period_months = data.get('period_months', 1)
    period_display = data.get('period_display', '1 месяц')
    service = data.get('service')
    service_display = data.get('service_display', 'Все сервисы')

    user_id = message.chat.id
    settings = await get_user_settings(user_id)
    date_format = settings.get('date_format', 'ДД.ММ.ГГГГ') if settings else 'ДД.ММ.ГГГГ'

    loading_text = (
        f"🔍 <b>Поиск соревнований...</b>\n\n"
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

    try:
        logger.info(f"Fetching competitions: city={city}, sport={sport}, period_months={period_months}, service={service}")

        all_competitions = await fetch_all_competitions(
            city=city,
            sport=sport,
            limit=1000,  
            period_months=period_months,
            service=service
        )

        logger.info(f"Received {len(all_competitions)} competitions after filtering")

        from database.queries import is_user_registered_all_distances, get_user_participant_competition_urls

        participant_urls = await get_user_participant_competition_urls(user_id)
        logger.info(f"User is participant in {len(participant_urls)} competitions")

        filtered_competitions = []
        for comp in all_competitions:
            comp_url = comp.get('url', '')
            distances_count = len(comp.get('distances', []))
            sport_code = comp.get('sport_code', '')

            if not comp_url:
                filtered_competitions.append(comp)
                continue

            if distances_count <= 1:
                if sport_code == "camp":
                    if comp_url not in participant_urls:
                        filtered_competitions.append(comp)
                    else:
                        logger.info(f"Hiding competition (camp, registered): {comp.get('name', 'Unknown')}")
                else:
                    filtered_competitions.append(comp)
            else:
                is_all_registered = await is_user_registered_all_distances(user_id, comp_url, distances_count)
                if not is_all_registered:
                    filtered_competitions.append(comp)
                else:
                    logger.info(f"Hiding competition (all distances registered): {comp.get('name', 'Unknown')}")

        all_competitions = filtered_competitions
        logger.info(f"After filtering participant competitions: {len(all_competitions)} competitions")

        await state.update_data(all_competitions=all_competitions)

        items_per_page = 10
        total_pages = (len(all_competitions) + items_per_page - 1) // items_per_page

        if page < 1:
            page = 1
        if page > total_pages and total_pages > 0:
            page = total_pages

        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        competitions = all_competitions[start_idx:end_idx]
    except Exception as e:
        logger.error(f"Error fetching competitions: {e}")
        await message.edit_text(
            "❌ Произошла ошибка при получении данных.\n"
            "Попробуйте позже.",
            parse_mode="HTML"
        )
        await state.clear()
        return

    if not all_competitions:
        text = (
            f"😔 <b>Соревнования не найдены</b>\n\n"
            f"📍 Город: <b>{city_display}</b>\n"
            f"📅 Период: <b>{period_display}</b>\n"
            f"🏃 Спорт: <b>{sport_display}</b>\n"
            f"🌐 Сервис: <b>{service_display}</b>\n\n"
            f"Попробуйте изменить параметры поиска."
        )

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="◀️ Назад в меню", callback_data="comp:menu")
        )

        await message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
        await state.clear()
        return

    text = (
        f"🏆 <b>НАЙДЕНО СОРЕВНОВАНИЙ: {len(all_competitions)}</b>\n"
        f"📄 Страница {page} из {total_pages}\n\n"
        f"📍 Город: <b>{city_display}</b>\n"
        f"📅 Период: <b>{period_display}</b>\n"
        f"🏃 Спорт: <b>{sport_display}</b>\n"
        f"🌐 Сервис: <b>{service_display}</b>\n\n"
    )

    builder = InlineKeyboardBuilder()

    for i, comp in enumerate(competitions, start_idx + 1):
        try:
            date_obj = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
            date_str = DateFormatter.format_date(date_obj, date_format)
        except:
            date_str = ""

        button_text = f"{comp['title'][:40]}"
        if date_str:
            button_text = f"{date_str} | {button_text}"

        builder.row(
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"compdetail:{comp['id']}"
            )
        )

    pagination_buttons = []
    if page > 1:
        pagination_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"upc:page:{page-1}")
        )
    if page < total_pages:
        pagination_buttons.append(
            InlineKeyboardButton(text="➡️ Вперед", callback_data=f"upc:page:{page+1}")
        )

    if pagination_buttons:
        builder.row(*pagination_buttons)

    builder.row(
        InlineKeyboardButton(text="◀️ Назад в меню", callback_data="comp:menu")
    )

    await message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await state.set_state(UpcomingCompetitionsStates.showing_results)


@router.callback_query(F.data.startswith("upc:page:"))
async def navigate_page(callback: CallbackQuery, state: FSMContext):
    """Навигация по страницам результатов"""
    page_str = callback.data.split(":", 2)[2]
    page = int(page_str)

    await show_competitions_results(callback.message, state, page)
    await callback.answer()


@router.callback_query(F.data.startswith("compdetail:"))
async def show_competition_detail(callback: CallbackQuery, state: FSMContext):
    """Показать детальную информацию о соревновании"""
    comp_id = callback.data.split(":", 1)[1]

    data = await state.get_data()
    all_competitions = data.get('all_competitions', [])

    try:
        comp = next((c for c in all_competitions if c['id'] == comp_id), None)

        if not comp:
            await callback.answer("❌ Соревнование не найдено", show_alert=True)
            return

        user_id = callback.from_user.id
        settings = await get_user_settings(user_id)
        date_format = settings.get('date_format', 'ДД.ММ.ГГГГ') if settings else 'ДД.ММ.ГГГГ'
        distance_unit = settings.get('distance_unit', 'км') if settings else 'км'

        try:
            begin_date = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(comp['end_date'].replace('Z', '+00:00'))
            date_str = DateFormatter.format_date_range(begin_date, end_date, date_format)
        except:
            date_str = "Дата уточняется"

        sport_code = comp.get('sport_code', '')
        sport_name_ru = SPORT_NAMES.get(sport_code, sport_code)

        text = (
            f"🏆 <b>{comp['title']}</b>\n\n"
            f"📅 Дата: {date_str}\n"
            f"📍 Место: {comp['place']}\n"
            f"🏃 Вид спорта: {sport_name_ru}\n"
        )

        service = comp.get('service', '')
        logger.info(f"Competition detail: service={service}, has distances={bool(comp.get('distances'))}, count={len(comp.get('distances', []))}")

        if service != 'HeroLeague':
            if comp.get('distances'):
                from utils.unit_converter import safe_convert_distance_name

                text += f"\n<b>📏 Дистанции:</b>\n"
                logger.info(f"Showing {len(comp['distances'])} distances for {service}")
                for dist in comp['distances'][:10]:
                    distance_km = dist.get('distance', 0)
                    distance_name = dist.get('name', 'Дистанция')

                    converted_name = safe_convert_distance_name(distance_name, distance_unit)

                    text += f"  • {converted_name}\n"
                    logger.debug(f"  Distance: {converted_name}")
            else:
                logger.warning(f"No distances found for {service} competition: {comp.get('title')}")

        if comp.get('url'):
            text += f"\n🔗 <a href=\"{comp['url']}\">Подробнее на сайте</a>"

        is_participant = await is_user_participant(user_id, comp.get('url', comp_id))
        distances = comp.get('distances', [])
        distances_count = len(distances)

        logger.info(f"Button logic: is_participant={is_participant}, distances_count={distances_count}")

        builder = InlineKeyboardBuilder()

        if distances_count > 1:
            from database.queries import is_user_registered_all_distances, get_user_registered_distances
            is_all_registered = await is_user_registered_all_distances(user_id, comp.get('url', comp_id), distances_count)

            registered_indices = await get_user_registered_distances(user_id, comp.get('url', comp_id), distances)
            logger.info(f"Registered on {len(registered_indices)} out of {distances_count} distances")
            logger.info(f"is_all_registered={is_all_registered}, is_participant={is_participant}")

            if is_all_registered:
                logger.info("Showing: ❌ Отменить участие (registered on all)")
                builder.row(
                    InlineKeyboardButton(text="❌ Отменить участие", callback_data=f"comp:cancel:{comp_id}")
                )
            elif is_participant:
                logger.info("Showing: ➕ Добавить дистанцию (registered on some)")
                builder.row(
                    InlineKeyboardButton(text="➕ Добавить дистанцию", callback_data=f"comp:participate:{comp_id}")
                )
            else:
                logger.info("Showing: ✅ Я участвую (not registered)")
                builder.row(
                    InlineKeyboardButton(text="✅ Я участвую", callback_data=f"comp:participate:{comp_id}")
                )
        else:
            service = comp.get('service', '')
            sport_code = comp.get('sport_code', '')

            if (service == 'HeroLeague' and sport_code != 'camp') or service == 'reg.place':
                if is_participant:
                    logger.info(f"Showing: ➕ Добавить дистанцию ({service}, registered)")
                    builder.row(
                        InlineKeyboardButton(text="➕ Добавить дистанцию", callback_data=f"comp:participate:{comp_id}")
                    )
                else:
                    logger.info(f"Showing: ✅ Я участвую ({service}, not registered)")
                    builder.row(
                        InlineKeyboardButton(text="✅ Я участвую", callback_data=f"comp:participate:{comp_id}")
                    )
            else:
                if is_participant:
                    logger.info("Showing: ❌ Отменить участие (single registration)")
                    builder.row(
                        InlineKeyboardButton(text="❌ Отменить участие", callback_data=f"comp:cancel:{comp_id}")
                    )
                else:
                    logger.info("Showing: ✅ Я участвую (single registration)")
                    builder.row(
                        InlineKeyboardButton(text="✅ Я участвую", callback_data=f"comp:participate:{comp_id}")
                    )

        builder.row(
            InlineKeyboardButton(text="◀️ К списку", callback_data="upc:page:1")
        )
        builder.row(
            InlineKeyboardButton(text="◀️ Назад в меню", callback_data="comp:menu")
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


@router.callback_query(F.data.startswith("comp:participate:"))
async def participate_in_competition(callback: CallbackQuery, state: FSMContext):
    """Начать процесс участия в соревновании"""
    comp_id = callback.data.split(":", 2)[2]

    try:
        data = await state.get_data()
        all_competitions = data.get('all_competitions', [])

        comp = next((c for c in all_competitions if c['id'] == comp_id), None)

        if not comp:
            await callback.answer("❌ Соревнование не найдено", show_alert=True)
            return

        await state.update_data(pending_competition_id=comp_id)

        distances = comp.get('distances', [])

        if len(distances) > 1:
            user_id = callback.from_user.id
            settings = await get_user_settings(user_id)
            distance_unit = settings.get('distance_unit', 'км') if settings else 'км'

            from database.queries import get_user_registered_distances
            registered_indices = await get_user_registered_distances(user_id, comp.get('url', comp_id), distances)

            await state.update_data(selected_distances=[], registered_distances=registered_indices)

            builder = InlineKeyboardBuilder()

            from utils.unit_converter import safe_convert_distance_name

            for i, dist in enumerate(distances[:15]):
                distance_km = dist.get('distance', 0)
                distance_name = dist.get('name', 'Дистанция')

                converted_name = safe_convert_distance_name(distance_name, distance_unit)

                if i in registered_indices:
                    button_text = f"🔒 {converted_name} (зарегистрирован)"
                    callback_data = f"comp:already_registered:{i}"
                else:
                    button_text = f"☐ {converted_name}"
                    callback_data = f"comp:toggle_dist:{comp_id}:{i}"

                builder.row(InlineKeyboardButton(
                    text=button_text,
                    callback_data=callback_data
                ))

            builder.row(InlineKeyboardButton(
                text="✅ Продолжить",
                callback_data=f"comp:confirm_distances:{comp_id}"
            ))
            builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data=f"compdetail:{comp_id}"))

            await state.set_state(UpcomingCompetitionsStates.selecting_multiple_distances)

            message_text = "📏 <b>Выберите дистанции:</b>\n\n"
            if registered_indices:
                message_text += "🔒 Вы уже зарегистрированы на некоторые дистанции (отмечены замком).\n"
                message_text += "Выберите дополнительные дистанции для регистрации.\n\n"
            else:
                message_text += "Выберите одну или несколько дистанций, на которых вы планируете участвовать.\n"
                message_text += "Нажмите на дистанцию чтобы выбрать/отменить выбор.\n\n"
            message_text += "После выбора нажмите ✅ Продолжить"

            await callback.message.edit_text(
                message_text,
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
            await callback.answer()

        elif len(distances) == 1:
            distance_km = distances[0].get('distance', 0)
            selected_distance = distance_km if distance_km is not None and distance_km > 0 else None
            await state.update_data(selected_distance=selected_distance, selected_distance_name=distances[0].get('name', ''))

            await prompt_for_target_time(callback, state, comp_id)

        else:
            service = comp.get('service', '')

            if service in ('HeroLeague', 'reg.place'):
                await state.set_state(UpcomingCompetitionsStates.waiting_for_custom_distance)

                user_id = callback.from_user.id
                settings = await get_user_settings(user_id)
                distance_unit = settings.get('distance_unit', 'км') if settings else 'км'

                if distance_unit == 'миль':
                    examples = (
                        f"• 3 {distance_unit}\n"
                        f"• 6 {distance_unit}\n"
                        f"• 13.1 {distance_unit}\n"
                        f"• Марафон\n"
                        f"• 2 {distance_unit} (лыжная гонка)\n"
                    )
                else:  
                    examples = (
                        f"• 5 {distance_unit}\n"
                        f"• 10 {distance_unit}\n"
                        f"• 21.1 {distance_unit}\n"
                        f"• Марафон\n"
                        f"• 3 {distance_unit} (лыжная гонка)\n"
                    )

                message_text = (
                    f"📏 <b>Введите дистанцию</b>\n\n"
                    f"Укажите дистанцию, на которой вы планируете участвовать.\n\n"
                    f"Примеры:\n"
                    f"{examples}"
                )

                builder = InlineKeyboardBuilder()
                builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data=f"compdetail:{comp_id}"))

                await callback.message.edit_text(
                    message_text,
                    parse_mode="HTML",
                    reply_markup=builder.as_markup()
                )
                await callback.answer()
            else:
                await state.update_data(selected_distance=None, selected_distance_name=None)
                await prompt_for_target_time(callback, state, comp_id)

    except Exception as e:
        logger.error(f"Error starting participation: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("comp:already_registered:"))
async def already_registered_distance(callback: CallbackQuery, state: FSMContext):
    """Обработка нажатия на уже зарегистрированную дистанцию"""
    await callback.answer(
        "⚠️ Вы уже зарегистрированы на эту дистанцию.\n"
        "Для отмены участия используйте кнопку 'Отменить участие' на странице соревнования.",
        show_alert=True
    )


@router.callback_query(F.data.startswith("comp:toggle_dist:"))
async def toggle_distance_selection(callback: CallbackQuery, state: FSMContext):
    """Toggle distance selection (checkbox)"""
    try:
        parts = callback.data.split(":", 3)
        comp_id = parts[2]
        distance_idx = int(parts[3])

        data = await state.get_data()
        selected_distances = data.get('selected_distances', [])
        registered_distances = data.get('registered_distances', [])
        all_competitions = data.get('all_competitions', [])

        competition = None
        for comp in all_competitions:
            if comp.get('id') == comp_id:
                competition = comp
                break

        if not competition:
            await callback.answer("❌ Соревнование не найдено", show_alert=True)
            return

        distances = competition.get('distances', [])

        if distance_idx in registered_distances:
            await callback.answer(
                "🔒 Вы уже зарегистрированы на эту дистанцию. "
                "Её нельзя удалить или добавить повторно.",
                show_alert=True
            )
            return

        if distance_idx in selected_distances:
            selected_distances.remove(distance_idx)
        else:
            selected_distances.append(distance_idx)

        await state.update_data(selected_distances=selected_distances)

        user_id = callback.from_user.id
        settings = await get_user_settings(user_id)
        distance_unit = settings.get('distance_unit', 'км') if settings else 'км'

        builder = InlineKeyboardBuilder()

        from utils.unit_converter import safe_convert_distance_name

        for i, dist in enumerate(distances[:15]):
            distance_km = dist.get('distance', 0)
            distance_name = dist.get('name', 'Дистанция')
            converted_name = safe_convert_distance_name(distance_name, distance_unit)

            if i in registered_distances:
                button_text = f"🔒 {converted_name} (зарегистрирован)"
                callback_data = f"comp:already_registered:{i}"
            else:
                checkbox = "✓" if i in selected_distances else "☐"
                button_text = f"{checkbox} {converted_name}"
                callback_data = f"comp:toggle_dist:{comp_id}:{i}"

            builder.row(InlineKeyboardButton(
                text=button_text,
                callback_data=callback_data
            ))

        builder.row(InlineKeyboardButton(
            text="✅ Продолжить",
            callback_data=f"comp:confirm_distances:{comp_id}"
        ))
        builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data=f"comp:detail:{comp_id}"))

        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
        await callback.answer()

    except Exception as e:
        logger.error(f"Error toggling distance: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("comp:confirm_distances:"))
async def confirm_distances_selection(callback: CallbackQuery, state: FSMContext):
    """Confirm distance selection and start sequential time input"""
    try:
        comp_id = callback.data.split(":", 2)[2]

        data = await state.get_data()
        selected_distances = data.get('selected_distances', [])

        if not selected_distances:
            await callback.answer("⚠️ Выберите хотя бы одну дистанцию", show_alert=True)
            return

        all_competitions = data.get('all_competitions', [])

        competition = None
        for comp in all_competitions:
            if comp.get('id') == comp_id:
                competition = comp
                break

        if not competition:
            await callback.answer("❌ Соревнование не найдено", show_alert=True)
            return

        distances = competition.get('distances', [])

        distances_to_process = []
        for idx in selected_distances:
            if idx < len(distances):
                distances_to_process.append({
                    'index': idx,
                    'distance_km': distances[idx].get('distance', 0),
                    'name': distances[idx].get('name', '')
                })

        await state.update_data(
            distances_to_process=distances_to_process,
            current_distance_index=0,
            competition_id=comp_id,
            current_competition=competition  
        )

        await prompt_for_distance_time(callback, state, 0)

    except Exception as e:
        logger.error(f"Error confirming distances: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


async def prompt_for_distance_time(callback: CallbackQuery, state: FSMContext, index: int):
    """Prompt for target time for specific distance"""
    logger.info(f"prompt_for_distance_time called for index {index}")

    data = await state.get_data()
    distances_to_process = data.get('distances_to_process', [])
    comp_id = data.get('competition_id')

    logger.info(f"Found {len(distances_to_process)} distances to process")

    if index >= len(distances_to_process):
        logger.info("Index >= length, calling save_all_distances_and_redirect")
        await save_all_distances_and_redirect(callback, state)
        return

    distance_info = distances_to_process[index]
    distance_name = distance_info['name']
    distance_km = distance_info['distance_km']

    logger.info(f"Prompting for distance: {distance_name} ({distance_km}km)")

    user_id = callback.from_user.id
    settings = await get_user_settings(user_id)
    distance_unit = settings.get('distance_unit', 'км') if settings else 'км'

    from utils.unit_converter import safe_convert_distance_name
    converted_name = safe_convert_distance_name(distance_name, distance_unit)

    display_name = converted_name

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="⏭ Пропустить",
        callback_data=f"comp:skip_dist_time:{index}"
    ))

    if index > 0:
        builder.row(InlineKeyboardButton(
            text="◀️ К предыдущей дистанции",
            callback_data=f"comp:back_dist_time:{index-1}"
        ))
    elif len(distances_to_process) > 1:
        builder.row(InlineKeyboardButton(
            text="◀️ К выбору дистанций",
            callback_data=f"comp:participate:{comp_id}"
        ))
    else:
        builder.row(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=f"compdetail:{comp_id}"
        ))

    logger.info(f"Setting FSM state to waiting_for_target_time")
    await state.set_state(UpcomingCompetitionsStates.waiting_for_target_time)

    current_state = await state.get_state()
    logger.info(f"Current FSM state after setting: {current_state}")

    total = len(distances_to_process)
    progress = f"[{index + 1}/{total}]"

    await callback.message.edit_text(
        f"⏱ <b>Целевое время {progress}</b>\n\n"
        f"Дистанция: <b>{display_name}</b>\n\n"
        f"Введите целевое время в формате:\n"
        f"• ЧЧ:ММ:СС (например, 01:30:00)\n"
        f"• ММ:СС (например, 45:30)\n\n"
        f"Или нажмите ⏭ Пропустить",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


async def save_all_distances_and_redirect(callback_or_message, state: FSMContext):
    """Save all distances with their times to database and redirect"""
    try:
        logger.info(f"save_all_distances_and_redirect called with type: {type(callback_or_message)}")

        data = await state.get_data()
        logger.info(f"State data keys: {list(data.keys())}")

        distances_to_process = data.get('distances_to_process', [])
        comp_id = data.get('competition_id')
        competition = data.get('current_competition')  
        distance_times = data.get('distance_times', {})

        logger.info(f"Processing {len(distances_to_process)} distances")
        logger.info(f"comp_id: {comp_id}, competition exists: {competition is not None}")
        logger.info(f"distance_times: {distance_times}")

        if hasattr(callback_or_message, 'message'):
            logger.info("Detected as CallbackQuery")
            user_id = callback_or_message.from_user.id
            message_obj = callback_or_message.message
        else:
            logger.info("Detected as Message")
            user_id = callback_or_message.from_user.id
            message_obj = callback_or_message

        if not competition:
            if hasattr(callback_or_message, 'message'):
                await callback_or_message.answer("❌ Соревнование не найдено", show_alert=True)
            else:
                await callback_or_message.answer("❌ Соревнование не найдено")
            return

        logger.info(f"Saving {len(distances_to_process)} distances to database...")
        for dist_info in distances_to_process:
            idx = dist_info['index']
            distance_km = dist_info['distance_km']
            distance_name = dist_info['name']
            target_time = distance_times.get(idx)

            logger.info(f"Saving distance {idx}: {distance_name} ({distance_km}km) - time: {target_time}")

            await add_competition_participant(
                user_id=user_id,
                competition_id=comp_id,
                comp_data=competition,
                target_time=target_time,
                distance=distance_km,
                distance_name=distance_name
            )

        logger.info("All distances saved successfully")

        from competitions.competitions_queries import get_user_competitions
        saved_comps = await get_user_competitions(user_id, status_filter='upcoming')
        logger.info(f"VERIFICATION: User {user_id} now has {len(saved_comps)} upcoming competitions")
        for comp in saved_comps:
            logger.info(f"  - {comp.get('name')} on {comp.get('date')}")

        count = len(distances_to_process)
        logger.info(f"Showing success message for {count} distances")

        await state.clear()

        logger.info("Redirecting to My Competitions...")
        from competitions.competitions_handlers import show_my_competitions

        if hasattr(callback_or_message, 'message'):
            logger.info("Redirecting via CallbackQuery")
            await callback_or_message.answer(
                f"✅ Зарегистрированы на {count} дистанций!",
                show_alert=True
            )
            await show_my_competitions(callback_or_message, state)
        else:
            logger.info("Redirecting via Message - sending new message")

            await message_obj.answer(f"✅ Зарегистрированы на {count} дистанций!")

            class FakeCallback:
                def __init__(self, msg, user):
                    self.message = msg
                    self.from_user = user
                    self.data = "comp:my"

                async def answer(self, text="", show_alert=False):
                    pass

            new_msg = await message_obj.answer("⏳ Загрузка...")

            await asyncio.sleep(0.2)

            fake_callback = FakeCallback(new_msg, message_obj.from_user)
            await show_my_competitions(fake_callback, state)

        logger.info("My Competitions shown")

    except Exception as e:
        logger.error(f"Error saving distances: {e}")
        if hasattr(callback_or_message, 'message'):
            await callback_or_message.answer("❌ Ошибка при сохранении", show_alert=True)
        else:
            await callback_or_message.answer("❌ Ошибка при сохранении")


async def prompt_for_target_time(callback: CallbackQuery, state: FSMContext, comp_id: str):
    """Запросить целевое время для участия"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⏭ Пропустить", callback_data=f"comp:skip_time:{comp_id}"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data=f"compdetail:{comp_id}"))

    await state.set_state(UpcomingCompetitionsStates.waiting_for_target_time)

    await callback.message.edit_text(
        "⏱ Введите целевое время для этого соревнования\n\n"
        "Формат: ЧЧ:ММ:СС (например, 01:30:00) или ММ:СС (например, 45:30)\n\n"
        "Вы можете пропустить этот шаг, нажав кнопку ниже.",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("comp:select_dist:"))
async def select_distance(callback: CallbackQuery, state: FSMContext):
    """Обработать выбор дистанции"""
    parts = callback.data.split(":", 3)
    comp_id = parts[2]
    distance_index = int(parts[3])

    try:
        data = await state.get_data()
        all_competitions = data.get('all_competitions', [])

        comp = next((c for c in all_competitions if c['id'] == comp_id), None)

        if not comp:
            await callback.answer("❌ Соревнование не найдено", show_alert=True)
            return

        distances = comp.get('distances', [])
        if distance_index >= len(distances):
            await callback.answer("❌ Дистанция не найдена", show_alert=True)
            return

        selected_dist = distances[distance_index]
        distance_km = selected_dist.get('distance', 0)
        distance_name = selected_dist.get('name', '')

        if distance_km is not None and distance_km > 0:
            selected_distance = distance_km
        else:
            selected_distance = None

        await state.update_data(
            selected_distance=selected_distance,
            selected_distance_name=distance_name
        )

        await prompt_for_target_time(callback, state, comp_id)

    except Exception as e:
        logger.error(f"Error selecting distance: {e}")
        await callback.answer("❌ Ошибка при выборе дистанции", show_alert=True)


@router.callback_query(F.data.startswith("comp:cancel:"))
async def cancel_participation(callback: CallbackQuery, state: FSMContext):
    """Отменить участие в соревновании"""
    from database.queries import remove_competition_participant

    comp_id = callback.data.split(":", 2)[2]
    user_id = callback.from_user.id

    try:
        data = await state.get_data()
        all_competitions = data.get('all_competitions', [])

        comp = next((c for c in all_competitions if c['id'] == comp_id), None)

        if not comp:
            await callback.answer("❌ Соревнование не найдено", show_alert=True)
            return

        await remove_competition_participant(user_id, comp.get('url', comp_id))

        await callback.answer(
            "✅ Участие отменено",
            show_alert=True
        )

        await show_competition_detail(callback, state)

    except Exception as e:
        logger.error(f"Error canceling participation: {e}")
        await callback.answer("❌ Ошибка при отмене", show_alert=True)


@router.callback_query(F.data.startswith("comp:skip_dist_time:"))
async def skip_distance_target_time(callback: CallbackQuery, state: FSMContext):
    """Skip target time for current distance in multi-distance flow"""
    try:
        index = int(callback.data.split(":", 2)[2])
        logger.info(f"Skipping distance time at index {index}")

        data = await state.get_data()
        distance_times = data.get('distance_times', {})
        distances_to_process = data.get('distances_to_process', [])

        logger.info(f"State has {len(distances_to_process)} distances to process")
        logger.info(f"State keys before update: {list(data.keys())}")

        distance_times[index] = None
        await state.update_data(distance_times=distance_times, current_distance_index=index)

        next_index = index + 1
        logger.info(f"Next index: {next_index}, total distances: {len(distances_to_process)}")

        if next_index >= len(distances_to_process):
            logger.info("All distances processed, calling save_all_distances_and_redirect")
            await save_all_distances_and_redirect(callback, state)
        else:
            logger.info(f"Moving to next distance at index {next_index}")
            await prompt_for_distance_time(callback, state, next_index)

    except Exception as e:
        logger.error(f"Error skipping distance time: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("comp:back_dist_time:"))
async def back_to_previous_distance_time(callback: CallbackQuery, state: FSMContext):
    """Вернуться к предыдущей дистанции для изменения целевого времени"""
    try:
        index = int(callback.data.split(":", 2)[2])
        logger.info(f"Going back to distance at index {index}")

        data = await state.get_data()
        distances_to_process = data.get('distances_to_process', [])
        distance_times = data.get('distance_times', {})

        logger.info(f"Current distance_times before going back: {distance_times}")

        if index in distance_times:
            del distance_times[index]
            await state.update_data(distance_times=distance_times, current_distance_index=index)
            logger.info(f"Cleared time for distance {index}, updated state")

        await prompt_for_distance_time(callback, state, index)

    except Exception as e:
        logger.error(f"Error going back to previous distance: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("comp:skip_time:"))
async def skip_target_time(callback: CallbackQuery, state: FSMContext):
    """Пропустить ввод целевого времени и добавить без него"""
    from database.queries import add_competition_participant
    from competitions.competitions_handlers import show_my_competitions

    comp_id = callback.data.split(":", 2)[2]
    user_id = callback.from_user.id

    try:
        data = await state.get_data()
        all_competitions = data.get('all_competitions', [])
        selected_distance = data.get('selected_distance')
        selected_distance_name = data.get('selected_distance_name')

        comp = next((c for c in all_competitions if c['id'] == comp_id), None)

        if not comp:
            await callback.answer("❌ Соревнование не найдено", show_alert=True)
            return

        await add_competition_participant(
            user_id,
            comp_id,
            comp,
            target_time=None,
            distance=selected_distance,
            distance_name=selected_distance_name
        )

        await callback.answer(
            "✅ Соревнование добавлено в 'Мои соревнования'!",
            show_alert=True
        )

        await state.clear()

        from competitions.competitions_handlers import show_my_competitions
        await show_my_competitions(callback, state)

    except Exception as e:
        logger.error(f"Error adding participant without target time: {e}")
        await callback.answer("❌ Ошибка при добавлении", show_alert=True)


@router.message(UpcomingCompetitionsStates.waiting_for_custom_distance)
async def process_custom_distance(message: Message, state: FSMContext):
    """Обработать введенную дистанцию для HeroLeague"""
    user_id = message.from_user.id

    if not message.text:
        await message.answer("❌ Пожалуйста, введите дистанцию в текстовом формате")
        return

    distance_name = message.text.strip()

    logger.info(f"User {user_id} entered custom distance: {distance_name}")

    await state.update_data(
        selected_distance_name=distance_name,
        selected_distance=None  
    )

    data = await state.get_data()
    comp_id = data.get('pending_competition_id')

    if not comp_id:
        await message.answer("❌ Ошибка: не найден ID соревнования")
        return

    await state.set_state(UpcomingCompetitionsStates.waiting_for_target_time)

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⏭ Пропустить", callback_data=f"comp:skip_time:{comp_id}"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data=f"compdetail:{comp_id}"))

    await message.answer(
        "⏱ Введите целевое время для этого соревнования\n\n"
        "Формат: ЧЧ:ММ:СС (например, 01:30:00) или ММ:СС (например, 45:30)\n\n"
        "Вы можете пропустить этот шаг, нажав кнопку ниже.",
        reply_markup=builder.as_markup()
    )


@router.message(UpcomingCompetitionsStates.waiting_for_target_time)
async def process_target_time(message: Message, state: FSMContext):
    """Обработать введенное целевое время"""
    from database.queries import add_competition_participant
    from utils.time_formatter import validate_time_format, normalize_time

    logger.info(f"process_target_time handler called! message.text={message.text}")

    user_id = message.from_user.id

    if not message.text:
        logger.warning("message.text is None or empty!")
        await message.answer("❌ Пожалуйста, введите время в текстовом формате")
        return

    target_time_text = message.text.strip()

    logger.info(f"Processing target time: {target_time_text}")

    if not validate_time_format(target_time_text):
        await message.answer(
            "❌ Неверный формат времени!\n\n"
            "Используйте формат ЧЧ:ММ:СС или ММ:СС или Ч:М:С\n"
            "Можно указать сотые: ЧЧ:ММ:СС.сс\n\n"
            "Примеры:\n"
            "• 1:30:05 или 1:30:5 (1 час 30 минут 5 секунд)\n"
            "• 45:30 (45 минут 30 секунд)\n"
            "• 1:23:45.50 (с сотыми)"
        )
        return

    target_time = normalize_time(target_time_text)

    try:
        data = await state.get_data()
        distances_to_process = data.get('distances_to_process')

        logger.info(f"State keys: {list(data.keys())}")
        logger.info(f"distances_to_process exists: {distances_to_process is not None}")

        if distances_to_process:
            logger.info(f"Multi-distance flow: {len(distances_to_process)} distances")
            current_index = data.get('current_distance_index', 0)
            distance_times = data.get('distance_times', {})

            logger.info(f"Current index: {current_index}, distance_times: {distance_times}")

            current_distance_info = distances_to_process[current_index]
            real_distance_idx = current_distance_info['index']

            logger.info(f"Storing time '{target_time}' for real distance index {real_distance_idx} (current_index={current_index})")

            distance_times[real_distance_idx] = target_time

            next_index = current_index + 1

            await state.update_data(
                distance_times=distance_times,
                current_distance_index=next_index
            )

            await message.answer(f"✅ Целевое время {target_time} сохранено!")

            if next_index >= len(distances_to_process):
                logger.info(f"All {len(distances_to_process)} distances have times, saving...")
                await save_all_distances_and_redirect(message, state)
            else:
                logger.info(f"Moving to next distance at index {next_index}")
                distance_info = distances_to_process[next_index]
                distance_name = distance_info['name']
                distance_km = distance_info['distance_km']

                user_id = message.from_user.id
                settings = await get_user_settings(user_id)
                distance_unit = settings.get('distance_unit', 'км') if settings else 'км'

                from utils.unit_converter import safe_convert_distance_name
                converted_name = safe_convert_distance_name(distance_name, distance_unit)

                display_name = converted_name

                total = len(distances_to_process)
                progress = f"[{next_index + 1}/{total}]"

                builder = InlineKeyboardBuilder()
                builder.row(InlineKeyboardButton(
                    text="⏭ Пропустить",
                    callback_data=f"comp:skip_dist_time:{next_index}"
                ))

                comp_id_val = data.get('competition_id')
                if next_index > 0:
                    builder.row(InlineKeyboardButton(
                        text="◀️ К предыдущей дистанции",
                        callback_data=f"comp:back_dist_time:{next_index-1}"
                    ))
                elif len(distances_to_process) > 1:
                    builder.row(InlineKeyboardButton(
                        text="◀️ К выбору дистанций",
                        callback_data=f"comp:participate:{comp_id_val}"
                    ))
                else:
                    builder.row(InlineKeyboardButton(
                        text="◀️ Назад",
                        callback_data=f"compdetail:{comp_id_val}"
                    ))

                logger.info("Keeping FSM state as waiting_for_target_time for next distance")

                await state.set_state(UpcomingCompetitionsStates.waiting_for_target_time)

                check_state = await state.get_state()
                logger.info(f"State before sending message: {check_state}")

                sent_msg = await message.answer(
                    f"⏱ <b>Целевое время {progress}</b>\n\n"
                    f"Дистанция: <b>{display_name}</b>\n\n"
                    f"Введите целевое время в формате:\n"
                    f"• ЧЧ:ММ:СС (например, 01:30:00)\n"
                    f"• ММ:СС (например, 45:30)\n\n"
                    f"Или нажмите ⏭ Пропустить",
                    parse_mode="HTML",
                    reply_markup=builder.as_markup()
                )
                logger.info(f"Sent prompt for distance {next_index + 1}/{total}, message_id={sent_msg.message_id}")

                final_check_state = await state.get_state()
                logger.info(f"State after sending message: {final_check_state}")

                final_data = await state.get_data()
                logger.info(f"State data after sending: keys={list(final_data.keys())}, distances_to_process exists={('distances_to_process' in final_data)}")

        else:
            comp_id = data.get('pending_competition_id')
            all_competitions = data.get('all_competitions', [])
            selected_distance = data.get('selected_distance')
            selected_distance_name = data.get('selected_distance_name', '')

            if not comp_id:
                await message.answer("❌ Ошибка: соревнование не найдено")
                return

            comp = next((c for c in all_competitions if c['id'] == comp_id), None)

            if not comp:
                await message.answer("❌ Соревнование не найдено")
                return

            await add_competition_participant(
                user_id,
                comp_id,
                comp,
                target_time=target_time,
                distance=selected_distance,
                distance_name=selected_distance_name
            )

            await message.answer("✅ Соревнование добавлено в 'Мои соревнования'!")

            await state.clear()

            from competitions.competitions_handlers import show_my_competitions

            class FakeCallback:
                def __init__(self, msg):
                    self.message = msg
                    self.from_user = msg.from_user
                    self.data = "comp:my"

                async def answer(self, text="", show_alert=False):
                    pass

            new_msg = await message.answer("⏳ Загрузка...")
            logger.info(f"Created new message for My Competitions with id={new_msg.message_id}")

            logger.info("Waiting 0.2 seconds before editing message...")
            await asyncio.sleep(0.2)

            logger.info("Returning to My Competitions (single-distance flow)...")

            fake_callback = FakeCallback(new_msg)
            await show_my_competitions(fake_callback, state)

            logger.info("My Competitions shown (single-distance flow)")

    except Exception as e:
        logger.error(f"Error processing target time: {e}")
        await message.answer("❌ Ошибка при сохранении целевого времени")


@router.callback_query(F.data == "upc:back_to_list")
async def back_to_competitions_list(callback: CallbackQuery, state: FSMContext):
    """Вернуться к списку соревнований после добавления"""
    await state.set_state(UpcomingCompetitionsStates.showing_results)

    await show_competitions_results(callback.message, state, page=1)
    await callback.answer()


