"""
FSM состояния для раздела соревнований
"""

from aiogram.fsm.state import State, StatesGroup


class UpcomingCompetitionsStates(StatesGroup):
    """Состояния для поиска предстоящих соревнований"""
    waiting_for_city = State()
    waiting_for_period = State()
    waiting_for_sport = State()
    showing_results = State()
    waiting_for_distance = State()
    waiting_for_target_time = State()


class CompetitionsExportStates(StatesGroup):
    """Состояния для экспорта соревнований в PDF"""
    waiting_for_start_date = State()
    waiting_for_end_date = State()
