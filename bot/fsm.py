"""
FSM состояния для многошаговых операций
"""

from aiogram.fsm.state import State, StatesGroup


class AddTrainingStates(StatesGroup):
    """Состояния для добавления тренировки"""
    
    # Общие поля для всех типов тренировок
    waiting_for_type = State()          # Выбор типа тренировки
    waiting_for_date = State()          # Дата тренировки
    waiting_for_time = State()          # Время (ЧЧ:ММ:СС)
    waiting_for_duration = State()      # Продолжительность (минуты)
    
    # Поля для тренировок с дистанцией (кросс, плавание, велотренировка)
    waiting_for_distance = State()      # Дистанция (км)
    
    # Поля для силовой тренировки
    waiting_for_exercises = State()     # Описание упражнений
    
    # Поля для интервальной тренировки
    waiting_for_intervals = State()     # Описание интервалов
    
    # Пульс для всех типов тренировок
    waiting_for_avg_pulse = State()     # Средний пульс
    waiting_for_max_pulse = State()     # Максимальный пульс
    
    # Общие завершающие поля
    waiting_for_comment = State()       # Комментарий
    waiting_for_fatigue = State()       # Уровень усталости (1-10)