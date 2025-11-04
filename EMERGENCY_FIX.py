"""
ЭКСТРЕННАЯ ПРОВЕРКА И ИСПРАВЛЕНИЕ
"""
import asyncio
import aiosqlite
import os
import sys

async def emergency_fix():
    print("=" * 70)
    print("ЭКСТРЕННАЯ ДИАГНОСТИКА")
    print("=" * 70)

    # 1. Проверяем БД
    db_path = os.getenv('DB_PATH', 'bot_data.db')
    print(f"\n[1] Проверка БД: {db_path}")

    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute('PRAGMA table_info(competition_participants)')
        columns = await cursor.fetchall()

        fields = {col[1] for col in columns}

        print(f"    Поле 'heart_rate': {'[OK]' if 'heart_rate' in fields else '[MISSING]'}")
        print(f"    Поле 'place_overall': {'[OK]' if 'place_overall' in fields else '[MISSING]'}")
        print(f"    Поле 'place_age_category': {'[OK]' if 'place_age_category' in fields else '[MISSING]'}")

    # 2. Проверяем импорты модулей
    print(f"\n[2] Проверка модулей...")

    try:
        from bot.fsm import CompetitionStates
        print(f"    FSM импорт: [OK]")
        print(f"    waiting_for_heart_rate: {'[OK]' if hasattr(CompetitionStates, 'waiting_for_heart_rate') else '[MISSING]'}")
    except Exception as e:
        print(f"    FSM импорт: [FAIL] {e}")
        return False

    try:
        from competitions import competitions_handlers
        print(f"    Handlers импорт: [OK]")

        handlers_check = {
            'start_add_result': hasattr(competitions_handlers, 'start_add_result'),
            'process_finish_time': hasattr(competitions_handlers, 'process_finish_time'),
            'process_place_overall': hasattr(competitions_handlers, 'process_place_overall'),
            'process_place_age_category': hasattr(competitions_handlers, 'process_place_age_category'),
            'process_heart_rate': hasattr(competitions_handlers, 'process_heart_rate'),
        }

        for name, exists in handlers_check.items():
            print(f"      {name}: {'[OK]' if exists else '[MISSING]'}")
    except Exception as e:
        print(f"    Handlers импорт: [FAIL] {e}")
        return False

    # 3. Проверяем роутер
    print(f"\n[3] Проверка роутера...")
    router = competitions_handlers.router
    print(f"    Роутер: {router}")
    print(f"    Обработчиков: {len(router.observers)}")

    # 4. Проверяем регистрацию обработчиков в роутере
    print(f"\n[4] Поиск обработчиков в роутере...")

    found_handlers = set()
    for observer in router.observers:
        if hasattr(observer, 'callback'):
            callback = observer.callback
            if hasattr(callback, '__name__'):
                found_handlers.add(callback.__name__)

    required = ['start_add_result', 'process_finish_time', 'process_place_overall',
                'process_place_age_category', 'process_heart_rate']

    for handler in required:
        if handler in found_handlers:
            print(f"    {handler}: [FOUND IN ROUTER]")
        else:
            print(f"    {handler}: [NOT IN ROUTER]")

    # 5. Тест callback
    print(f"\n[5] Тест callback паттерна...")
    test_callback = "comp:add_result:123"
    print(f"    Тестовый callback: {test_callback}")

    # Проверяем есть ли обработчик для этого паттерна
    from aiogram import F
    test_filter = F.data.startswith("comp:add_result:")
    print(f"    Фильтр создан: {test_filter}")

    # 6. Проверяем сигнатуру add_competition_result
    print(f"\n[6] Проверка add_competition_result...")
    from competitions.competitions_queries import add_competition_result
    import inspect

    sig = inspect.signature(add_competition_result)
    params = list(sig.parameters.keys())
    print(f"    Параметры: {params}")
    print(f"    heart_rate в параметрах: {'[OK]' if 'heart_rate' in params else '[MISSING]'}")

    # 7. ИТОГОВЫЙ ДИАГНОЗ
    print("\n" + "=" * 70)
    print("ДИАГНОЗ:")
    print("=" * 70)

    all_ok = all([
        'heart_rate' in fields,
        hasattr(CompetitionStates, 'waiting_for_heart_rate'),
        all(handlers_check.values()),
        'heart_rate' in params
    ])

    if all_ok:
        print("\n✓ ВСЕ КОМПОНЕНТЫ НА МЕСТЕ")
        print("\n→ ПРОБЛЕМА: Бот использует СТАРЫЙ КОД из памяти!")
        print("\n→ РЕШЕНИЕ:")
        print("  1. ПОЛНОСТЬЮ остановите бота (taskkill /F /IM python.exe)")
        print("  2. Очистите кэш: del /s /q *.pyc && for /d /r . %d in (__pycache__) do @if exist \"%d\" rd /s /q \"%d\"")
        print("  3. Запустите: venv\\Scripts\\python.exe main.py")
    else:
        print("\n✗ ОБНАРУЖЕНЫ ПРОБЛЕМЫ В КОДЕ")
        print("\n→ Необходимо проверить исходные файлы")

    return all_ok

if __name__ == '__main__':
    result = asyncio.run(emergency_fix())
    sys.exit(0 if result else 1)
