"""
Модуль для расчёта статистики тренировок
"""

import pandas as pd
from typing import List, Dict, Any

def calculate_weekly_stats(trainings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Рассчитать статистику за неделю.

    Args:
        trainings: Список тренировок (словарей) из БД за неделю.

    Returns:
        Словарь с метриками:
        - total_trainings: общее количество тренировок
        - avg_distance: средний километраж за тренировку (км)
        - type_percentages: процентное распределение типов тренировок
        - avg_fatigue: средний уровень усилий
    """
    if not trainings:
        return {
            "total_trainings": 0,
            "avg_distance": 0.0,
            "type_percentages": {},
            "avg_fatigue": 0.0
        }

    df = pd.DataFrame(trainings)

    total_trainings = len(df)

    avg_distance = df['distance'].mean() if 'distance' in df and df['distance'].notna().any() else 0.0

    type_counts = df['type'].value_counts()
    type_percentages = (type_counts / total_trainings * 100).round(2).to_dict()

    avg_fatigue = df['fatigue_level'].mean().round(2) if 'fatigue_level' in df and df['fatigue_level'].notna().any() else 0.0

    return {
        "total_trainings": total_trainings,
        "avg_distance": round(avg_distance, 2),
        "type_percentages": type_percentages,
        "avg_fatigue": avg_fatigue
    }