"""
Клавиатуры для раздела настроек
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def get_settings_menu_keyboard(is_coach: bool = False) -> InlineKeyboardMarkup:
    """
    Главное меню настроек

    Args:
        is_coach: Показывать ли статус тренера
    """
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="👤 Профиль", callback_data="settings:profile")
    )
    builder.row(
        InlineKeyboardButton(text="💓 Пульсовые зоны", callback_data="settings:pulse_zones")
    )
    builder.row(
        InlineKeyboardButton(text="🎯 Цели", callback_data="settings:goals")
    )
    builder.row(
        InlineKeyboardButton(text="📏 Единицы измерения", callback_data="settings:units")
    )
    builder.row(
        InlineKeyboardButton(text="🔔 Уведомления", callback_data="settings:notifications")
    )

    if is_coach:
        builder.row(
            InlineKeyboardButton(text="✅ Режим тренера", callback_data="settings:coach_mode")
        )
    else:
        builder.row(
            InlineKeyboardButton(text="❌ Режим тренера", callback_data="settings:coach_mode")
        )

    builder.row(
        InlineKeyboardButton(text="👨‍🏫 Мой тренер", callback_data="student:my_coach")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_menu")
    )

    return builder.as_markup()


def get_profile_settings_keyboard() -> InlineKeyboardMarkup:
    """Меню настроек профиля"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="✏️ Имя", callback_data="settings:profile:name")
    )
    builder.row(
        InlineKeyboardButton(text="🎂 Дата рождения", callback_data="settings:profile:birth_date")
    )
    builder.row(
        InlineKeyboardButton(text="⚧️ Пол", callback_data="settings:profile:gender")
    )
    builder.row(
        InlineKeyboardButton(text="⚖️ Вес", callback_data="settings:profile:weight")
    )
    builder.row(
        InlineKeyboardButton(text="📏 Рост", callback_data="settings:profile:height")
    )
    builder.row(
        InlineKeyboardButton(text="🏃 Основные типы тренировок", callback_data="settings:profile:main_types")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="settings:menu")
    )
    
    return builder.as_markup()


def get_pulse_zones_menu_keyboard() -> InlineKeyboardMarkup:
    """Меню настроек пульсовых зон"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="✏️ Ручной ввод", callback_data="settings:pulse:manual")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="settings:menu")
    )

    return builder.as_markup()


def get_goals_settings_keyboard() -> InlineKeyboardMarkup:
    """Меню настройки целей"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="📊 Недельный объем", callback_data="settings:goals:volume")
    )

    builder.row(
        InlineKeyboardButton(text="🔢 Количество тренировок", callback_data="settings:goals:count")
    )

    builder.row(
        InlineKeyboardButton(text="🏃 Цели по типам", callback_data="settings:goals:by_type")
    )

    builder.row(
        InlineKeyboardButton(text="⚖️ Целевой вес", callback_data="settings:goals:weight")
    )

    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="settings:menu")
    )

    return builder.as_markup()


def get_units_settings_keyboard() -> InlineKeyboardMarkup:
    """Меню настройки единиц измерения"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📏 Дистанция", callback_data="settings:units:distance")
    )
    builder.row(
        InlineKeyboardButton(text="⚖️ Вес", callback_data="settings:units:weight")
    )
    builder.row(
        InlineKeyboardButton(text="📅 Формат даты", callback_data="settings:units:date")
    )
    builder.row(
        InlineKeyboardButton(text="🌍 Часовой пояс", callback_data="settings:units:timezone")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="settings:menu")
    )

    return builder.as_markup()


def get_notifications_settings_keyboard() -> InlineKeyboardMarkup:
    """Меню настройки уведомлений"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="⏰ Время ежедневного ввода", callback_data="settings:notif:daily_time")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Недельный отчет", callback_data="settings:notif:weekly_report")
    )
    builder.row(
        InlineKeyboardButton(text="🔔 Напоминания о тренировках", callback_data="settings:notif:training_reminders")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="settings:menu")
    )

    return builder.as_markup()


def get_gender_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора пола"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="👨 Мужской", callback_data="gender:male"),
        InlineKeyboardButton(text="👩 Женский", callback_data="gender:female")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="settings:profile")
    )
    
    return builder.as_markup()


def get_training_types_selection_keyboard(selected_types: list) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора основных типов тренировок
    
    Args:
        selected_types: Список уже выбранных типов
    """
    builder = InlineKeyboardBuilder()
    
    all_types = [
        ("🏃 Кросс", "кросс"),
        ("🏊 Плавание", "плавание"),
        ("🚴 Велотренировка", "велотренировка"),
        ("💪 Силовая", "силовая"),
        ("⚡ Интервальная", "интервальная")
    ]
    
    for name, type_id in all_types:
        text = f"✅ {name}" if type_id in selected_types else name
        builder.row(
            InlineKeyboardButton(
                text=text,
                callback_data=f"toggle_type:{type_id}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="💾 Сохранить", callback_data="save_training_types")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="settings:profile")
    )
    
    return builder.as_markup()


def get_distance_unit_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора единиц дистанции"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📏 Километры (км)", callback_data="distance_unit:км"),
        InlineKeyboardButton(text="📏 Мили (mi)", callback_data="distance_unit:мили")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="settings:units")
    )
    
    return builder.as_markup()


def get_weight_unit_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора единиц веса"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="⚖️ Килограммы (кг)", callback_data="weight_unit:кг"),
        InlineKeyboardButton(text="⚖️ Фунты (lb)", callback_data="weight_unit:фунты")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="settings:units")
    )
    
    return builder.as_markup()


def get_date_format_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора формата даты"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📅 ДД.ММ.ГГГГ", callback_data="date_format:ДД.ММ.ГГГГ")
    )
    builder.row(
        InlineKeyboardButton(text="📅 ММ/ДД/ГГГГ", callback_data="date_format:ММ/ДД/ГГГГ")
    )
    builder.row(
        InlineKeyboardButton(text="📅 ГГГГ-ММ-ДД", callback_data="date_format:ГГГГ-ММ-ДД")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="settings:units")
    )
    
    return builder.as_markup()


def get_weekday_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора дня недели"""
    builder = InlineKeyboardBuilder()
    
    weekdays = [
        "Понедельник", "Вторник", "Среда", "Четверг",
        "Пятница", "Суббота", "Воскресенье"
    ]
    
    for day in weekdays:
        builder.row(
            InlineKeyboardButton(text=day, callback_data=f"weekday:{day}")
        )
    
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="settings:notifications")
    )
    
    return builder.as_markup()


def get_training_type_goals_keyboard(main_types: list = None, type_goals: dict = None, distance_unit: str = 'км') -> InlineKeyboardMarkup:
    """
    Клавиатура для настройки целей по типам тренировок

    Args:
        main_types: Список основных типов тренировок пользователя
        type_goals: Словарь с установленными целями {тип: значение}
        distance_unit: Единица измерения дистанции
    """
    builder = InlineKeyboardBuilder()

    type_goals = type_goals or {}
    main_types = main_types or []

    type_emoji = {
        'кросс': '🏃',
        'плавание': '🏊',
        'велотренировка': '🚴',
        'силовая': '💪',
        'интервальная': '⚡'
    }

    for t_type in main_types:
        emoji = type_emoji.get(t_type, '🏃')

        if t_type == 'силовая':
            goal_text = f" ({type_goals[t_type]:.0f} мин)" if t_type in type_goals else ""
        else:
            goal_text = f" ({type_goals[t_type]} {distance_unit})" if t_type in type_goals else ""

        builder.row(
            InlineKeyboardButton(text=f"{emoji} {t_type.capitalize()}{goal_text}", callback_data=f"type_goal:{t_type}")
        )

    builder.row(
        InlineKeyboardButton(text="💾 Готово", callback_data="settings:goals")
    )

    return builder.as_markup()


def get_simple_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Простая клавиатура с кнопкой отмены"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="❌ Отмена"))
    return builder.as_markup(resize_keyboard=True)


def get_cancel_delete_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопками отмены и удаления цели"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="❌ Отмена"),
        KeyboardButton(text="🗑 Удалить цель")
    )
    return builder.as_markup(resize_keyboard=True)


def get_timezone_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора часового пояса"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="🌍 Калининград (UTC+2)", callback_data="timezone:Europe/Kaliningrad")
    )
    builder.row(
        InlineKeyboardButton(text="🌍 Москва (UTC+3)", callback_data="timezone:Europe/Moscow")
    )
    builder.row(
        InlineKeyboardButton(text="🌍 Самара (UTC+4)", callback_data="timezone:Europe/Samara")
    )
    builder.row(
        InlineKeyboardButton(text="🌍 Екатеринбург (UTC+5)", callback_data="timezone:Asia/Yekaterinburg")
    )
    builder.row(
        InlineKeyboardButton(text="🌍 Омск (UTC+6)", callback_data="timezone:Asia/Omsk")
    )
    builder.row(
        InlineKeyboardButton(text="🌍 Красноярск (UTC+7)", callback_data="timezone:Asia/Krasnoyarsk")
    )
    builder.row(
        InlineKeyboardButton(text="🌍 Иркутск (UTC+8)", callback_data="timezone:Asia/Irkutsk")
    )
    builder.row(
        InlineKeyboardButton(text="🌍 Якутск (UTC+9)", callback_data="timezone:Asia/Yakutsk")
    )
    builder.row(
        InlineKeyboardButton(text="🌍 Владивосток (UTC+10)", callback_data="timezone:Asia/Vladivostok")
    )
    builder.row(
        InlineKeyboardButton(text="🌍 Магадан (UTC+11)", callback_data="timezone:Asia/Magadan")
    )
    builder.row(
        InlineKeyboardButton(text="🌍 Камчатка (UTC+12)", callback_data="timezone:Asia/Kamchatka")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="settings:units")
    )

    return builder.as_markup()


def get_training_reminder_days_keyboard(selected_days: list) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора дней недели для напоминаний о тренировках

    Args:
        selected_days: Список уже выбранных дней
    """
    builder = InlineKeyboardBuilder()

    weekdays = [
        ("Понедельник", "Пн"),
        ("Вторник", "Вт"),
        ("Среда", "Ср"),
        ("Четверг", "Чт"),
        ("Пятница", "Пт"),
        ("Суббота", "Сб"),
        ("Воскресенье", "Вс")
    ]

    for day_full, day_short in weekdays:
        text = f"✅ {day_short}" if day_full in selected_days else day_short
        builder.button(
            text=text,
            callback_data=f"toggle_reminder_day:{day_full}"
        )

    builder.adjust(4, 3)

    builder.row(
        InlineKeyboardButton(text="💾 Сохранить", callback_data="save_reminder_days")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="settings:notif:training_reminders")
    )

    return builder.as_markup()


def get_training_reminder_toggle_keyboard(is_enabled: bool) -> InlineKeyboardMarkup:
    """
    Клавиатура управления напоминаниями о тренировках

    Args:
        is_enabled: Включены ли напоминания
    """
    builder = InlineKeyboardBuilder()

    if is_enabled:
        builder.row(
            InlineKeyboardButton(text="🔕 Выключить напоминания", callback_data="toggle_training_reminders:off")
        )
        builder.row(
            InlineKeyboardButton(text="📅 Выбрать дни", callback_data="select_reminder_days")
        )
        builder.row(
            InlineKeyboardButton(text="⏰ Изменить время", callback_data="change_reminder_time")
        )
    else:
        builder.row(
            InlineKeyboardButton(text="🔔 Включить напоминания", callback_data="toggle_training_reminders:on")
        )

    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="settings:notifications")
    )

    return builder.as_markup()
