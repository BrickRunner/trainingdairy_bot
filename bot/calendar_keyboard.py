"""
Модуль для создания inline-календаря в Telegram боте
Поддерживает 4 формата отображения:
1 - Выбор даты (дни месяца)
2 - Выбор месяца
3 - Выбор года
4 - Выбор десятилетия
"""

from datetime import datetime, timedelta
from calendar import monthrange
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional


class CalendarKeyboard:
    """Класс для создания календарной клавиатуры"""

    # Названия месяцев (краткие)
    MONTH_NAMES = [
        "Янв", "Фев", "Мар", "Апр", "Май", "Июнь",
        "Июль", "Авг", "Сен", "Окт", "Ноя", "Дек"
    ]

    # Названия дней недели
    WEEKDAY_NAMES = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

    @staticmethod
    def create_calendar(
        calendar_format: int = 1,
        current_date: Optional[datetime] = None,
        callback_prefix: str = "cal"
    ) -> InlineKeyboardMarkup:
        """
        Создает календарь в нужном формате

        :param calendar_format: 1=дни, 2=месяцы, 3=годы, 4=десятилетия
        :param current_date: текущая дата для отображения
        :param callback_prefix: префикс для callback_data
        :return: InlineKeyboardMarkup
        """
        if current_date is None:
            current_date = datetime.now()

        if calendar_format == 1:
            return CalendarKeyboard._create_days_calendar(current_date, callback_prefix)
        elif calendar_format == 2:
            return CalendarKeyboard._create_months_calendar(current_date, callback_prefix)
        elif calendar_format == 3:
            return CalendarKeyboard._create_years_calendar(current_date, callback_prefix)
        elif calendar_format == 4:
            return CalendarKeyboard._create_decades_calendar(current_date, callback_prefix)
        else:
            raise ValueError(f"Неверный формат календаря: {calendar_format}")

    @staticmethod
    def _create_days_calendar(date: datetime, prefix: str) -> InlineKeyboardMarkup:
        """Создает календарь с днями месяца"""
        keyboard = []

        # Первая строка: навигация и заголовок
        year = date.year
        month = date.month
        month_name = CalendarKeyboard.MONTH_NAMES[month - 1]

        first_row = [
            InlineKeyboardButton(
                text="<",
                callback_data=f"{prefix}_1_less_{year}_{month:02d}_01"
            ),
            InlineKeyboardButton(
                text=f"{month_name} {year}",
                callback_data=f"{prefix}_1_change_{year}_{month:02d}_01"
            ),
            InlineKeyboardButton(
                text=">",
                callback_data=f"{prefix}_1_more_{year}_{month:02d}_01"
            )
        ]
        keyboard.append(first_row)

        # Вторая строка: дни недели
        weekday_row = [
            InlineKeyboardButton(text=day, callback_data=f"{prefix}_empty")
            for day in CalendarKeyboard.WEEKDAY_NAMES
        ]
        keyboard.append(weekday_row)

        # Получаем первый день месяца и количество дней
        first_day = datetime(year, month, 1)
        weekday = first_day.weekday()  # 0=понедельник
        days_in_month = monthrange(year, month)[1]

        # Строки с днями
        current_row = []

        # Пустые кнопки до первого дня месяца
        for _ in range(weekday):
            current_row.append(
                InlineKeyboardButton(text=" ", callback_data=f"{prefix}_empty")
            )

        # Дни месяца
        today = datetime.now().date()
        for day in range(1, days_in_month + 1):
            day_date = datetime(year, month, day)

            # Если это сегодня, показываем иконку ☀
            if day_date.date() == today:
                text = "☀"
            else:
                text = str(day)

            current_row.append(
                InlineKeyboardButton(
                    text=text,
                    callback_data=f"{prefix}_1_select_{year}_{month:02d}_{day:02d}"
                )
            )

            # Если заполнена неделя, добавляем строку
            if len(current_row) == 7:
                keyboard.append(current_row)
                current_row = []

        # Заполняем оставшиеся пустые кнопки
        while len(current_row) < 7 and len(current_row) > 0:
            current_row.append(
                InlineKeyboardButton(text=" ", callback_data=f"{prefix}_empty")
            )

        if current_row:
            keyboard.append(current_row)

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def _create_months_calendar(date: datetime, prefix: str) -> InlineKeyboardMarkup:
        """Создает календарь с выбором месяца"""
        keyboard = []
        year = date.year

        # Первая строка: навигация и заголовок
        first_row = [
            InlineKeyboardButton(
                text="<",
                callback_data=f"{prefix}_2_less_{year}_01_01"
            ),
            InlineKeyboardButton(
                text=str(year),
                callback_data=f"{prefix}_2_change_{year}_01_01"
            ),
            InlineKeyboardButton(
                text=">",
                callback_data=f"{prefix}_2_more_{year}_01_01"
            )
        ]
        keyboard.append(first_row)

        # Строки с месяцами (по 4 месяца в строке)
        for i in range(0, 12, 4):
            month_row = []
            for j in range(4):
                month_num = i + j + 1
                month_row.append(
                    InlineKeyboardButton(
                        text=CalendarKeyboard.MONTH_NAMES[month_num - 1],
                        callback_data=f"{prefix}_2_select_{year}_{month_num:02d}_01"
                    )
                )
            keyboard.append(month_row)

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def _create_years_calendar(date: datetime, prefix: str) -> InlineKeyboardMarkup:
        """Создает календарь с выбором года"""
        keyboard = []
        year = date.year

        # Определяем начало десятилетия
        decade_start = (year // 10) * 10 - 1
        if decade_start < 1:
            decade_start = 1

        decade_end = decade_start + 11
        if decade_end > 3999:
            decade_end = 3999

        # Первая строка: навигация и заголовок
        first_row = [
            InlineKeyboardButton(
                text="<",
                callback_data=f"{prefix}_3_less_{decade_start}_01_01"
            ),
            InlineKeyboardButton(
                text=f"{decade_start}-{str(decade_end)[-2:]}",
                callback_data=f"{prefix}_3_change_{decade_start}_01_01"
            ),
            InlineKeyboardButton(
                text=">",
                callback_data=f"{prefix}_3_more_{decade_start}_01_01"
            )
        ]
        keyboard.append(first_row)

        # Строки с годами (по 4 года в строке)
        current_row = []
        for y in range(decade_start, decade_end + 1):
            current_row.append(
                InlineKeyboardButton(
                    text=str(y),
                    callback_data=f"{prefix}_3_select_{y}_01_01"
                )
            )

            if len(current_row) == 4:
                keyboard.append(current_row)
                current_row = []

        if current_row:
            keyboard.append(current_row)

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def _create_decades_calendar(date: datetime, prefix: str) -> InlineKeyboardMarkup:
        """Создает календарь с выбором десятилетия"""
        keyboard = []
        year = date.year

        # Определяем начало века
        century_start = (year // 100) * 100 - 10
        if century_start < 1:
            century_start = 1

        century_end = century_start + 110
        if century_end > 3999:
            century_end = 3999

        # Первая строка: навигация и заголовок
        first_row = [
            InlineKeyboardButton(
                text="<",
                callback_data=f"{prefix}_4_less_{century_start}_01_01"
            ),
            InlineKeyboardButton(
                text=f"{century_start}-{str(century_end)[-2:]}",
                callback_data=f"{prefix}_4_change_{century_start}_01_01"
            ),
            InlineKeyboardButton(
                text=">",
                callback_data=f"{prefix}_4_more_{century_start}_01_01"
            )
        ]
        keyboard.append(first_row)

        # Строки с десятилетиями (по 4 в строке)
        current_row = []
        decade = century_start
        while decade <= century_end:
            decade_end_year = decade + 9
            if decade_end_year > 3999:
                decade_end_year = 3999

            current_row.append(
                InlineKeyboardButton(
                    text=f"{decade}-{str(decade_end_year)[-2:]}",
                    callback_data=f"{prefix}_4_select_{decade}_01_01"
                )
            )

            if len(current_row) == 4:
                keyboard.append(current_row)
                current_row = []

            decade += 10

        if current_row:
            keyboard.append(current_row)

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def parse_callback_data(callback_data: str) -> dict:
        """
        Парсит callback_data и возвращает словарь с информацией

        Формат: prefix_format_action_year_month_day

        :param callback_data: строка callback_data
        :return: словарь с ключами: prefix, format, action, date
        """
        parts = callback_data.split("_")

        if len(parts) < 2:
            return {}

        result = {
            "prefix": parts[0],
            "format": int(parts[1]) if parts[1].isdigit() else None,
            "action": parts[2] if len(parts) > 2 else None,
        }

        # Парсим дату если есть
        if len(parts) >= 6:
            try:
                year = int(parts[3])
                month = int(parts[4])
                day = int(parts[5])
                result["date"] = datetime(year, month, day)
            except (ValueError, IndexError):
                result["date"] = None

        return result

    @staticmethod
    def handle_navigation(callback_data: str, prefix: str = "cal") -> Optional[InlineKeyboardMarkup]:
        """
        Обрабатывает навигацию по календарю

        :param callback_data: данные callback
        :param prefix: префикс callback
        :return: новая клавиатура или None
        """
        if callback_data == f"{prefix}_empty":
            return None

        parsed = CalendarKeyboard.parse_callback_data(callback_data)

        if not parsed or parsed["prefix"] != prefix:
            return None

        current_format = parsed["format"]
        action = parsed["action"]
        date = parsed["date"]

        if not date:
            return None

        # Смена формата (увеличение масштаба)
        if action == "change":
            new_format = current_format + 1 if current_format < 4 else 1
            return CalendarKeyboard.create_calendar(new_format, date, prefix)

        # Навигация влево
        elif action == "less":
            if current_format == 1:
                new_date = date - timedelta(days=monthrange(date.year, date.month)[1])
            elif current_format == 2:
                new_date = datetime(date.year - 1, 1, 1)
            elif current_format == 3:
                year = (date.year // 10) * 10 - 11
                new_date = datetime(max(1, year), 1, 1)
            elif current_format == 4:
                year = (date.year // 100) * 100 - 110
                new_date = datetime(max(1, year), 1, 1)
            else:
                return None

            return CalendarKeyboard.create_calendar(current_format, new_date, prefix)

        # Навигация вправо
        elif action == "more":
            if current_format == 1:
                # Следующий месяц
                if date.month == 12:
                    new_date = datetime(date.year + 1, 1, 1)
                else:
                    new_date = datetime(date.year, date.month + 1, 1)
            elif current_format == 2:
                new_date = datetime(min(3999, date.year + 1), 1, 1)
            elif current_format == 3:
                year = (date.year // 10) * 10 + 10
                new_date = datetime(min(3999, year), 1, 1)
            elif current_format == 4:
                year = (date.year // 100) * 100 + 110
                new_date = datetime(min(3999, year), 1, 1)
            else:
                return None

            return CalendarKeyboard.create_calendar(current_format, new_date, prefix)

        # Выбор элемента (не финальная дата)
        elif action == "select" and current_format > 1:
            # Уменьшаем формат (детализируем)
            return CalendarKeyboard.create_calendar(current_format - 1, date, prefix)

        return None
