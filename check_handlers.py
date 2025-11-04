"""
Диагностический скрипт для проверки обработчиков результатов
"""
import sys
import importlib

def check_handlers():
    print("=== Проверка обработчиков ===\n")

    # Проверяем FSM состояния
    print("1. Проверка FSM состояний...")
    from bot.fsm import CompetitionStates

    states = [
        'waiting_for_finish_time',
        'waiting_for_place_overall',
        'waiting_for_place_age',
        'waiting_for_heart_rate'
    ]

    for state_name in states:
        if hasattr(CompetitionStates, state_name):
            print(f"   [OK] {state_name}")
        else:
            print(f"   [FAIL] {state_name} - НЕ НАЙДЕНО")

    # Проверяем роутер
    print("\n2. Проверка роутера competitions_handlers...")
    from competitions import competitions_handlers
    router = competitions_handlers.router
    print(f"   Роутер загружен: {router}")
    print(f"   Количество обработчиков: {len(router.observers)}")

    # Проверяем функции
    print("\n3. Проверка функций...")
    funcs = [
        'start_add_result',
        'process_finish_time',
        'process_place_overall',
        'process_place_age_category',
        'process_heart_rate'
    ]

    for func_name in funcs:
        if hasattr(competitions_handlers, func_name):
            print(f"   [OK] {func_name}")
        else:
            print(f"   [FAIL] {func_name} - НЕ НАЙДЕНА")

    # Проверяем импорты в competitions_queries
    print("\n4. Проверка competitions_queries...")
    from competitions.competitions_queries import add_competition_result
    import inspect
    sig = inspect.signature(add_competition_result)
    print(f"   Сигнатура add_competition_result:")
    for param_name, param in sig.parameters.items():
        default = f" = {param.default}" if param.default != inspect.Parameter.empty else ""
        print(f"      - {param_name}{default}")

    # Проверяем time_formatter
    print("\n5. Проверка time_formatter...")
    from utils.time_formatter import normalize_time, validate_time_format, calculate_pace
    print(f"   [OK] normalize_time")
    print(f"   [OK] validate_time_format")
    print(f"   [OK] calculate_pace")

    # Тест нормализации
    test_time = "00:45:30"
    normalized = normalize_time(test_time)
    print(f"   Тест: {test_time} -> {normalized}")

    # Тест темпа
    pace = calculate_pace("42:30", 10.0)
    print(f"   Тест темпа: 42:30 на 10км = {pace}/км")

    print("\n=== Проверка завершена ===")

if __name__ == '__main__':
    check_handlers()
