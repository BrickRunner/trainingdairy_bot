"""
AI Services для Training Assistant
"""

from training_assistant.services.plan_generator import generate_training_plan
from training_assistant.services.workout_corrector import analyze_and_correct_workout
from training_assistant.services.race_preparation import get_race_preparation_advice
from training_assistant.services.race_tactics import generate_race_tactics
from training_assistant.services.sports_psychologist import chat_with_psychologist
from training_assistant.services.result_predictor import predict_race_result
from training_assistant.services.utils import get_user_preferences

__all__ = [
    'generate_training_plan',
    'analyze_and_correct_workout',
    'get_race_preparation_advice',
    'generate_race_tactics',
    'chat_with_psychologist',
    'predict_race_result',
    'get_user_preferences'
]
