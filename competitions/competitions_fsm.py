"""
FSM состояния для раздела соревнований
"""

from aiogram.fsm.state import State, StatesGroup


class UpcomingCompetitionsStates(StatesGroup):
    """Состояния для поиска предстоящих соревнований"""
    waiting_for_city = State()
    waiting_for_period = State()
    waiting_for_sport = State()
    waiting_for_service = State()  # Выбор сервиса для регистрации
    showing_results = State()
    waiting_for_distance = State()  # Старое: выбор одной дистанции
    selecting_multiple_distances = State()  # Новое: выбор нескольких дистанций с чекбоксами
    waiting_for_custom_distance = State()  # Ручной ввод дистанции (для HeroLeague)
    waiting_for_target_time = State()


class CompetitionsExportStates(StatesGroup):
    """Состояния для экспорта соревнований в PDF"""
    waiting_for_start_date = State()
    waiting_for_end_date = State()


class CoachUpcomingCompetitionsStates(StatesGroup):
    """Состояния для поиска предстоящих соревнований для тренера"""
    waiting_for_city = State()
    waiting_for_period = State()
    waiting_for_sport = State()
    waiting_for_service = State()
    showing_results = State()
    selecting_multiple_distances = State()  # Выбор нескольких дистанций с чекбоксами
    waiting_for_custom_distance = State()  # Ручной ввод дистанции (для HeroLeague)
    waiting_for_target_time = State()  # Ввод целевого времени
