"""
FSM состояния для раздела соревнований
"""

from aiogram.fsm.state import State, StatesGroup


class CompetitionsExportStates(StatesGroup):
    """Состояния для экспорта соревнований в PDF"""
    waiting_for_start_date = State()
    waiting_for_end_date = State()
