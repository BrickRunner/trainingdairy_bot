"""
FSM состояния для многошаговых операций
"""

from aiogram.fsm.state import State, StatesGroup


class AddTrainingStates(StatesGroup):
    """Состояния для добавления тренировки"""
    
    # Общие поля для всех типов тренировок
    waiting_for_type = State()          # Выбор типа тренировки
    waiting_for_date = State()          # Дата тренировки
    waiting_for_duration = State()      # Продолжительность (минуты)
    
    # Поля специфичные для кросса
    waiting_for_distance = State()      # Дистанция (км)
    waiting_for_pulse = State()         # Средний пульс
    waiting_for_description = State()   # Описание тренировки
    waiting_for_results = State()       # Результаты
    waiting_for_comment = State()       # Комментарий
    waiting_for_fatigue = State()       # Уровень усталости (1-10)
