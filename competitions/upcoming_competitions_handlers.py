"""
Handlers для раздела "Предстоящие соревнования"
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime

from competitions.competitions_fsm import UpcomingCompetitionsStates
from competitions.parser import fetch_competitions, SPORT_CODES, SPORT_NAMES
from database.queries import get_user_settings, add_competition_participant, is_user_participant, get_user_participant_competition_urls
from utils.date_formatter import DateFormatter
from utils.unit_converter import format_distance
import logging

logger = logging.getLogger(__name__)

router = Router()


# Список городов для быстрого выбора
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

    # Показываем клавиатуру с популярными городами
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
        # Пользователь хочет ввести свой город
        await callback.message.edit_text(
            "✏️ Введите название города:",
            parse_mode="HTML"
        )
        await state.set_state(UpcomingCompetitionsStates.waiting_for_city)
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

    # Переходим к выбору периода
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

    # Добавляем периоды
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
        # Если не получается редактировать (например, после ввода текста)
        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )

    await state.set_state(UpcomingCompetitionsStates.waiting_for_period)


@router.callback_query(F.data.startswith("upc:period:"))
async def select_period(callback: CallbackQuery, state: FSMContext):
    """Выбор периода"""
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

    # Добавляем виды спорта
    for sport_name, sport_code in SPORT_CODES.items():
        builder.row(
            InlineKeyboardButton(
                text=sport_name,
                callback_data=f"upc:sport:{sport_code}"
            )
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
        # Если не получается редактировать (например, после ввода текста)
        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )

    await state.set_state(UpcomingCompetitionsStates.waiting_for_sport)


@router.callback_query(F.data.startswith("upc:sport:"))
async def select_sport(callback: CallbackQuery, state: FSMContext):
    """Выбор вида спорта и показ результатов"""
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

    # Показываем результаты
    await show_competitions_results(callback.message, state)
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

    # Получаем user_id и настройки
    user_id = message.chat.id
    settings = await get_user_settings(user_id)
    date_format = settings.get('date_format', 'ДД.ММ.ГГГГ') if settings else 'ДД.ММ.ГГГГ'

    # Показываем сообщение о загрузке
    loading_text = (
        f"🔍 <b>Поиск соревнований...</b>\n\n"
        f"📍 Город: <b>{city_display}</b>\n"
        f"📅 Период: <b>{period_display}</b>\n"
        f"🏃 Спорт: <b>{sport_display}</b>"
    )

    try:
        await message.edit_text(loading_text, parse_mode="HTML")
    except:
        msg = await message.answer(loading_text, parse_mode="HTML")
        message = msg

    # Получаем соревнования из API
    try:
        # Логируем параметры для отладки
        logger.info(f"Fetching competitions: city={city}, sport={sport}, period_months={period_months}")

        # Получаем все соревнования с фильтрацией по периоду
        all_competitions = await fetch_competitions(
            city=city,
            sport=sport,
            limit=1000,  # Получаем максимум для фильтрации по периоду
            period_months=period_months
        )

        logger.info(f"Received {len(all_competitions)} competitions after filtering")

        # Фильтруем соревнования:
        # - Если 1 дистанция И пользователь участвует -> скрываем
        # - Если >1 дистанции И пользователь зарегистрирован на ВСЕ -> скрываем
        # - Иначе показываем
        from database.queries import is_user_registered_all_distances

        filtered_competitions = []
        for comp in all_competitions:
            comp_url = comp.get('url', '')
            distances_count = len(comp.get('distances', []))

            if distances_count <= 1:
                # Одна дистанция или нет дистанций - скрываем если участвует
                participant_urls = await get_user_participant_competition_urls(user_id)
                if comp_url not in participant_urls:
                    filtered_competitions.append(comp)
            else:
                # Несколько дистанций - скрываем только если зарегистрирован на все
                is_all_registered = await is_user_registered_all_distances(user_id, comp_url, distances_count)
                if not is_all_registered:
                    filtered_competitions.append(comp)

        all_competitions = filtered_competitions
        logger.info(f"After filtering participant competitions: {len(all_competitions)} competitions")

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
        await message.edit_text(
            "❌ Произошла ошибка при получении данных.\n"
            "Попробуйте позже.",
            parse_mode="HTML"
        )
        await state.clear()
        return

    if not all_competitions:
        # Нет соревнований
        text = (
            f"😔 <b>Соревнования не найдены</b>\n\n"
            f"📍 Город: <b>{city_display}</b>\n"
            f"📅 Период: <b>{period_display}</b>\n"
            f"🏃 Спорт: <b>{sport_display}</b>\n\n"
            f"Попробуйте изменить параметры поиска."
        )

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="◀️ Назад в меню", callback_data="comp:menu")
        )

        await message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
        await state.clear()
        return

    # Показываем результаты
    text = (
        f"🏆 <b>НАЙДЕНО СОРЕВНОВАНИЙ: {len(all_competitions)}</b>\n"
        f"📄 Страница {page} из {total_pages}\n\n"
        f"📍 Город: <b>{city_display}</b>\n"
        f"📅 Период: <b>{period_display}</b>\n"
        f"🏃 Спорт: <b>{sport_display}</b>\n\n"
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

        builder.row(
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"compdetail:{comp['id']}"
            )
        )

    # Кнопки пагинации
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

    # Кнопки навигации
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

    # Показываем результаты для выбранной страницы
    await show_competitions_results(callback.message, state, page)
    await callback.answer()


@router.callback_query(F.data.startswith("compdetail:"))
async def show_competition_detail(callback: CallbackQuery, state: FSMContext):
    """Показать детальную информацию о соревновании"""
    comp_id = callback.data.split(":", 1)[1]

    # Получаем данные о соревновании из state
    data = await state.get_data()
    all_competitions = data.get('all_competitions', [])

    try:
        # Ищем соревнование в сохраненных данных
        comp = next((c for c in all_competitions if c['id'] == comp_id), None)

        if not comp:
            await callback.answer("❌ Соревнование не найдено", show_alert=True)
            return

        # Получаем настройки пользователя
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
            f"📅 Дата: {date_str}\n"
            f"📍 Место: {comp['place']}\n"
            f"🏃 Вид спорта: {sport_name_ru}\n"
        )

        # Дистанции
        if comp['distances']:
            from utils.unit_converter import safe_convert_distance_name

            text += f"\n<b>📏 Дистанции:</b>\n"
            for dist in comp['distances'][:10]:
                # Форматируем дистанцию с учетом настроек пользователя
                distance_km = dist.get('distance', 0)
                distance_name = dist.get('name', 'Дистанция')

                # Конвертируем название дистанции (безопасно, с fallback)
                converted_name = safe_convert_distance_name(distance_name, distance_unit)

                # Показываем только сконвертированное название
                # Не дублируем информацию о дистанции
                text += f"  • {converted_name}\n"

        if comp['url']:
            text += f"\n🔗 <a href=\"{comp['url']}\">Подробнее на сайте</a>"

        # Проверяем, уже участвует ли пользователь
        is_participant = await is_user_participant(user_id, comp.get('url', comp_id))

        builder = InlineKeyboardBuilder()
        if is_participant:
            builder.row(
                InlineKeyboardButton(text="❌ Отменить участие", callback_data=f"comp:cancel:{comp_id}")
            )
        else:
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
        # Получаем данные о соревновании из state
        data = await state.get_data()
        all_competitions = data.get('all_competitions', [])

        # Ищем соревнование в сохраненных данных
        comp = next((c for c in all_competitions if c['id'] == comp_id), None)

        if not comp:
            await callback.answer("❌ Соревнование не найдено", show_alert=True)
            return

        # Сохраняем comp_id в state для последующего использования
        await state.update_data(pending_competition_id=comp_id)

        # Проверяем количество дистанций
        distances = comp.get('distances', [])

        if len(distances) > 1:
            # Если несколько дистанций - показываем множественный выбор с чекбоксами
            user_id = callback.from_user.id
            settings = await get_user_settings(user_id)
            distance_unit = settings.get('distance_unit', 'км') if settings else 'км'

            # Инициализируем список выбранных дистанций если его нет
            await state.update_data(selected_distances=[])

            builder = InlineKeyboardBuilder()

            # Добавляем кнопки для каждой дистанции с чекбоксами (максимум 15)
            from utils.unit_converter import safe_convert_distance_name

            for i, dist in enumerate(distances[:15]):
                distance_km = dist.get('distance', 0)
                distance_name = dist.get('name', 'Дистанция')

                # Конвертируем название дистанции (безопасно, с fallback)
                converted_name = safe_convert_distance_name(distance_name, distance_unit)

                # Показываем только сконвертированное название, без дублирования
                button_text = f"☐ {converted_name}"

                # Чекбокс: toggle выбора дистанции
                builder.row(InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"comp:toggle_dist:{comp_id}:{i}"
                ))

            # Кнопка продолжить (будет активна когда выбрана хотя бы одна дистанция)
            builder.row(InlineKeyboardButton(
                text="✅ Продолжить",
                callback_data=f"comp:confirm_distances:{comp_id}"
            ))
            builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data=f"comp:detail:{comp_id}"))

            # Переводим в состояние выбора нескольких дистанций
            await state.set_state(UpcomingCompetitionsStates.selecting_multiple_distances)

            await callback.message.edit_text(
                "📏 <b>Выберите дистанции:</b>\n\n"
                "Выберите одну или несколько дистанций, на которых вы планируете участвовать.\n"
                "Нажмите на дистанцию чтобы выбрать/отменить выбор.\n\n"
                "После выбора нажмите ✅ Продолжить",
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
            await callback.answer()

        elif len(distances) == 1:
            # Если только одна дистанция - сохраняем её и переходим к вводу времени
            distance_km = distances[0].get('distance', 0)
            await state.update_data(selected_distance=distance_km, selected_distance_name=distances[0].get('name', ''))

            # Переходим к вводу целевого времени
            await prompt_for_target_time(callback, state, comp_id)

        else:
            # Нет дистанций - сохраняем без дистанции и переходим к вводу времени
            await state.update_data(selected_distance=None, selected_distance_name=None)
            await prompt_for_target_time(callback, state, comp_id)

    except Exception as e:
        logger.error(f"Error starting participation: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("comp:toggle_dist:"))
async def toggle_distance_selection(callback: CallbackQuery, state: FSMContext):
    """Toggle distance selection (checkbox)"""
    try:
        parts = callback.data.split(":", 3)
        comp_id = parts[2]
        distance_idx = int(parts[3])

        # Get current selections and competition data
        data = await state.get_data()
        selected_distances = data.get('selected_distances', [])
        all_competitions = data.get('all_competitions', [])

        # Find competition
        competition = None
        for comp in all_competitions:
            if comp.get('id') == comp_id:
                competition = comp
                break

        if not competition:
            await callback.answer("❌ Соревнование не найдено", show_alert=True)
            return

        distances = competition.get('distances', [])

        # Toggle selection
        if distance_idx in selected_distances:
            selected_distances.remove(distance_idx)
        else:
            selected_distances.append(distance_idx)

        await state.update_data(selected_distances=selected_distances)

        # Rebuild keyboard with updated checkmarks
        user_id = callback.from_user.id
        settings = await get_user_settings(user_id)
        distance_unit = settings.get('distance_unit', 'км') if settings else 'км'

        builder = InlineKeyboardBuilder()

        from utils.unit_converter import safe_convert_distance_name

        for i, dist in enumerate(distances[:15]):
            distance_km = dist.get('distance', 0)
            distance_name = dist.get('name', 'Дистанция')
            converted_name = safe_convert_distance_name(distance_name, distance_unit)

            # Show checkmark if selected
            checkbox = "✓" if i in selected_distances else "☐"

            # Показываем только сконвертированное название, без дублирования
            button_text = f"{checkbox} {converted_name}"

            builder.row(InlineKeyboardButton(
                text=button_text,
                callback_data=f"comp:toggle_dist:{comp_id}:{i}"
            ))

        # Continue button
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

        # Get selected distances
        data = await state.get_data()
        selected_distances = data.get('selected_distances', [])

        if not selected_distances:
            await callback.answer("⚠️ Выберите хотя бы одну дистанцию", show_alert=True)
            return

        all_competitions = data.get('all_competitions', [])

        # Find competition
        competition = None
        for comp in all_competitions:
            if comp.get('id') == comp_id:
                competition = comp
                break

        if not competition:
            await callback.answer("❌ Соревнование не найдено", show_alert=True)
            return

        distances = competition.get('distances', [])

        # Store info about distances to process
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
            current_competition=competition  # Save full competition object
        )

        # Start with first distance
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
        # All distances processed - save and redirect
        logger.info("Index >= length, calling save_all_distances_and_redirect")
        await save_all_distances_and_redirect(callback, state)
        return

    distance_info = distances_to_process[index]
    distance_name = distance_info['name']
    distance_km = distance_info['distance_km']

    logger.info(f"Prompting for distance: {distance_name} ({distance_km}km)")

    # Get user settings for unit conversion
    user_id = callback.from_user.id
    settings = await get_user_settings(user_id)
    distance_unit = settings.get('distance_unit', 'км') if settings else 'км'

    from utils.unit_converter import safe_convert_distance_name
    converted_name = safe_convert_distance_name(distance_name, distance_unit)

    # Показываем только сконвертированное название, без дублирования
    display_name = converted_name

    # Create keyboard
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="⏭ Пропустить",
        callback_data=f"comp:skip_dist_time:{index}"
    ))

    # Умная кнопка "Назад"
    if index > 0:
        # Если это не первая дистанция - возвращаемся к предыдущей
        builder.row(InlineKeyboardButton(
            text="◀️ К предыдущей дистанции",
            callback_data=f"comp:back_dist_time:{index-1}"
        ))
    elif len(distances_to_process) > 1:
        # Если первая дистанция и их несколько - возвращаемся к выбору дистанций
        builder.row(InlineKeyboardButton(
            text="◀️ К выбору дистанций",
            callback_data=f"comp:participate:{comp_id}"
        ))
    else:
        # Если одна дистанция - возвращаемся к деталям соревнования
        builder.row(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=f"compdetail:{comp_id}"
        ))

    logger.info(f"Setting FSM state to waiting_for_target_time")
    await state.set_state(UpcomingCompetitionsStates.waiting_for_target_time)

    # Verify state was set
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
        competition = data.get('current_competition')  # Get saved competition object
        distance_times = data.get('distance_times', {})

        logger.info(f"Processing {len(distances_to_process)} distances")
        logger.info(f"comp_id: {comp_id}, competition exists: {competition is not None}")
        logger.info(f"distance_times: {distance_times}")

        # Determine if it's a callback or message
        if hasattr(callback_or_message, 'message'):
            # It's a CallbackQuery
            logger.info("Detected as CallbackQuery")
            user_id = callback_or_message.from_user.id
            message_obj = callback_or_message.message
        else:
            # It's a Message
            logger.info("Detected as Message")
            user_id = callback_or_message.from_user.id
            message_obj = callback_or_message

        if not competition:
            if hasattr(callback_or_message, 'message'):
                await callback_or_message.answer("❌ Соревнование не найдено", show_alert=True)
            else:
                await callback_or_message.answer("❌ Соревнование не найдено")
            return

        # Save each distance
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

        # Show success message and redirect
        count = len(distances_to_process)
        logger.info(f"Showing success message for {count} distances")

        # Show success alert and immediately redirect to "Мои соревнования"
        if hasattr(callback_or_message, 'message'):
            # It's CallbackQuery
            logger.info("Sending success alert and redirecting via CallbackQuery")
            await callback_or_message.answer(
                f"✅ Зарегистрированы на {count} дистанций!",
                show_alert=True
            )
        else:
            # It's Message - show quick notification
            logger.info("Sending success message and redirecting via Message")
            await message_obj.answer(f"✅ Зарегистрированы на {count} дистанций!")

        # Clear state
        await state.clear()

        # Redirect to "Мои соревнования" by simulating callback
        from competitions.competitions_handlers import show_my_competitions

        # Create a fake callback query with the message
        if hasattr(callback_or_message, 'message'):
            # It's already a CallbackQuery - use it directly
            await show_my_competitions(callback_or_message, state)
        else:
            # It's a Message - create a pseudo callback to use the original handler
            class PseudoCallbackQuery:
                """Wrapper to make Message look like CallbackQuery for show_my_competitions"""
                def __init__(self, message):
                    self.message = message
                    self.from_user = message.from_user

                async def answer(self, text="", show_alert=False):
                    # Ignore callback answers for message-based flow
                    pass

            # Send a placeholder message to edit
            placeholder_message = await message_obj.answer("Загрузка...")

            # Create pseudo callback with the placeholder message
            pseudo_callback = PseudoCallbackQuery(placeholder_message)

            # Use the original handler
            await show_my_competitions(pseudo_callback, state)

    except Exception as e:
        logger.error(f"Error saving distances: {e}")
        if hasattr(callback_or_message, 'message'):
            await callback_or_message.answer("❌ Ошибка при сохранении", show_alert=True)
        else:
            await callback_or_message.answer("❌ Ошибка при сохранении")


async def prompt_for_target_time(callback: CallbackQuery, state: FSMContext, comp_id: str):
    """Запросить целевое время для участия"""
    # Создаем клавиатуру с кнопкой "Пропустить"
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⏭ Пропустить", callback_data=f"comp:skip_time:{comp_id}"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data=f"comp:detail:{comp_id}"))

    # Переводим в состояние ожидания целевого времени
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
        # Получаем данные о соревновании из state
        data = await state.get_data()
        all_competitions = data.get('all_competitions', [])

        # Ищем соревнование в сохраненных данных
        comp = next((c for c in all_competitions if c['id'] == comp_id), None)

        if not comp:
            await callback.answer("❌ Соревнование не найдено", show_alert=True)
            return

        distances = comp.get('distances', [])
        if distance_index >= len(distances):
            await callback.answer("❌ Дистанция не найдена", show_alert=True)
            return

        # Сохраняем выбранную дистанцию
        selected_dist = distances[distance_index]
        distance_km = selected_dist.get('distance', 0)
        distance_name = selected_dist.get('name', '')

        await state.update_data(
            selected_distance=distance_km if distance_km > 0 else None,
            selected_distance_name=distance_name
        )

        # Переходим к вводу целевого времени
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
        # Получаем данные о соревновании из state
        data = await state.get_data()
        all_competitions = data.get('all_competitions', [])

        # Ищем соревнование в сохраненных данных
        comp = next((c for c in all_competitions if c['id'] == comp_id), None)

        if not comp:
            await callback.answer("❌ Соревнование не найдено", show_alert=True)
            return

        # Удаляем пользователя из участников
        await remove_competition_participant(user_id, comp.get('url', comp_id))

        await callback.answer(
            "✅ Участие отменено",
            show_alert=True
        )

        # Обновляем отображение (кнопка изменится на "Я участвую")
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

        # Store None for this distance (skipped)
        distance_times[index] = None
        await state.update_data(distance_times=distance_times, current_distance_index=index)

        # Move to next distance
        next_index = index + 1
        logger.info(f"Next index: {next_index}, total distances: {len(distances_to_process)}")

        # Check if there are more distances
        if next_index >= len(distances_to_process):
            # All distances processed - save and redirect
            logger.info("All distances processed, calling save_all_distances_and_redirect")
            await save_all_distances_and_redirect(callback, state)
        else:
            # Move to next distance
            logger.info(f"Moving to next distance at index {next_index}")
            await prompt_for_distance_time(callback, state, next_index)

    except Exception as e:
        logger.error(f"Error skipping distance time: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("comp:skip_time:"))
async def skip_target_time(callback: CallbackQuery, state: FSMContext):
    """Пропустить ввод целевого времени и добавить без него"""
    from database.queries import add_competition_participant
    from competitions.competitions_handlers import show_my_competitions

    comp_id = callback.data.split(":", 2)[2]
    user_id = callback.from_user.id

    try:
        # Получаем данные о соревновании из state
        data = await state.get_data()
        all_competitions = data.get('all_competitions', [])
        selected_distance = data.get('selected_distance')
        selected_distance_name = data.get('selected_distance_name')

        # Ищем соревнование в сохраненных данных
        comp = next((c for c in all_competitions if c['id'] == comp_id), None)

        if not comp:
            await callback.answer("❌ Соревнование не найдено", show_alert=True)
            return

        # Добавляем пользователя как участника без целевого времени, но с дистанцией
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

        # Очищаем state
        await state.clear()

        # Показываем раздел "Мои соревнования"
        await show_my_competitions(callback, state)

    except Exception as e:
        logger.error(f"Error adding participant without target time: {e}")
        await callback.answer("❌ Ошибка при добавлении", show_alert=True)


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

    # Валидация формата времени используя общую функцию
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

    # Нормализуем время (убираем ведущие нули из часов)
    target_time = normalize_time(target_time_text)

    try:
        # Получаем данные из state
        data = await state.get_data()
        distances_to_process = data.get('distances_to_process')

        logger.info(f"State keys: {list(data.keys())}")
        logger.info(f"distances_to_process exists: {distances_to_process is not None}")

        # Check if this is multi-distance flow
        if distances_to_process:
            # Multi-distance flow
            logger.info(f"Multi-distance flow: {len(distances_to_process)} distances")
            current_index = data.get('current_distance_index', 0)
            distance_times = data.get('distance_times', {})

            logger.info(f"Current index: {current_index}, distance_times: {distance_times}")

            # Store time for current distance
            distance_times[current_index] = target_time

            # Move to next distance FIRST
            next_index = current_index + 1

            # Update both distance_times AND current_distance_index in one call
            await state.update_data(
                distance_times=distance_times,
                current_distance_index=next_index
            )

            await message.answer(f"✅ Целевое время {target_time} сохранено!")

            # Check if there are more distances to process
            if next_index >= len(distances_to_process):
                # All distances processed - save and redirect
                logger.info(f"All {len(distances_to_process)} distances have times, saving...")
                await save_all_distances_and_redirect(message, state)
            else:
                # Prompt for next distance
                logger.info(f"Moving to next distance at index {next_index}")
                distance_info = distances_to_process[next_index]
                distance_name = distance_info['name']
                distance_km = distance_info['distance_km']

                user_id = message.from_user.id
                settings = await get_user_settings(user_id)
                distance_unit = settings.get('distance_unit', 'км') if settings else 'км'

                from utils.unit_converter import safe_convert_distance_name
                converted_name = safe_convert_distance_name(distance_name, distance_unit)

                # Показываем только сконвертированное название, без дублирования
                display_name = converted_name

                total = len(distances_to_process)
                progress = f"[{next_index + 1}/{total}]"

                builder = InlineKeyboardBuilder()
                builder.row(InlineKeyboardButton(
                    text="⏭ Пропустить",
                    callback_data=f"comp:skip_dist_time:{next_index}"
                ))
                comp_id_val = data.get('competition_id')
                builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data=f"comp:detail:{comp_id_val}"))

                # IMPORTANT: Keep FSM state for next input
                logger.info("Keeping FSM state as waiting_for_target_time for next distance")

                # Set state BEFORE sending message
                await state.set_state(UpcomingCompetitionsStates.waiting_for_target_time)

                # Verify state
                check_state = await state.get_state()
                logger.info(f"State before sending message: {check_state}")

                # Send message with keyboard
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

                # Verify state AGAIN after sending
                final_check_state = await state.get_state()
                logger.info(f"State after sending message: {final_check_state}")

                # Get all state data to verify it's not cleared
                final_data = await state.get_data()
                logger.info(f"State data after sending: keys={list(final_data.keys())}, distances_to_process exists={('distances_to_process' in final_data)}")

        else:
            # Single distance flow (original behavior)
            comp_id = data.get('pending_competition_id')
            all_competitions = data.get('all_competitions', [])
            selected_distance = data.get('selected_distance')
            selected_distance_name = data.get('selected_distance_name', '')

            if not comp_id:
                await message.answer("❌ Ошибка: соревнование не найдено")
                return

            # Ищем соревнование в сохраненных данных
            comp = next((c for c in all_competitions if c['id'] == comp_id), None)

            if not comp:
                await message.answer("❌ Соревнование не найдено")
                return

            # Добавляем пользователя как участника с целевым временем и дистанцией
            await add_competition_participant(
                user_id,
                comp_id,
                comp,
                target_time=target_time,
                distance=selected_distance,
                distance_name=selected_distance_name
            )

            # Отправляем подтверждение
            await message.answer("✅ Соревнование добавлено в 'Мои соревнования'!")

            # Автоматически показываем раздел "Мои соревнования"
            from competitions.competitions_handlers import show_my_competitions

            class FakeCallback:
                def __init__(self, msg):
                    self.message = msg
                    self.from_user = msg.from_user

                async def answer(self, text="", show_alert=False):
                    pass

            placeholder_msg = await message.answer("Загрузка...")
            fake_callback = FakeCallback(placeholder_msg)

            await show_my_competitions(fake_callback, state)

            # Очищаем state ПОСЛЕ показа ТОЛЬКО для single-distance flow
            await state.clear()

    except Exception as e:
        logger.error(f"Error processing target time: {e}")
        await message.answer("❌ Ошибка при сохранении целевого времени")


@router.callback_query(F.data == "upc:back_to_list")
async def back_to_competitions_list(callback: CallbackQuery, state: FSMContext):
    """Вернуться к списку соревнований после добавления"""
    # Переводим в правильное состояние
    await state.set_state(UpcomingCompetitionsStates.showing_results)

    # Показываем список с первой страницы
    await show_competitions_results(callback.message, state, page=1)
    await callback.answer()


