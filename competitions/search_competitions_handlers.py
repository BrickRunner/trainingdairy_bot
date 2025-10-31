"""
Обработчики для поиска соревнований по городу и фильтрации по месяцам
"""

import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.fsm import CompetitionStates

logger = logging.getLogger(__name__)
router = Router()


# Список крупных городов России для выбора
CITIES = [
    "Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань",
    "Нижний Новгород", "Челябинск", "Самара", "Омск", "Ростов-на-Дону",
    "Уфа", "Красноярск", "Воронеж", "Пермь", "Волгоград", "Краснодар",
    "Саратов", "Тюмень", "Тольятти", "Ижевск", "Барнаул", "Ульяновск",
    "Иркутск", "Хабаровск", "Ярославль", "Владивосток", "Махачкала",
    "Томск", "Оренбург", "Кемерово", "Новокузнецк", "Рязань", "Астрахань",
    "Пенза", "Липецк", "Тула", "Киров", "Чебоксары", "Калининград",
    "Курск", "Улан-Удэ", "Ставрополь", "Магнитогорск", "Сочи"
]

MONTHS = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]


@router.callback_query(F.data == "comp:search")
async def start_search_competitions(callback: CallbackQuery, state: FSMContext):
    """Начать поиск соревнований"""

    text = (
        "🔍 <b>ПОИСК СОРЕВНОВАНИЙ</b>\n\n"
        "Найдите соревнования по вашему городу!\n\n"
        "Выберите город:"
    )

    # Создаём клавиатуру с популярными городами
    builder = InlineKeyboardBuilder()

    # Топ-10 популярных городов
    popular_cities = CITIES[:10]

    for i in range(0, len(popular_cities), 2):
        row_buttons = []
        row_buttons.append(
            InlineKeyboardButton(
                text=popular_cities[i],
                callback_data=f"comp:city:{popular_cities[i]}"
            )
        )
        if i + 1 < len(popular_cities):
            row_buttons.append(
                InlineKeyboardButton(
                    text=popular_cities[i + 1],
                    callback_data=f"comp:city:{popular_cities[i + 1]}"
                )
            )
        builder.row(*row_buttons)

    builder.row(
        InlineKeyboardButton(text="📍 Другой город", callback_data="comp:city_other")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="comp:menu")
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "comp:city_other")
async def show_all_cities(callback: CallbackQuery, state: FSMContext):
    """Показать все города"""

    text = (
        "🔍 <b>ВЫБОР ГОРОДА</b>\n\n"
        "Выберите город из списка:"
    )

    # Создаём клавиатуру со всеми городами
    builder = InlineKeyboardBuilder()

    for i in range(0, len(CITIES), 2):
        row_buttons = []
        row_buttons.append(
            InlineKeyboardButton(
                text=CITIES[i],
                callback_data=f"comp:city:{CITIES[i]}"
            )
        )
        if i + 1 < len(CITIES):
            row_buttons.append(
                InlineKeyboardButton(
                    text=CITIES[i + 1],
                    callback_data=f"comp:city:{CITIES[i + 1]}"
                )
            )
        builder.row(*row_buttons)

    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="comp:search")
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("comp:city:"))
async def select_city(callback: CallbackQuery, state: FSMContext):
    """Выбрать город для поиска"""

    city = callback.data.split(":", 2)[2]

    # Сохраняем выбранный город
    await state.update_data(search_city=city)

    text = (
        f"📍 <b>Город: {city}</b>\n\n"
        f"Теперь выберите месяц для поиска соревнований:"
    )

    # Создаём клавиатуру с месяцами
    builder = InlineKeyboardBuilder()

    current_month = datetime.now().month

    # Показываем текущий и следующие 11 месяцев
    for i in range(12):
        month_index = (current_month - 1 + i) % 12
        month_number = month_index + 1
        month_name = MONTHS[month_index]

        # Определяем год
        year = datetime.now().year
        if current_month + i > 12:
            year += 1

        builder.row(
            InlineKeyboardButton(
                text=f"{month_name} {year}",
                callback_data=f"comp:month:{city}:{year}-{month_number:02d}"
            )
        )

    builder.row(
        InlineKeyboardButton(text="📅 Все месяцы", callback_data=f"comp:month:{city}:all")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Изменить город", callback_data="comp:search")
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("comp:month:"))
async def search_by_city_and_month(callback: CallbackQuery, state: FSMContext):
    """Поиск соревнований по городу и месяцу"""

    parts = callback.data.split(":", 3)
    city = parts[2]
    period = parts[3]  # YYYY-MM или 'all'

    await callback.answer("🔍 Ищу соревнования...", show_alert=False)

    # Ищем соревнования в базе данных
    from competitions.search_queries import search_competitions_by_city_and_month

    competitions = await search_competitions_by_city_and_month(city, period)

    if not competitions:
        # Если не нашли в БД, пробуем загрузить из Russia Running API
        from competitions.competitions_parser import load_competitions_from_api, add_competition

        # Загружаем из API
        try:
            # Парсим период для передачи в API
            if period != 'all':
                year, month = period.split('-')
                api_comps = await load_competitions_from_api(
                    city=city,
                    year=int(year),
                    month=int(month)
                )
            else:
                api_comps = await load_competitions_from_api(city=city)

            # Добавляем в БД
            added = 0
            for comp_data in api_comps:
                try:
                    await add_competition(comp_data)
                    added += 1
                except:
                    pass

            if added > 0:
                # Ищем снова
                competitions = await search_competitions_by_city_and_month(city, period)

        except Exception as e:
            logger.error(f"Error loading competitions from Russia Running API: {e}")

    if not competitions:
        # Определяем период для отображения
        if period == 'all':
            period_text = "все месяцы"
        else:
            year, month = period.split('-')
            month_name = MONTHS[int(month) - 1]
            period_text = f"{month_name} {year}"

        text = (
            f"🔍 <b>ПОИСК СОРЕВНОВАНИЙ</b>\n\n"
            f"📍 Город: <b>{city}</b>\n"
            f"📅 Период: <b>{period_text}</b>\n\n"
            f"❌ К сожалению, соревнований не найдено.\n\n"
            f"Попробуйте:\n"
            f"• Выбрать другой месяц\n"
            f"• Выбрать другой город\n"
            f"• Или создать своё соревнование вручную"
        )

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="📍 Другой город", callback_data="comp:search")
        )
        builder.row(
            InlineKeyboardButton(text="📅 Другой месяц", callback_data=f"comp:city:{city}")
        )
        builder.row(
            InlineKeyboardButton(text="➕ Создать своё", callback_data="comp:create_custom")
        )
        builder.row(
            InlineKeyboardButton(text="◀️ Назад в меню", callback_data="comp:menu")
        )

        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
        return

    # Форматируем результаты
    if period == 'all':
        period_text = "все месяцы"
    else:
        year, month = period.split('-')
        month_name = MONTHS[int(month) - 1]
        period_text = f"{month_name} {year}"

    text = (
        f"🔍 <b>НАЙДЕНО СОРЕВНОВАНИЙ: {len(competitions)}</b>\n\n"
        f"📍 Город: <b>{city}</b>\n"
        f"📅 Период: <b>{period_text}</b>\n\n"
    )

    # Показываем первые 5 соревнований
    from competitions.competitions_keyboards import format_competition_distance, format_time_until_competition

    for i, comp in enumerate(competitions[:5], 1):
        try:
            comp_date = datetime.strptime(comp['date'], '%Y-%m-%d')
            date_str = comp_date.strftime('%d.%m.%Y')
        except:
            date_str = comp['date']

        time_until = format_time_until_competition(comp['date'])

        # Форматируем дистанции
        try:
            import json
            distances = comp.get('distances', [])
            if isinstance(distances, str):
                distances = json.loads(distances)

            if distances:
                distances_str = ', '.join([format_competition_distance(float(d)) for d in distances])
            else:
                distances_str = 'Дистанции уточняются'
        except:
            distances_str = 'Дистанции уточняются'

        text += (
            f"{i}. <b>{comp['name']}</b>\n"
            f"   📅 {date_str} ({time_until})\n"
            f"   🏃 {distances_str}\n\n"
        )

    # Создаём клавиатуру с соревнованиями
    builder = InlineKeyboardBuilder()

    for i, comp in enumerate(competitions[:5], 1):
        comp_name_short = comp['name'][:40] + "..." if len(comp['name']) > 40 else comp['name']
        builder.row(
            InlineKeyboardButton(
                text=f"{i}. {comp_name_short}",
                callback_data=f"comp:view:{comp['id']}"
            )
        )

    if len(competitions) > 5:
        text += f"\n<i>Показано 5 из {len(competitions)} соревнований</i>"

    builder.row(
        InlineKeyboardButton(text="📅 Другой месяц", callback_data=f"comp:city:{city}")
    )
    builder.row(
        InlineKeyboardButton(text="📍 Другой город", callback_data="comp:search")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад в меню", callback_data="comp:menu")
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
