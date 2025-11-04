"""
Детальная диагностика обработчиков
"""
import sys

def debug_handlers():
    print("=" * 60)
    print("ДЕТАЛЬНАЯ ДИАГНОСТИКА ОБРАБОТЧИКОВ РЕЗУЛЬТАТОВ")
    print("=" * 60)

    # Импортируем роутер
    from competitions import competitions_handlers
    router = competitions_handlers.router

    print(f"\n[INFO] Роутер загружен: {router}")
    print(f"[INFO] Всего обработчиков в роутере: {len(router.observers)}")

    # Ищем обработчики по именам функций
    print("\n" + "=" * 60)
    print("CALLBACK QUERY ОБРАБОТЧИКИ:")
    print("=" * 60)

    callback_handlers = [
        'start_add_result',
        'show_my_results',
        'show_my_results_period'
    ]

    for handler_name in callback_handlers:
        if hasattr(competitions_handlers, handler_name):
            func = getattr(competitions_handlers, handler_name)
            print(f"\n[OK] {handler_name}")
            print(f"     Функция: {func}")
        else:
            print(f"\n[FAIL] {handler_name} - НЕ НАЙДЕН")

    # Проверяем MESSAGE обработчики
    print("\n" + "=" * 60)
    print("MESSAGE ОБРАБОТЧИКИ (FSM):")
    print("=" * 60)

    message_handlers = [
        ('process_finish_time', 'waiting_for_finish_time'),
        ('process_place_overall', 'waiting_for_place_overall'),
        ('process_place_age_category', 'waiting_for_place_age'),
        ('process_heart_rate', 'waiting_for_heart_rate')
    ]

    from bot.fsm import CompetitionStates

    for func_name, state_name in message_handlers:
        if hasattr(competitions_handlers, func_name):
            func = getattr(competitions_handlers, func_name)
            state = getattr(CompetitionStates, state_name, None)
            print(f"\n[OK] {func_name}")
            print(f"     FSM State: {state_name}")
            print(f"     State value: {state}")
        else:
            print(f"\n[FAIL] {func_name} - НЕ НАЙДЕН")

    # Проверяем порядок обработчиков в роутере
    print("\n" + "=" * 60)
    print("АНАЛИЗ РОУТЕРА (первые 10 обработчиков):")
    print("=" * 60)

    for idx, observer in enumerate(router.observers[:10], 1):
        print(f"\n{idx}. {observer}")
        if hasattr(observer, 'callback'):
            print(f"   Callback: {observer.callback}")

    # Тест времени с сотыми
    print("\n" + "=" * 60)
    print("ТЕСТ ПОДДЕРЖКИ СОТЫХ ДОЛЕЙ:")
    print("=" * 60)

    from utils.time_formatter import normalize_time, validate_time_format

    test_cases = [
        "01:23:45.50",
        "00:42:30.25",
        "1:23:45",
        "42:30",
        "00:05:30.1",
    ]

    for test in test_cases:
        valid = validate_time_format(test)
        if valid:
            normalized = normalize_time(test)
            print(f"[OK] {test:15} -> {normalized} (valid: {valid})")
        else:
            print(f"[FAIL] {test:15} -> INVALID")

    print("\n" + "=" * 60)
    print("РЕКОМЕНДАЦИИ:")
    print("=" * 60)
    print("""
1. Если обработчики присутствуют, но не срабатывают:
   - Используйте restart_bot.bat для перезапуска
   - Убедитесь что процесс Python полностью завершен

2. Проверьте логи бота при добавлении результата:
   - Какое состояние FSM установлено
   - Какие обработчики вызываются

3. Тестовый сценарий:
   a) Откройте бот
   b) Соревнования -> Мои соревнования
   c) Выберите завершенное соревнование
   d) Нажмите "Добавить результат"
   e) Введите время (например: 42:30.50)
   f) Проверьте что запрашивается место
    """)

if __name__ == '__main__':
    debug_handlers()
