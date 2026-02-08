"""
FSM состояния для Training Assistant
"""

from aiogram.fsm.state import State, StatesGroup


class TrainingPlanStates(StatesGroup):
    """Состояния для создания тренировочного плана"""

    waiting_for_sport_type = State()        
    waiting_for_plan_duration = State()     
    waiting_for_available_days = State()    


class CorrectionStates(StatesGroup):
    """Состояния для коррекции тренировки"""

    selecting_training = State()            
    waiting_for_feedback = State()          
    waiting_for_comment = State()           


class RacePreparationStates(StatesGroup):
    """Состояния для подготовки к соревнованию"""

    selecting_competition = State()         
    selecting_days_before = State()         
    waiting_for_target_time = State()       


class RaceTacticsStates(StatesGroup):
    """Состояния для тактики забега"""

    selecting_competition = State()         
    waiting_for_target_time = State()       
    waiting_for_race_type = State()         


class PsychologistStates(StatesGroup):
    """Состояния для психологической поддержки"""

    waiting_for_problem = State()           
    in_conversation = State()               


class ResultPredictionStates(StatesGroup):
    """Состояния для прогноза результата"""

    waiting_for_distance = State()          
    waiting_for_analysis_period = State()   
