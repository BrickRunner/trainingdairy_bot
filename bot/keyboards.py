"""
Клавиатуры и кнопки для интерфейса бота
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню бота"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="➕ Добавить тренировку"),
        KeyboardButton(text="📊 Мои тренировки")
    )
    builder.row(
        KeyboardButton(text="📈 Графики"),
        KeyboardButton(text="🏆 Достижения")
    )
    builder.row(
        KeyboardButton(text="⚙️ Настройки"),
        KeyboardButton(text="ℹ️ Помощь")
    )
    return builder.as_markup(resize_keyboard=True)


def get_training_types_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа тренировки"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🏃 Кросс", callback_data="training_type:кросс")
    )
    builder.row(
        InlineKeyboardButton(text="🏊 Плавание", callback_data="training_type:плавание")
    )
    builder.row(
        InlineKeyboardButton(text="🚴 Велотренировка", callback_data="training_type:велотренировка")
    )
    builder.row(
        InlineKeyboardButton(text="💪 Силовая", callback_data="training_type:силовая")
    )
    builder.row(
        InlineKeyboardButton(text="⚡ Интервальная", callback_data="training_type:интервальная")
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
    """Клавиатура для выбора уровня усталости"""
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


def get_trainings_list_keyboard(trainings: list, period: str) -> InlineKeyboardMarkup:
    """
    Клавиатура со списком тренировок (кнопки для каждой)
    
    Args:
        trainings: Список тренировок из БД
        period: Текущий период просмотра
        
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
        
        # Парсим дату для короткого отображения
        from datetime import datetime
        date = datetime.strptime(training['date'], '%Y-%m-%d').strftime('%d.%m')
        
        # Текст кнопки: "№1 🏃 15.01"
        button_text = f"№{idx} {emoji} {date}"
        
        # В callback_data передаем ID тренировки и период
        builder.button(
            text=button_text,
            callback_data=f"training_detail:{training['id']}:{period}"
        )
    
    # Размещаем по 3 кнопки в ряду
    builder.adjust(3)
    
    # Добавляем кнопку "Назад" в отдельном ряду
    builder.row(
        InlineKeyboardButton(text="🔙 Вернуться к периодам", callback_data="back_to_periods")
    )
    
    return builder.as_markup()