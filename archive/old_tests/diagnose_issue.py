"""
Диагностика: почему не работает ввод пульса и мест
"""
import sys
import asyncio
import aiosqlite
import os
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

async def diagnose():
    print("=" * 80)
    print("ДИАГНОСТИКА ПРОБЛЕМЫ С ВВОДОМ ПУЛЬСА И МЕСТ")
    print("=" * 80)

    print("\n[1] ПРОВЕРКА БАЗЫ ДАННЫХ")
    print("-" * 80)

    db_path = os.getenv('DB_PATH', 'bot_data.db')

    if not os.path.exists(db_path):
        print(f"  [FAIL] База данных не найдена: {db_path}")
        return

    async with aiosqlite.connect(db_path) as db:
        # Проверяем структуру таблицы
        cursor = await db.execute("PRAGMA table_info(competition_participants)")
        columns = await cursor.fetchall()

        print(f"\n  Структура таблицы competition_participants:")
        has_heart_rate = False
        has_place_overall = False
        has_place_age = False

        for col in columns:
            col_name = col[1]
            col_type = col[2]
            print(f"    - {col_name} ({col_type})")

            if col_name == 'heart_rate':
                has_heart_rate = True
            if col_name == 'place_overall':
                has_place_overall = True
            if col_name == 'place_age_category':
                has_place_age = True

        print()
        print(f"  {'[OK]' if has_heart_rate else '[FAIL]'} Поле heart_rate")
        print(f"  {'[OK]' if has_place_overall else '[FAIL]'} Поле place_overall")
        print(f"  {'[OK]' if has_place_age else '[FAIL]'} Поле place_age_category")

        # Проверяем есть ли соревнования
        cursor = await db.execute("""
            SELECT COUNT(*) FROM competitions WHERE status = 'finished'
        """)
        finished_count = (await cursor.fetchone())[0]

        cursor = await db.execute("""
            SELECT COUNT(*) FROM competition_participants
            WHERE finish_time IS NOT NULL
        """)
        results_count = (await cursor.fetchone())[0]

        print(f"\n  Прошедших соревнований в БД: {finished_count}")
        print(f"  Результатов с временем: {results_count}")

        # Проверяем конкретные данные результатов
        cursor = await db.execute("""
            SELECT
                c.name,
                cp.finish_time,
                cp.place_overall,
                cp.place_age_category,
                cp.heart_rate
            FROM competition_participants cp
            JOIN competitions c ON c.id = cp.competition_id
            WHERE cp.finish_time IS NOT NULL
            LIMIT 5
        """)

        results = await cursor.fetchall()

        if results:
            print(f"\n  Примеры результатов:")
            for r in results:
                name, time, place_overall, place_age, hr = r
                print(f"    - {name}")
                print(f"      Время: {time}")
                print(f"      Место общее: {place_overall if place_overall else 'не указано'}")
                print(f"      Место категория: {place_age if place_age else 'не указано'}")
                print(f"      Пульс: {hr if hr else 'не указан'}")
        else:
            print(f"\n  [INFO] Нет результатов в БД для проверки")

    print("\n[2] ПРОВЕРКА ОБРАБОТЧИКОВ")
    print("-" * 80)

    from competitions import competitions_handlers
    from bot.fsm import CompetitionStates

    handlers_to_check = [
        'start_add_result',
        'process_finish_time',
        'process_place_overall',
        'process_place_age_category',
        'process_heart_rate'
    ]

    all_handlers_ok = True
    for handler_name in handlers_to_check:
        exists = hasattr(competitions_handlers, handler_name)
        print(f"  {'[OK]' if exists else '[FAIL]'} {handler_name}")
        if not exists:
            all_handlers_ok = False

    print("\n[3] ПРОВЕРКА FSM СОСТОЯНИЙ")
    print("-" * 80)

    states_to_check = [
        'waiting_for_finish_time',
        'waiting_for_place_overall',
        'waiting_for_place_age',
        'waiting_for_heart_rate'
    ]

    all_states_ok = True
    for state_name in states_to_check:
        exists = hasattr(CompetitionStates, state_name)
        print(f"  {'[OK]' if exists else '[FAIL]'} CompetitionStates.{state_name}")
        if not exists:
            all_states_ok = False

    print("\n[4] ПРОВЕРКА РОУТЕРА")
    print("-" * 80)

    router = competitions_handlers.router
    print(f"  Всего обработчиков в роутере: {len(router.observers)}")

    # Проверяем наличие конкретных обработчиков
    handler_names = []
    for observer in router.observers:
        if hasattr(observer, 'callback') and hasattr(observer.callback, '__name__'):
            handler_names.append(observer.callback.__name__)

    our_handlers = ['start_add_result', 'process_finish_time', 'process_place_overall',
                    'process_place_age_category', 'process_heart_rate']

    print(f"\n  Наши обработчики в роутере:")
    for h in our_handlers:
        found = h in handler_names
        print(f"    {'[OK]' if found else '[FAIL]'} {h}")

    print("\n" + "=" * 80)
    print("ДИАГНОЗ:")
    print("=" * 80)

    if not all_handlers_ok:
        print("\n  [ПРОБЛЕМА] Не все обработчики найдены в коде")
        print("  РЕШЕНИЕ: Проверить competitions_handlers.py")
    elif not all_states_ok:
        print("\n  [ПРОБЛЕМА] Не все FSM состояния найдены")
        print("  РЕШЕНИЕ: Проверить bot/fsm.py")
    elif not has_heart_rate or not has_place_overall or not has_place_age:
        print("\n  [ПРОБЛЕМА] Поля отсутствуют в базе данных")
        print("  РЕШЕНИЕ: Запустить миграцию migrations/add_heart_rate_field.py")
    else:
        print("\n  [OK] Все компоненты на месте!")
        print("\n  ВОЗМОЖНАЯ ПРИЧИНА: Бот работает со старым кэшем Python")
        print("\n  РЕШЕНИЕ:")
        print("    1. Остановите бота (Ctrl+C)")
        print("    2. Удалите кэш: ")
        print("       for /d /r . %d in (__pycache__) do @if exist \"%d\" rd /s /q \"%d\"")
        print("    3. Запустите бота заново: venv\\Scripts\\python.exe main.py")
        print("\n  ИЛИ используйте: .\\restart.ps1")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(diagnose())
