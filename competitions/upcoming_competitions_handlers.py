"""
Handlers для раздела "Предстоящие соревнования"
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime

from competitions.competitions_fsm import UpcomingCompetitionsStates
from competitions.parser import fetch_competitions, SPORT_CODES
import logging

logger = logging.getLogger(__name__)

router = Router()


# Список популярных городов для быстрого выбора
POPULAR_CITIES = [
    "Москва",
    "Санкт-Петербург",
    "Новосибирск",
    "Екатеринбург",
    "Казань",
    "Нижний Новгород",
    "Челябинск",
    "Самара",
    "Омск",
    "Ростов-на-Дону",
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
        InlineKeyboardButton(text="◀️ Назад", callback_data="comp:back_to_menu")
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

    # Переходим к выбору вида спорта
    await show_sport_selection(callback.message, state)
    await callback.answer()


@router.message(UpcomingCompetitionsStates.waiting_for_city)
async def process_custom_city(message: Message, state: FSMContext):
    """Обработка введенного города"""
    city = message.text.strip()

    if not city:
        await message.answer("❌ Пожалуйста, введите корректное название города.")
        return

    await state.update_data(city=city, city_display=city)

    # Переходим к выбору вида спорта
    await show_sport_selection(message, state)


async def show_sport_selection(message: Message, state: FSMContext):
    """Показать выбор вида спорта"""
    data = await state.get_data()
    city_display = data.get('city_display', 'Все города')

    text = (
        f"🏃 <b>ПРЕДСТОЯЩИЕ СОРЕВНОВАНИЯ</b>\n\n"
        f"📍 Город: <b>{city_display}</b>\n\n"
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
        InlineKeyboardButton(text="🏅 Все виды спорта", callback_data="upc:sport:all")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Изменить город", callback_data="comp:upcoming")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад в меню", callback_data="comp:back_to_menu")
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

    # Показываем сообщение о загрузке
    loading_text = (
        f"🔍 <b>Поиск соревнований...</b>\n\n"
        f"📍 Город: <b>{city_display}</b>\n"
        f"🏃 Спорт: <b>{sport_display}</b>"
    )

    try:
        await message.edit_text(loading_text, parse_mode="HTML")
    except:
        msg = await message.answer(loading_text, parse_mode="HTML")
        message = msg

    # Получаем соревнования из API
    try:
        # Получаем больше соревнований для пагинации
        all_competitions = await fetch_competitions(
            city=city,
            sport=sport,
            limit=200,  # Получаем больше для пагинации
            period_months=None  # Период не используется, API возвращает все доступные
        )

        # Сохраняем все соревнования в state для пагинации
        await state.update_data(all_competitions=all_competitions)

        # Пагинация: 20 соревнований на страницу
        items_per_page = 20
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
            f"🏃 Спорт: <b>{sport_display}</b>\n\n"
            f"Попробуйте изменить параметры поиска."
        )

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🔄 Новый поиск", callback_data="comp:upcoming")
        )
        builder.row(
            InlineKeyboardButton(text="◀️ Назад в меню", callback_data="comp:back_to_menu")
        )

        await message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
        await state.clear()
        return

    # Показываем результаты
    text = (
        f"🏆 <b>НАЙДЕНО СОРЕВНОВАНИЙ: {len(all_competitions)}</b>\n"
        f"📄 Страница {page} из {total_pages}\n\n"
        f"📍 Город: <b>{city_display}</b>\n"
        f"🏃 Спорт: <b>{sport_display}</b>\n\n"
    )

    builder = InlineKeyboardBuilder()

    for i, comp in enumerate(competitions, start_idx + 1):
        # Форматируем дату
        try:
            date_obj = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
            date_str = date_obj.strftime("%d.%m.%Y")
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
        InlineKeyboardButton(text="🔄 Новый поиск", callback_data="comp:upcoming")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад в меню", callback_data="comp:back_to_menu")
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

        # Форматируем информацию
        try:
            begin_date = datetime.fromisoformat(comp['begin_date'].replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(comp['end_date'].replace('Z', '+00:00'))
            date_str = f"{begin_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"
        except:
            date_str = "Дата уточняется"

        text = (
            f"🏆 <b>{comp['title']}</b>\n\n"
            f"📅 Дата: {date_str}\n"
            f"📍 Место: {comp['place']}\n"
            f"🏃 Вид спорта: {comp['sport_code']}\n"
            f"👥 Участников: {comp['participants_count']}\n"
        )

        if comp['organizer']:
            text += f"🏢 Организатор: {comp['organizer']}\n"

        # Дистанции
        if comp['distances']:
            text += f"\n<b>📏 Дистанции:</b>\n"
            for dist in comp['distances'][:10]:
                text += f"  • {dist['name']} ({dist['distance']} км)\n"

        if comp['url']:
            text += f"\n🔗 <a href=\"{comp['url']}\">Подробнее на сайте</a>"

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="◀️ К списку", callback_data="upc:page:1")
        )
        builder.row(
            InlineKeyboardButton(text="◀️ Назад в меню", callback_data="comp:back_to_menu")
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


@router.callback_query(F.data == "comp:back_to_menu")
async def back_to_competitions_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню соревнований"""
    await state.clear()

    text = (
        "🏃 <b>СОРЕВНОВАНИЯ</b>\n\n"
        "Выберите раздел:"
    )

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📅 Предстоящие соревнования", callback_data="comp:upcoming")
    )
    builder.row(
        InlineKeyboardButton(text="🏆 Мои соревнования", callback_data="comp:my")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Главное меню", callback_data="main_menu")
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()
