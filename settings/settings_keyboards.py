"""
Клавиатуры для раздела настроек
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def get_settings_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню настроек"""
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
        InlineKeyboardButton(text="🔄 Автоматический расчет", callback_data="settings:pulse:auto")
    )
    builder.row(
        InlineKeyboardButton(text="✏️ Ручной ввод", callback_data="settings:pulse:manual")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Показать текущие зоны", callback_data="settings:pulse:show")
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
        # Добавляем галочку если тип уже выбран
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
        InlineKeyboardButton(text="📅 ДД.ММ.ГГГГ", callback_data="date_format:DD.MM.YYYY")
    )
    builder.row(
        InlineKeyboardButton(text="📅 ММ/ДД/ГГГГ", callback_data="date_format:MM/DD/YYYY")
    )
    builder.row(
        InlineKeyboardButton(text="📅 ГГГГ-ММ-ДД", callback_data="date_format:YYYY-MM-DD")
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
        InlineKeyboardButton(text="◀️ Назад", callback_data="settings:notif:weekly_report")
    )
    
    return builder.as_markup()


def get_training_type_goals_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для настройки целей по типам тренировок"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🏃 Кросс", callback_data="type_goal:кросс")
    )
    builder.row(
        InlineKeyboardButton(text="🏊 Плавание", callback_data="type_goal:плавание")
    )
    builder.row(
        InlineKeyboardButton(text="🚴 Велотренировка", callback_data="type_goal:велотренировка")
    )
    builder.row(
        InlineKeyboardButton(text="💪 Силовая", callback_data="type_goal:силовая")
    )
    builder.row(
        InlineKeyboardButton(text="⚡ Интервальная", callback_data="type_goal:интервальная")
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
