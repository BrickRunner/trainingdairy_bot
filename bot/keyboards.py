"""
Клавиатуры и кнопки для интерфейса бота
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from database.queries import format_date_by_setting  # Добавил импорт


def get_main_menu_keyboard(is_coach: bool = False) -> ReplyKeyboardMarkup:
    """
    Главное меню бота

    Args:
        is_coach: Является ли пользователь тренером
    """
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="➕ Добавить тренировку"),
        KeyboardButton(text="📊 Мои тренировки")
    )
    builder.row(
        KeyboardButton(text="🏃 Соревнования"),
        KeyboardButton(text="🏆 Достижения")
    )

    # Кнопка "Тренер" показывается только если is_coach=True
    if is_coach:
        builder.row(
            KeyboardButton(text="👨‍🏫 Тренер"),
            KeyboardButton(text="❤️ Здоровье")
        )
    else:
        builder.row(
            KeyboardButton(text="❤️ Здоровье"),
            KeyboardButton(text="⚙️ Настройки")
        )

    # Настройки всегда видны, но в разных позициях
    if is_coach:
        builder.row(
            KeyboardButton(text="⚙️ Настройки"),
            KeyboardButton(text="📥 Экспорт в PDF")
        )
        builder.row(
            KeyboardButton(text="ℹ️ Помощь")
        )
    else:
        builder.row(
            KeyboardButton(text="📥 Экспорт в PDF"),
            KeyboardButton(text="ℹ️ Помощь")
        )

    return builder.as_markup(resize_keyboard=True)


def get_training_types_keyboard(allowed_types: list = None) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора типа тренировки

    Args:
        allowed_types: Список разрешенных типов тренировок.
                      Если None, показываются все типы.
    """
    # Все доступные типы с эмодзи
    all_types = {
        'интервальная': '⚡ Интервальная',
        'силовая': '💪 Силовая',
        'кросс': '🏃 Кросс',
        'плавание': '🏊 Плавание',
        'велотренировка': '🚴 Велотренировка'
    }

    # Если allowed_types не указан, используем все типы
    if allowed_types is None:
        allowed_types = list(all_types.keys())

    builder = InlineKeyboardBuilder()

    # Добавляем только разрешенные типы
    for type_key in all_types.keys():
        if type_key in allowed_types:
            builder.row(
                InlineKeyboardButton(
                    text=all_types[type_key],
                    callback_data=f"training_type:{type_key}"
                )
            )

    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )
    return builder.as_markup()


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой отмены"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="❌ Отменить"))
    return builder.as_markup(resize_keyboard=True)


def get_skip_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопками пропуска и отмены"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="⏭️ Пропустить"),
        KeyboardButton(text="❌ Отменить")
    )
    return builder.as_markup(resize_keyboard=True)


def get_fatigue_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора уровня усилий"""
    builder = InlineKeyboardBuilder()
    for i in range(1, 11):
        builder.button(text=str(i), callback_data=f"fatigue:{i}")
    builder.adjust(5)  # 5 кнопок в ряду
    # Добавляем кнопку отмены в отдельном ряду
    builder.row(InlineKeyboardButton(text="❌ Отменить", callback_data="cancel"))
    return builder.as_markup()


def get_period_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора периода для просмотра тренировок"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📅 Неделя", callback_data="period:week")
    )
    builder.row(
        InlineKeyboardButton(text="📅 2 недели", callback_data="period:2weeks")
    )
    builder.row(
        InlineKeyboardButton(text="📅 Месяц", callback_data="period:month")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")
    )
    return builder.as_markup()


def get_date_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора даты тренировки"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📅 Сегодня"),
        KeyboardButton(text="📅 Вчера")
    )
    builder.row(
        KeyboardButton(text="📝 Ввести дату"),
        KeyboardButton(text="❌ Отменить")
    )
    return builder.as_markup(resize_keyboard=True)


def get_trainings_list_keyboard(trainings: list, period: str, date_format: str) -> InlineKeyboardMarkup:  # Добавил date_format параметр
    """
    Клавиатура со списком тренировок (кнопки для каждой)
    
    Args:
        trainings: Список тренировок из БД
        period: Текущий период просмотра
        date_format: Формат даты из настроек пользователя
        
    Returns:
        InlineKeyboardMarkup с кнопками для каждой тренировки
    """
    builder = InlineKeyboardBuilder()
    
    # Добавляем кнопку для каждой тренировки (максимум 15)
    for idx, training in enumerate(trainings[:15], 1):
        # Эмодзи для типов
        type_emoji = {
            'кросс': '🏃',
            'плавание': '🏊',
            'велотренировка': '🚴',
            'силовая': '💪',
            'интервальная': '⚡'
        }
        
        t_type = training['type']
        emoji = type_emoji.get(t_type, '📝')
        
        # Форматируем дату согласно настройкам (короткий формат: без года)
        formatted_date = format_date_by_setting(training['date'], date_format)
        # Для короткого отображения берем только день.месяц или эквивалент
        if date_format == 'DD.MM.YYYY':
            short_date = formatted_date[:5]  # ДД.ММ
        elif date_format == 'MM/DD/YYYY':
            short_date = formatted_date[:5]  # ММ/ДД
        else:
            short_date = formatted_date[-5:]  # ММ-ДД (от末尾)
        
        # Текст кнопки: "№1 🏃 15.01"
        button_text = f"№{idx} {emoji} {short_date}"
        
        # В callback_data передаем ID тренировки и период
        builder.button(
            text=button_text,
            callback_data=f"training_detail:{training['id']}:{period}"
        )
    
    # Размещаем по 3 кнопки в ряду
    builder.adjust(3)
    
    # Добавляем кнопки навигации в отдельных рядах
    builder.row(
        InlineKeyboardButton(text="🔄 Выбрать другой период", callback_data="back_to_periods")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_menu")
    )
    
    return builder.as_markup()


def get_training_detail_keyboard(period: str, training_id: int = None):
    """
    Создаёт клавиатуру для детальной информации о тренировке.
    
    Args:
        period (str): Период тренировок (week, 2weeks, month).
        training_id (int, optional): ID тренировки для кнопки удаления.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками.
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 К списку", callback_data=f"back_to_list:{period}"),
        InlineKeyboardButton(text="🗑 Удалить тренировку", callback_data=f"delete_training:{training_id}:{period}")
    )
    builder.row(InlineKeyboardButton(text="🏠 В меню", callback_data="back_to_menu"))
    return builder.as_markup()


def get_export_type_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа экспорта в PDF"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📊 Экспорт тренировок", callback_data="export_type:trainings")
    )
    builder.row(
        InlineKeyboardButton(text="❤️ Экспорт данных здоровья", callback_data="export_type:health")
    )
    builder.row(
        InlineKeyboardButton(text="🏃 Экспорт соревнований", callback_data="export_type:competitions")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")
    )
    return builder.as_markup()


def get_export_period_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора периода для экспорта в PDF"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📅 Полгода", callback_data="export_period:6months")
    )
    builder.row(
        InlineKeyboardButton(text="📅 Год", callback_data="export_period:year")
    )
    builder.row(
        InlineKeyboardButton(text="📅 Произвольный период", callback_data="export_period:custom")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_export_menu")
    )
    return builder.as_markup()


# ===== КЛАВИАТУРЫ ДЛЯ ПЛАВАНИЯ =====

def get_swimming_location_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора места для плавания"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🏊 Бассейн", callback_data="swimming_location:pool")
    )
    builder.row(
        InlineKeyboardButton(text="🌊 Открытая вода", callback_data="swimming_location:open_water")
    )
    return builder.as_markup()


def get_pool_length_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора длины бассейна"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="25 м", callback_data="pool_length:25"),
        InlineKeyboardButton(text="50 м", callback_data="pool_length:50")
    )
    return builder.as_markup()


def get_swimming_styles_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора стилей плавания (множественный выбор)"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="☐ Вольный стиль", callback_data="swimming_style:freestyle")
    )
    builder.row(
        InlineKeyboardButton(text="☐ Брасс", callback_data="swimming_style:breaststroke")
    )
    builder.row(
        InlineKeyboardButton(text="☐ Баттерфляй", callback_data="swimming_style:butterfly")
    )
    builder.row(
        InlineKeyboardButton(text="☐ На спине", callback_data="swimming_style:backstroke")
    )
    builder.row(
        InlineKeyboardButton(text="☐ Комплекс (IM)", callback_data="swimming_style:im")
    )
    builder.row(
        InlineKeyboardButton(text="✅ Готово", callback_data="swimming_styles:done")
    )
    return builder.as_markup()


def update_swimming_styles_keyboard(selected_styles: list) -> InlineKeyboardMarkup:
    """
    Обновляет клавиатуру стилей плавания с отметками выбранных

    Args:
        selected_styles: Список выбранных стилей
    """
    styles = {
        'freestyle': 'Вольный стиль',
        'breaststroke': 'Брасс',
        'butterfly': 'Баттерфляй',
        'backstroke': 'На спине',
        'im': 'Комплекс (IM)'
    }

    builder = InlineKeyboardBuilder()

    for style_key, style_name in styles.items():
        checkbox = "☑" if style_key in selected_styles else "☐"
        builder.row(
            InlineKeyboardButton(
                text=f"{checkbox} {style_name}",
                callback_data=f"swimming_style:{style_key}"
            )
        )

    builder.row(
        InlineKeyboardButton(text="✅ Готово", callback_data="swimming_styles:done")
    )

    return builder.as_markup()