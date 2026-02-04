"""
FSM состояния для Training Assistant
"""

from aiogram.fsm.state import State, StatesGroup


class TrainingPlanStates(StatesGroup):
    """Состояния для создания тренировочного плана"""

    waiting_for_sport_type = State()        # Выбор вида спорта
    waiting_for_plan_duration = State()     # Длительность плана (неделя/месяц)
    waiting_for_available_days = State()    # Доступные дни для тренировок (множественный выбор)


class CorrectionStates(StatesGroup):
    """Состояния для коррекции тренировки"""

    selecting_training = State()            # Выбор тренировки для коррекции
    waiting_for_feedback = State()          # Обратная связь (легко/тяжело/пульс)
    waiting_for_comment = State()           # Дополнительный комментарий


class RacePreparationStates(StatesGroup):
    """Состояния для подготовки к соревнованию"""

    selecting_competition = State()         # Выбор соревнования
    selecting_days_before = State()         # За сколько дней (7/5/3/1)
    waiting_for_target_time = State()       # Ожидание ввода целевого времени


class RaceTacticsStates(StatesGroup):
    """Состояния для тактики забега"""

    selecting_competition = State()         # Выбор соревнования
    waiting_for_target_time = State()       # Целевое время
    waiting_for_race_type = State()         # Тип трассы


class PsychologistStates(StatesGroup):
    """Состояния для психологической поддержки"""

    waiting_for_problem = State()           # Описание проблемы/переживания
    in_conversation = State()               # Продолжение диалога


class ResultPredictionStates(StatesGroup):
    """Состояния для прогноза результата"""

    waiting_for_distance = State()          # Дистанция для прогноза
    waiting_for_analysis_period = State()   # Период анализа (месяц/2 недели)
