"""
FSM состояния для раздела соревнований
"""

from aiogram.fsm.state import State, StatesGroup


class UpcomingCompetitionsStates(StatesGroup):
    """Состояния для поиска предстоящих соревнований"""
    waiting_for_city = State()
    waiting_for_sport = State()
    showing_results = State()


class CompetitionsExportStates(StatesGroup):
    """Состояния для экспорта соревнований в PDF"""
    waiting_for_start_date = State()
    waiting_for_end_date = State()
