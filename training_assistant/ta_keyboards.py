"""
Клавиатуры для Training Assistant
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# Disclaimer для всех ответов
DISCLAIMER_TEXT = "\n\n⚠️ <i>Рекомендации носят исключительно информационный характер и не заменяют консультацию с врачом или профессиональным тренером. Перед началом тренировок проконсультируйтесь со специалистами.</i>"


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню Training Assistant"""
    keyboard = [
        [InlineKeyboardButton(text="📅 План тренировок", callback_data="ta:plan")],
        [InlineKeyboardButton(text="🏆 Подготовка к соревнованию", callback_data="ta:race_prep")],
        [InlineKeyboardButton(text="🎯 Тактика забега", callback_data="ta:tactics")],
        [InlineKeyboardButton(text="🧠 Спортивный психолог", callback_data="ta:psychologist")],
        [InlineKeyboardButton(text="🔮 Прогноз результата", callback_data="ta:prediction")],
        [InlineKeyboardButton(text="🔙 Закрыть", callback_data="ta:close")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_sport_type_keyboard() -> InlineKeyboardMarkup:
    """Выбор вида спорта"""
    keyboard = [
        [InlineKeyboardButton(text="🏃 Бег", callback_data="ta:sport:run")],
        [InlineKeyboardButton(text="🏊 Плавание", callback_data="ta:sport:swim")],
        [InlineKeyboardButton(text="🚴 Велоспорт", callback_data="ta:sport:bike")],
        [InlineKeyboardButton(text="« Отмена", callback_data="ta:menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_plan_duration_keyboard() -> InlineKeyboardMarkup:
    """Выбор длительности плана"""
    keyboard = [
        [InlineKeyboardButton(text="📅 На неделю", callback_data="ta:duration:week")],
        [InlineKeyboardButton(text="📆 На месяц", callback_data="ta:duration:month")],
        [InlineKeyboardButton(text="« Отмена", callback_data="ta:menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_available_days_keyboard(selected_days: list = None) -> InlineKeyboardMarkup:
    """Выбор доступных дней для тренировок (множественный выбор)"""
    if selected_days is None:
        selected_days = []

    days = [
        ("Понедельник", "Пн"),
        ("Вторник", "Вт"),
        ("Среда", "Ср"),
        ("Четверг", "Чт"),
        ("Пятница", "Пт"),
        ("Суббота", "Сб"),
        ("Воскресенье", "Вс")
    ]

    keyboard = []
    for full_name, short_name in days:
        # Добавляем галочку если день выбран
        prefix = "✅ " if short_name in selected_days else ""
        keyboard.append([
            InlineKeyboardButton(
                text=f"{prefix}{full_name}",
                callback_data=f"ta:day:{short_name}"
            )
        ])

    # Кнопка "Готово" (активна только если выбран хотя бы 1 день)
    if selected_days:
        keyboard.append([
            InlineKeyboardButton(text="✅ Готово", callback_data="ta:days:done")
        ])

    keyboard.append([
        InlineKeyboardButton(text="« Отмена", callback_data="ta:menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_feedback_keyboard() -> InlineKeyboardMarkup:
    """Выбор обратной связи по тренировке"""
    keyboard = [
        [InlineKeyboardButton(text="😓 Было слишком тяжело", callback_data="ta:fb:too_hard")],
        [InlineKeyboardButton(text="😌 Было слишком легко", callback_data="ta:fb:too_easy")],
        [InlineKeyboardButton(text="❤️ Высокий пульс", callback_data="ta:fb:high_pulse")],
        [InlineKeyboardButton(text="⏱️ Не уложился в темп", callback_data="ta:fb:slow_pace")],
        [InlineKeyboardButton(text="🚫 Не закончил тренировку", callback_data="ta:fb:didnt_finish")],
        [InlineKeyboardButton(text="« Отмена", callback_data="ta:menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_days_before_keyboard() -> InlineKeyboardMarkup:
    """Выбор периода до соревнования"""
    keyboard = [
        [InlineKeyboardButton(text="📅 За 7 дней", callback_data="ta:days:7")],
        [InlineKeyboardButton(text="📅 За 5 дней", callback_data="ta:days:5")],
        [InlineKeyboardButton(text="📅 За 3 дня", callback_data="ta:days:3")],
        [InlineKeyboardButton(text="📅 За 1 день", callback_data="ta:days:1")],
        [InlineKeyboardButton(text="« Отмена", callback_data="ta:menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_race_type_keyboard() -> InlineKeyboardMarkup:
    """Выбор типа трассы"""
    keyboard = [
        [InlineKeyboardButton(text="🏃 Ровная трасса", callback_data="ta:race:flat")],
        [InlineKeyboardButton(text="⛰️ Холмистая трасса", callback_data="ta:race:hilly")],
        [InlineKeyboardButton(text="🌲 Трейл", callback_data="ta:race:trail")],
        [InlineKeyboardButton(text="🏙️ Городской забег", callback_data="ta:race:city")],
        [InlineKeyboardButton(text="« Отмена", callback_data="ta:menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_prediction_period_keyboard() -> InlineKeyboardMarkup:
    """Выбор периода анализа для прогноза"""
    keyboard = [
        [InlineKeyboardButton(text="📊 За последний месяц", callback_data="ta:period:month")],
        [InlineKeyboardButton(text="📊 За последние 2 недели", callback_data="ta:period:2weeks")],
        [InlineKeyboardButton(text="« Отмена", callback_data="ta:menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Кнопка возврата в меню"""
    keyboard = [
        [InlineKeyboardButton(text="« Назад в меню ИИ-Ассистента", callback_data="ta:menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Кнопка отмены при вводе текста"""
    keyboard = [
        [InlineKeyboardButton(text="❌ Отмена", callback_data="ta:menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_continue_chat_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для продолжения диалога с психологом"""
    keyboard = [
        [InlineKeyboardButton(text="✅ Достаточно, спасибо", callback_data="ta:chat:end")],
        [InlineKeyboardButton(text="« Назад в меню", callback_data="ta:menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def get_user_competitions_keyboard(competitions: list, context: str, user_id: int = None) -> InlineKeyboardMarkup:
    """
    Клавиатура для выбора соревнования из списка пользователя

    Args:
        competitions: Список соревнований пользователя
        context: Контекст использования ('race_prep' или 'tactics')
        user_id: ID пользователя для получения настроек форматирования даты (опционально)
    """
    keyboard = []

    # Получаем формат даты пользователя
    date_format = 'ДД.ММ.ГГГГ'  # По умолчанию
    if user_id:
        try:
            from utils.date_formatter import get_user_date_format
            date_format = await get_user_date_format(user_id)
        except:
            pass

    for comp in competitions[:10]:  # Максимум 10 соревнований
        # Проверяем оба варианта полей для совместимости
        comp_id = comp.get('id') or comp.get('competition_id')
        title = comp.get('name') or comp.get('title', 'Без названия')
        date = comp.get('date') or comp.get('begin_date', '')

        # Форматируем дату согласно настройкам пользователя
        if date:
            try:
                from utils.date_formatter import DateFormatter
                date_str = DateFormatter.format_date(date, date_format)
                button_text = f"{title[:30]} • {date_str}"
            except:
                button_text = title[:40]
        else:
            button_text = title[:40]

        keyboard.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"ta:{context}:comp:{comp_id}"
            )
        ])

    keyboard.append([InlineKeyboardButton(text="« Отмена", callback_data="ta:menu")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
