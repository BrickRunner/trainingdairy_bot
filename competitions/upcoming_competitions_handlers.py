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

        # Фильтруем соревнования, в которых пользователь уже участвует
        participant_urls = await get_user_participant_competition_urls(user_id)
        all_competitions = [
            comp for comp in all_competitions
            if comp.get('url', '') not in participant_urls
        ]

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
            text += f"\n<b>📏 Дистанции:</b>\n"
            for dist in comp['distances'][:10]:
                # Форматируем дистанцию с учетом настроек пользователя
                distance_km = dist.get('distance', 0)
                if distance_km > 0:
                    distance_formatted = format_distance(distance_km, distance_unit)
                    text += f"  • {dist['name']} ({distance_formatted})\n"
                else:
                    text += f"  • {dist['name']}\n"

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
            # Если несколько дистанций - показываем выбор
            user_id = callback.from_user.id
            settings = await get_user_settings(user_id)
            distance_unit = settings.get('distance_unit', 'км') if settings else 'км'

            builder = InlineKeyboardBuilder()

            # Добавляем кнопки для каждой дистанции (максимум 15 для избежания лимита Telegram)
            for i, dist in enumerate(distances[:15]):
                distance_km = dist.get('distance', 0)
                if distance_km > 0:
                    distance_formatted = format_distance(distance_km, distance_unit)
                    button_text = f"{dist.get('name', 'Дистанция')} - {distance_formatted}"
                else:
                    button_text = dist.get('name', 'Дистанция')

                # Сохраняем индекс дистанции в callback_data
                builder.row(InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"comp:select_dist:{comp_id}:{i}"
                ))

            builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data=f"comp:detail:{comp_id}"))

            # Переводим в состояние ожидания выбора дистанции
            await state.set_state(UpcomingCompetitionsStates.waiting_for_distance)

            await callback.message.edit_text(
                "📏 <b>Выберите дистанцию:</b>\n\n"
                "Выберите дистанцию, на которой вы планируете участвовать.",
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


@router.callback_query(F.data.startswith("comp:skip_time:"))
async def skip_target_time(callback: CallbackQuery, state: FSMContext):
    """Пропустить ввод целевого времени и добавить без него"""
    from database.queries import add_competition_participant

    comp_id = callback.data.split(":", 2)[2]
    user_id = callback.from_user.id

    try:
        # Получаем данные о соревновании из state
        data = await state.get_data()
        all_competitions = data.get('all_competitions', [])
        selected_distance = data.get('selected_distance')

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
            distance=selected_distance
        )

        await callback.answer(
            "✅ Соревнование добавлено в 'Мои соревнования'!",
            show_alert=True
        )

        # Возвращаем в состояние просмотра результатов
        await state.set_state(UpcomingCompetitionsStates.showing_results)

        # Обновляем отображение (кнопка изменится на "Отменить участие")
        await show_competition_detail(callback, state)

    except Exception as e:
        logger.error(f"Error adding participant without target time: {e}")
        await callback.answer("❌ Ошибка при добавлении", show_alert=True)


@router.message(UpcomingCompetitionsStates.waiting_for_target_time)
async def process_target_time(message: Message, state: FSMContext):
    """Обработать введенное целевое время"""
    from database.queries import add_competition_participant
    import re

    user_id = message.from_user.id
    target_time_text = message.text.strip()

    # Валидация формата времени (HH:MM:SS или MM:SS)
    pattern_hhmmss = re.compile(r'^(\d{1,2}):([0-5]\d):([0-5]\d)$')
    pattern_mmss = re.compile(r'^([0-5]?\d):([0-5]\d)$')

    match_hhmmss = pattern_hhmmss.match(target_time_text)
    match_mmss = pattern_mmss.match(target_time_text)

    if match_hhmmss:
        # Формат ЧЧ:ММ:СС
        hours, minutes, seconds = match_hhmmss.groups()
        target_time = f"{int(hours):02d}:{minutes}:{seconds}"
    elif match_mmss:
        # Формат ММ:СС - добавляем часы
        minutes, seconds = match_mmss.groups()
        target_time = f"00:{int(minutes):02d}:{seconds}"
    else:
        # Неверный формат
        await message.answer(
            "❌ Неверный формат времени!\n\n"
            "Используйте формат ЧЧ:ММ:СС (например, 01:30:00) или ММ:СС (например, 45:30)"
        )
        return

    try:
        # Получаем данные из state
        data = await state.get_data()
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
            distance=selected_distance
        )

        # Формируем сообщение
        success_msg = f"✅ Соревнование добавлено в 'Мои соревнования'!\n"
        if selected_distance_name:
            success_msg += f"📏 Дистанция: {selected_distance_name}\n"
        success_msg += f"⏱ Целевое время: {target_time}"

        # Возвращаем в состояние просмотра результатов
        await state.set_state(UpcomingCompetitionsStates.showing_results)

        # Показываем кнопку для возврата к списку
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="◀️ Назад к списку", callback_data="upc:back_to_list"))

        await message.answer(success_msg, reply_markup=builder.as_markup())

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


