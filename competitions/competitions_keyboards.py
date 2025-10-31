"""
Клавиатуры для раздела соревнований
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from typing import List, Dict, Any
from datetime import datetime, date


def get_competitions_main_menu() -> InlineKeyboardMarkup:
    """Главное меню раздела соревнований"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="📅 Предстоящие соревнования", callback_data="comp:upcoming")
    )
    builder.row(
        InlineKeyboardButton(text="✅ Мои соревнования", callback_data="comp:my")
    )
    builder.row(
        InlineKeyboardButton(text="➕ Создать своё соревнование", callback_data="comp:create_custom")
    )
    builder.row(
        InlineKeyboardButton(text="🏅 Мои результаты", callback_data="comp:my_results")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="comp:statistics")
    )
    builder.row(
        InlineKeyboardButton(text="🔍 Поиск соревнований", callback_data="comp:search")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_menu")
    )

    return builder.as_markup()


def get_competition_card_keyboard(
    competition_id: int,
    is_registered: bool = False,
    has_multiple_distances: bool = False,
    show_back: bool = True
) -> InlineKeyboardMarkup:
    """
    Клавиатура для карточки соревнования

    Args:
        competition_id: ID соревнования
        is_registered: Зарегистрирован ли пользователь
        has_multiple_distances: Есть ли несколько дистанций
        show_back: Показывать ли кнопку "Назад"
    """
    builder = InlineKeyboardBuilder()

    if is_registered:
        builder.row(
            InlineKeyboardButton(
                text="✅ Вы зарегистрированы",
                callback_data=f"comp:view_registration:{competition_id}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="📊 Моя подготовка",
                callback_data=f"comp:preparation:{competition_id}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="❌ Отменить участие",
                callback_data=f"comp:unregister:{competition_id}"
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
        else:
            builder.row(
                InlineKeyboardButton(
                    text="✍️ Зарегистрироваться",
                    callback_data=f"comp:register:{competition_id}"
                )
            )

    builder.row(
        InlineKeyboardButton(
            text="🌐 Официальный сайт",
            url=f"comp_url_{competition_id}"  # Будет заменён на реальный URL
        )
    )

    if show_back:
        builder.row(
            InlineKeyboardButton(text="◀️ Назад", callback_data="comp:upcoming")
        )

    return builder.as_markup()


def get_distance_selection_keyboard(competition_id: int, distances: List[float]) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора дистанции

    Args:
        competition_id: ID соревнования
        distances: Список доступных дистанций
    """
    builder = InlineKeyboardBuilder()

    # Форматируем дистанции красиво
    distance_names = {
        42.195: "🏃 Марафон (42.195 км)",
        21.1: "🏃 Полумарафон (21.1 км)",
        10.0: "🏃 10 км",
        5.0: "🏃 5 км",
        3.0: "🏃 3 км"
    }

    for distance in sorted(distances, reverse=True):
        # Если есть красивое имя, используем его, иначе просто км
        text = distance_names.get(distance, f"🏃 {distance} км")
        builder.row(
            InlineKeyboardButton(
                text=text,
                callback_data=f"comp:register_dist:{competition_id}:{distance}"
            )
        )

    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data=f"comp:view:{competition_id}")
    )

    return builder.as_markup()


def get_my_competitions_menu() -> InlineKeyboardMarkup:
    """Меню 'Мои соревнования'"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="📅 Предстоящие", callback_data="comp:my:upcoming")
    )
    builder.row(
        InlineKeyboardButton(text="🏁 Завершённые", callback_data="comp:my:finished")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="comp:menu")
    )

    return builder.as_markup()


def get_my_competition_keyboard(competition_id: int, has_result: bool = False) -> InlineKeyboardMarkup:
    """
    Клавиатура для карточки моего соревнования

    Args:
        competition_id: ID соревнования
        has_result: Добавлен ли результат
    """
    builder = InlineKeyboardBuilder()

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

    builder.row(
        InlineKeyboardButton(
            text="📈 Статистика подготовки",
            callback_data=f"comp:preparation:{competition_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="comp:my")
    )

    return builder.as_markup()


def get_search_filters_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура фильтров поиска"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="📅 По дате", callback_data="comp:filter:date")
    )
    builder.row(
        InlineKeyboardButton(text="🏙️ По городу", callback_data="comp:filter:city")
    )
    builder.row(
        InlineKeyboardButton(text="🏃 По типу", callback_data="comp:filter:type")
    )
    builder.row(
        InlineKeyboardButton(text="🔍 Поиск по названию", callback_data="comp:filter:name")
    )
    builder.row(
        InlineKeyboardButton(text="🔄 Сбросить фильтры", callback_data="comp:filter:reset")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="comp:menu")
    )

    return builder.as_markup()


def get_competition_type_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа соревнования"""
    builder = InlineKeyboardBuilder()

    types = [
        ("🏃 Марафон", "марафон"),
        ("🏃 Полумарафон", "полумарафон"),
        ("🏃 Забег", "забег"),
        ("⛰️ Трейл", "трейл"),
        ("🏃 Ультрамарафон", "ультра"),
    ]

    for text, type_value in types:
        builder.row(
            InlineKeyboardButton(text=text, callback_data=f"comp:type:{type_value}")
        )

    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="comp:search")
    )

    return builder.as_markup()


def get_pagination_keyboard(
    callback_prefix: str,
    page: int,
    total_pages: int,
    back_callback: str = "comp:menu"
) -> InlineKeyboardMarkup:
    """
    Клавиатура пагинации для списков

    Args:
        callback_prefix: Префикс для callback (например "comp:upcoming:page")
        page: Текущая страница (начинается с 1)
        total_pages: Всего страниц
        back_callback: Callback для кнопки "Назад"
    """
    builder = InlineKeyboardBuilder()

    buttons = []

    # Кнопка "Предыдущая"
    if page > 1:
        buttons.append(
            InlineKeyboardButton(text="◀️", callback_data=f"{callback_prefix}:{page-1}")
        )

    # Показываем текущую страницу
    buttons.append(
        InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop")
    )

    # Кнопка "Следующая"
    if page < total_pages:
        buttons.append(
            InlineKeyboardButton(text="▶️", callback_data=f"{callback_prefix}:{page+1}")
        )

    if buttons:
        builder.row(*buttons)

    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data=back_callback)
    )

    return builder.as_markup()


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой отмены"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="❌ Отмена"))
    return builder.as_markup(resize_keyboard=True)


def get_result_input_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для ввода результатов"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="⏭️ Пропустить"),
        KeyboardButton(text="❌ Отмена")
    )
    return builder.as_markup(resize_keyboard=True)


def format_competition_distance(distance: float) -> str:
    """
    Форматировать дистанцию для отображения

    Args:
        distance: Дистанция в км

    Returns:
        Отформатированная строка
    """
    if distance == 42.195:
        return "Марафон (42.195 км)"
    elif distance == 21.1:
        return "Полумарафон (21.1 км)"
    elif distance == int(distance):
        return f"{int(distance)} км"
    else:
        return f"{distance} км"


def format_time_until_competition(competition_date: str) -> str:
    """
    Рассчитать и отформатировать время до соревнования

    Args:
        competition_date: Дата соревнования в формате YYYY-MM-DD

    Returns:
        Отформатированная строка
    """
    try:
        comp_date = datetime.strptime(competition_date, '%Y-%m-%d').date()
        today = date.today()
        delta = (comp_date - today).days

        if delta < 0:
            return "Завершено"
        elif delta == 0:
            return "Сегодня!"
        elif delta == 1:
            return "Завтра!"
        elif delta < 7:
            return f"Через {delta} дней"
        elif delta < 30:
            weeks = delta // 7
            return f"Через {weeks} нед."
        elif delta < 365:
            months = delta // 30
            return f"Через {months} мес."
        else:
            years = delta // 365
            return f"Через {years} г."
    except:
        return "Дата неизвестна"


def get_month_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора месяца"""
    builder = InlineKeyboardBuilder()

    months = [
        ("Январь", 1), ("Февраль", 2), ("Март", 3),
        ("Апрель", 4), ("Май", 5), ("Июнь", 6),
        ("Июль", 7), ("Август", 8), ("Сентябрь", 9),
        ("Октябрь", 10), ("Ноябрь", 11), ("Декабрь", 12)
    ]

    for month_name, month_num in months:
        builder.button(
            text=month_name,
            callback_data=f"comp:month:{month_num}"
        )

    builder.adjust(3)  # 3 кнопки в ряд

    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="comp:search")
    )

    return builder.as_markup()
