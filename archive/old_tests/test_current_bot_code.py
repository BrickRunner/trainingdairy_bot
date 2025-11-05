"""
Проверка какая версия кода используется в РАБОТАЮЩЕМ боте
"""
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("ПРОВЕРКА ВЕРСИИ КОДА В РАБОТАЮЩЕМ БОТЕ")
print("=" * 70)

try:
    # Пытаемся импортировать модули БЕЗ перезагрузки
    # Это покажет что загружено в памяти
    import competitions.competitions_handlers as handlers
    import competitions.competitions_queries as queries
    import bot.fsm as fsm

    print("\n[INFO] Модули уже загружены в память")
    print(f"       handlers: {handlers.__file__}")
    print(f"       queries:  {queries.__file__}")
    print(f"       fsm:      {fsm.__file__}")

    # Проверяем наличие обработчиков
    print("\n" + "=" * 70)
    print("ОБРАБОТЧИКИ В ПАМЯТИ:")
    print("=" * 70)

    handlers_list = [
        'start_add_result',
        'process_finish_time',
        'process_place_overall',
        'process_place_age_category',
        'process_heart_rate'  # НОВЫЙ обработчик
    ]

    all_present = True
    for handler_name in handlers_list:
        if hasattr(handlers, handler_name):
            func = getattr(handlers, handler_name)
            # Проверяем исходный код функции
            import inspect
            source_file = inspect.getsourcefile(func)
            print(f"[OK] {handler_name:30} -> {source_file}")
        else:
            print(f"[FAIL] {handler_name:30} -> НЕ НАЙДЕН")
            all_present = False

    # Проверяем сигнатуру add_competition_result
    print("\n" + "=" * 70)
    print("ПАРАМЕТРЫ add_competition_result:")
    print("=" * 70)

    import inspect
    sig = inspect.signature(queries.add_competition_result)
    for param_name in sig.parameters:
        print(f"   - {param_name}")

    has_heart_rate = 'heart_rate' in sig.parameters

    print("\n" + "=" * 70)
    print("РЕЗУЛЬТАТ:")
    print("=" * 70)

    if all_present and has_heart_rate:
        print("\n✓ ВСЕ ОБРАБОТЧИКИ ЗАГРУЖЕНЫ ПРАВИЛЬНО")
        print("✓ ПАРАМЕТР heart_rate ПРИСУТСТВУЕТ")
        print("\n→ Если обработчики не работают, это проблема с регистрацией роутера")
        print("→ Попробуйте перезапустить бота через kill_and_restart.bat")
    else:
        print("\n✗ ОБНАРУЖЕНЫ ПРОБЛЕМЫ")
        print("✗ БОТ ИСПОЛЬЗУЕТ СТАРУЮ ВЕРСИЮ КОДА")
        print("\n→ НЕОБХОДИМО ПЕРЕЗАПУСТИТЬ БОТА:")
        print("  1. Остановите бота (Ctrl+C)")
        print("  2. Запустите: kill_and_restart.bat")

except Exception as e:
    print(f"\n[ERROR] Ошибка при проверке: {e}")
    print("\n→ Модули не загружены (бот не запущен или ошибка импорта)")

print("\n" + "=" * 70)
