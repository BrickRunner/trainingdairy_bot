"""
Утилита для централизованного форматирования дат согласно настройкам пользователя
"""

from datetime import datetime, date
from typing import Optional, Union


class DateFormatter:
    """Класс для форматирования и парсинга дат согласно настройкам пользователя"""
    
    # Маппинг форматов настроек на Python strftime форматы
    FORMAT_MAPPING = {
        'ДД.ММ.ГГГГ': '%d.%m.%Y',
        'ММ/ДД/ГГГГ': '%m/%d/%Y',
        'ГГГГ-ММ-ДД': '%Y-%m-%d'
    }

    # Паттерны для валидации ввода
    VALIDATION_PATTERNS = {
        'ДД.ММ.ГГГГ': r'^\d{2}\.\d{2}\.\d{4}$',
        'ММ/ДД/ГГГГ': r'^\d{2}/\d{2}/\d{4}$',
        'ГГГГ-ММ-ДД': r'^\d{4}-\d{2}-\d{2}$'
    }

    # Описания форматов для пользователя
    FORMAT_DESCRIPTIONS = {
        'ДД.ММ.ГГГГ': 'ДД.ММ.ГГГГ (например, 15.01.2024)',
        'ММ/ДД/ГГГГ': 'ММ/ДД/ГГГГ (например, 01/15/2024)',
        'ГГГГ-ММ-ДД': 'ГГГГ-ММ-ДД (например, 2024-01-15)'
    }
    
    @staticmethod
    def format_date(
        date_obj: Union[date, datetime, str],
        user_format: str = 'ДД.ММ.ГГГГ'
    ) -> str:
        """
        Форматировать дату согласно настройкам пользователя
        
        Args:
            date_obj: Объект даты или строка в формате YYYY-MM-DD
            user_format: Формат из настроек пользователя
            
        Returns:
            Отформатированная строка даты
        """
        # Если это строка, преобразуем в date объект
        if isinstance(date_obj, str):
            try:
                date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
            except ValueError:
                return date_obj  # Возвращаем как есть, если не удалось распарсить
        
        # Если это datetime, берем только date
        if isinstance(date_obj, datetime):
            date_obj = date_obj.date()
        
        # Получаем Python формат из настроек
        python_format = DateFormatter.FORMAT_MAPPING.get(user_format, '%d.%m.%Y')
        
        try:
            return date_obj.strftime(python_format)
        except:
            return str(date_obj)
    
    @staticmethod
    def format_datetime(
        datetime_obj: Union[datetime, str],
        user_format: str = 'ДД.ММ.ГГГГ',
        include_time: bool = True
    ) -> str:
        """
        Форматировать дату и время согласно настройкам пользователя
        
        Args:
            datetime_obj: Объект datetime или строка
            user_format: Формат из настроек пользователя
            include_time: Включать ли время в вывод
            
        Returns:
            Отформатированная строка даты и времени
        """
        if isinstance(datetime_obj, str):
            try:
                datetime_obj = datetime.fromisoformat(datetime_obj)
            except ValueError:
                return datetime_obj
        
        date_str = DateFormatter.format_date(datetime_obj, user_format)
        
        if include_time:
            time_str = datetime_obj.strftime('%H:%M')
            return f"{date_str} {time_str}"
        
        return date_str
    
    @staticmethod
    def parse_date(
        date_str: str,
        user_format: str = 'ДД.ММ.ГГГГ'
    ) -> Optional[date]:
        """
        Распарсить строку даты согласно формату пользователя
        
        Args:
            date_str: Строка с датой
            user_format: Формат из настроек пользователя
            
        Returns:
            Объект date или None, если парсинг не удался
        """
        python_format = DateFormatter.FORMAT_MAPPING.get(user_format, '%d.%m.%Y')
        
        try:
            return datetime.strptime(date_str, python_format).date()
        except ValueError:
            return None
    
    @staticmethod
    def get_format_description(user_format: str = 'ДД.ММ.ГГГГ') -> str:
        """
        Получить описание формата для пользователя
        
        Args:
            user_format: Формат из настроек
            
        Returns:
            Строка с описанием формата
        """
        return DateFormatter.FORMAT_DESCRIPTIONS.get(
            user_format,
            'ДД.ММ.ГГГГ (например, 15.01.2024)'
        )
    
    @staticmethod
    def get_validation_pattern(user_format: str = 'ДД.ММ.ГГГГ') -> str:
        """
        Получить регулярное выражение для валидации формата
        
        Args:
            user_format: Формат из настроек
            
        Returns:
            Строка с регулярным выражением
        """
        return DateFormatter.VALIDATION_PATTERNS.get(
            user_format,
            r'^\d{2}\.\d{2}\.\d{4}$'
        )
    
    @staticmethod
    def format_date_range(
        start_date: Union[date, datetime, str],
        end_date: Union[date, datetime, str],
        user_format: str = 'ДД.ММ.ГГГГ'
    ) -> str:
        """
        Форматировать диапазон дат
        
        Args:
            start_date: Начальная дата
            end_date: Конечная дата
            user_format: Формат из настроек пользователя
            
        Returns:
            Отформатированная строка диапазона дат
        """
        start_str = DateFormatter.format_date(start_date, user_format)
        end_str = DateFormatter.format_date(end_date, user_format)
        return f"{start_str} - {end_str}"


async def get_user_date_format(user_id: int) -> str:
    """
    Получить формат даты пользователя из базы данных

    Args:
        user_id: ID пользователя

    Returns:
        Формат даты (по умолчанию 'ДД.ММ.ГГГГ')
    """
    from database.queries import get_user_settings

    settings = await get_user_settings(user_id)
    if settings:
        return settings.get('date_format', 'ДД.ММ.ГГГГ')
    return 'ДД.ММ.ГГГГ'