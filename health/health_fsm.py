"""
FSM состояния для модуля здоровья
"""

from aiogram.fsm.state import State, StatesGroup


class HealthMetricsStates(StatesGroup):
    """Состояния для ввода метрик здоровья"""
    waiting_for_pulse = State()
    waiting_for_weight = State()
    waiting_for_sleep_duration = State()
    waiting_for_sleep_quality = State()
    waiting_for_mood = State()
    waiting_for_stress = State()
    waiting_for_energy = State()
    waiting_for_notes = State()
