"""
Клавиатуры для работы с тренерским разделом
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_coach_main_menu() -> InlineKeyboardMarkup:
    """Главное меню тренера"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="👥 Мои ученики", callback_data="coach:students")
    )
    builder.row(
        InlineKeyboardButton(text="🔗 Ссылка для учеников", callback_data="coach:link")
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="back_to_main")
    )

    return builder.as_markup()


def get_students_list_keyboard(students: list) -> InlineKeyboardMarkup:
    """Клавиатура со списком учеников"""
    builder = InlineKeyboardBuilder()

    for student in students:
        builder.row(
            InlineKeyboardButton(
                text=f"👤 {student['name']}",
                callback_data=f"coach:student:{student['id']}"
            )
        )

    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="coach:menu")
    )

    return builder.as_markup()


def get_student_detail_keyboard(student_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для просмотра конкретного ученика"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="➕ Назначить тренировку",
            callback_data=f"coach:add_training:{student_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🏆 Соревнования",
            callback_data=f"coach:competitions_menu:{student_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📊 Статистика",
            callback_data=f"coach:student_trainings:{student_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="💪 Здоровье",
            callback_data=f"coach:student_health:{student_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="✏️ Изменить псевдоним",
            callback_data=f"coach:edit_nickname:{student_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🗑 Удалить ученика",
            callback_data=f"coach:remove_student:{student_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(text="« К списку", callback_data="coach:students")
    )

    return builder.as_markup()


def get_confirm_remove_student_keyboard(student_id: int) -> InlineKeyboardMarkup:
    """Подтверждение удаления ученика"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="✅ Да, удалить",
            callback_data=f"coach:confirm_remove:{student_id}"
        ),
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=f"coach:student:{student_id}"
        )
    )

    return builder.as_markup()


def get_add_coach_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для добавления тренера (со стороны ученика)"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="✏️ Ввести код тренера",
            callback_data="student:add_coach"
        )
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="settings:menu")
    )

    return builder.as_markup()


def get_student_coach_info_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с информацией о тренере (со стороны ученика)"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="🗑 Отключиться от тренера",
            callback_data="student:remove_coach"
        )
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="settings:menu")
    )

    return builder.as_markup()


def get_confirm_remove_coach_keyboard() -> InlineKeyboardMarkup:
    """Подтверждение отключения от тренера"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="✅ Да, отключиться",
            callback_data="student:confirm_remove_coach"
        ),
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="student:my_coach"
        )
    )

    return builder.as_markup()


def get_student_trainings_keyboard(student_id: int, trainings: list, period: str = None, date_format: str = 'ДД.ММ.ГГГГ') -> InlineKeyboardMarkup:
    """Клавиатура со списком тренировок ученика"""
    from utils.date_formatter import DateFormatter

    builder = InlineKeyboardBuilder()

    type_emoji = {
        'кросс': '🏃',
        'плавание': '🏊',
        'велотренировка': '🚴',
        'силовая': '💪',
        'интервальная': '⚡'
    }

    for training in trainings[:15]:  # Максимум 15 тренировок
        emoji = type_emoji.get(training['type'], '📝')

        # Форматируем дату согласно настройкам тренера (короткий формат: без года)
        formatted_date = DateFormatter.format_date(training['date'], date_format)
        # Для короткого отображения берем только день и месяц
        if date_format == 'ДД.ММ.ГГГГ':
            date_str = formatted_date[:5]  # ДД.ММ
        elif date_format == 'ММ/ДД/ГГГГ':
            date_str = formatted_date[:5]  # ММ/ДД
        else:  # ГГГГ-ММ-ДД
            date_str = formatted_date[5:]  # ММ-ДД

        # Отметка если добавлено тренером
        added_mark = " 👨‍🏫" if training.get('added_by_coach_id') else ""

        builder.row(
            InlineKeyboardButton(
                text=f"{emoji} {date_str}{added_mark}",
                callback_data=f"coach:training_detail:{training['id']}:{student_id}:{period}"
            )
        )

    # Кнопка назад - к выбору периода
    builder.row(
        InlineKeyboardButton(
            text="« К выбору периода",
            callback_data=f"coach:student_trainings:{student_id}"
        )
    )

    return builder.as_markup()


def get_training_detail_keyboard(training_id: int, student_id: int, period: str = None, has_comments: int = 0, coach_has_comment: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура для детальной информации о тренировке"""
    builder = InlineKeyboardBuilder()

    # Показываем кнопку добавления комментария только если тренер еще не комментировал
    if not coach_has_comment:
        # Формируем callback_data с учетом периода
        comment_callback = f"coach:add_comment:{training_id}:{student_id}"
        if period:
            comment_callback += f":{period}"

        builder.row(
            InlineKeyboardButton(
                text="💬 Добавить комментарий",
                callback_data=comment_callback
            )
        )

    # Если period указан, возвращаемся к списку с этим периодом, иначе к меню выбора периода
    if period:
        builder.row(
            InlineKeyboardButton(
                text="« К списку",
                callback_data=f"coach:trainings_period:{student_id}:{period}"
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="« К выбору периода",
                callback_data=f"coach:student_trainings:{student_id}"
            )
        )

    return builder.as_markup()


def get_student_stats_period_keyboard(student_id: int) -> InlineKeyboardMarkup:
    """Клавиатура выбора периода для просмотра статистики ученика"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="📅 Неделя", callback_data=f"coach:stats_period:{student_id}:week")
    )
    builder.row(
        InlineKeyboardButton(text="📅 2 недели", callback_data=f"coach:stats_period:{student_id}:2weeks")
    )
    builder.row(
        InlineKeyboardButton(text="📅 Месяц", callback_data=f"coach:stats_period:{student_id}:month")
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data=f"coach:student:{student_id}")
    )

    return builder.as_markup()


def get_student_trainings_period_keyboard(student_id: int) -> InlineKeyboardMarkup:
    """Клавиатура выбора периода для просмотра тренировок ученика"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="📅 Неделя", callback_data=f"coach:trainings_period:{student_id}:week")
    )
    builder.row(
        InlineKeyboardButton(text="📅 2 недели", callback_data=f"coach:trainings_period:{student_id}:2weeks")
    )
    builder.row(
        InlineKeyboardButton(text="📅 Месяц", callback_data=f"coach:trainings_period:{student_id}:month")
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data=f"coach:student:{student_id}")
    )

    return builder.as_markup()


def get_student_health_period_keyboard(student_id: int) -> InlineKeyboardMarkup:
    """Клавиатура выбора периода для просмотра здоровья ученика"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="📅 Неделя", callback_data=f"coach:health_period:{student_id}:week")
    )
    builder.row(
        InlineKeyboardButton(text="📅 Две недели", callback_data=f"coach:health_period:{student_id}:2weeks")
    )
    builder.row(
        InlineKeyboardButton(text="📅 Месяц", callback_data=f"coach:health_period:{student_id}:month")
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data=f"coach:student:{student_id}")
    )

    return builder.as_markup()
