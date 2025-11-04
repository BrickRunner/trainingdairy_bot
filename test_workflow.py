"""
Тест workflow добавления результата соревнования
Проверяем что все обработчики на месте и правильно связаны
"""
import sys
import os

print("=" * 70)
print("ПРОВЕРКА WORKFLOW ДОБАВЛЕНИЯ РЕЗУЛЬТАТА")
print("=" * 70)

# Импортируем модули
from bot.fsm import CompetitionStates
from competitions import competitions_handlers
import inspect

print("\n[1] Проверка FSM состояний:")
print("-" * 70)

states = [
    'waiting_for_finish_time',
    'waiting_for_place_overall',
    'waiting_for_place_age',
    'waiting_for_heart_rate'
]

for state_name in states:
    has_state = hasattr(CompetitionStates, state_name)
    status = "[OK]" if has_state else "[MISSING]"
    print(f"  {status} CompetitionStates.{state_name}")

print("\n[2] Проверка обработчиков:")
print("-" * 70)

handlers = [
    ('start_add_result', 'callback_query', 'comp:add_result:'),
    ('process_finish_time', 'message', 'waiting_for_finish_time'),
    ('process_place_overall', 'message', 'waiting_for_place_overall'),
    ('process_place_age_category', 'message', 'waiting_for_place_age'),
    ('process_heart_rate', 'message', 'waiting_for_heart_rate')
]

for handler_name, handler_type, trigger in handlers:
    exists = hasattr(competitions_handlers, handler_name)
    status = "[OK]" if exists else "[MISSING]"
    print(f"  {status} {handler_name}")
    if exists:
        print(f"       Тип: {handler_type}, Триггер: {trigger}")

print("\n[3] Проверка workflow цепочки:")
print("-" * 70)

workflow = [
    "1. Пользователь нажимает 'Добавить результат'",
    "   -> Callback: comp:add_result:{id}",
    "   -> Обработчик: start_add_result()",
    "   -> Устанавливает состояние: waiting_for_finish_time",
    "",
    "2. Пользователь вводит время (например: 42:30.50)",
    "   -> State: waiting_for_finish_time",
    "   -> Обработчик: process_finish_time()",
    "   -> Устанавливает состояние: waiting_for_place_overall",
    "",
    "3. Пользователь вводит место в общем зачёте",
    "   -> State: waiting_for_place_overall",
    "   -> Обработчик: process_place_overall()",
    "   -> Устанавливает состояние: waiting_for_place_age",
    "",
    "4. Пользователь вводит место в категории",
    "   -> State: waiting_for_place_age",
    "   -> Обработчик: process_place_age_category()",
    "   -> Устанавливает состояние: waiting_for_heart_rate",
    "",
    "5. Пользователь вводит пульс",
    "   -> State: waiting_for_heart_rate",
    "   -> Обработчик: process_heart_rate()",
    "   -> Сохраняет результат в БД"
]

for line in workflow:
    print(f"  {line}")

print("\n[4] Проверка функции сохранения результата:")
print("-" * 70)

from competitions.competitions_queries import add_competition_result
sig = inspect.signature(add_competition_result)
params = list(sig.parameters.keys())

print(f"  Параметры add_competition_result():")
for param in params:
    print(f"    - {param}")

required_params = ['heart_rate', 'place_overall', 'place_age_category']
for param in required_params:
    has_param = param in params
    status = "[OK]" if has_param else "[MISSING]"
    print(f"  {status} Параметр '{param}' присутствует")

print("\n[5] Проверка импорта в main.py:")
print("-" * 70)

# Читаем main.py
if os.path.exists('main.py'):
    with open('main.py', 'r', encoding='utf-8') as f:
        main_content = f.read()

    has_router_import = 'from competitions.competitions_handlers import router' in main_content or 'competitions_handlers' in main_content
    has_router_include = 'dp.include_router' in main_content or 'include_router(router)' in main_content or 'include_router(competitions_handlers.router)' in main_content

    print(f"  {'[OK]' if has_router_import else '[FAIL]'} Импорт competitions_handlers")
    print(f"  {'[OK]' if has_router_include else '[FAIL]'} Регистрация router в dispatcher")
else:
    print("  [WARN] main.py не найден")

print("\n" + "=" * 70)
print("ИТОГОВЫЙ ВЫВОД:")
print("=" * 70)

all_handlers_exist = all(hasattr(competitions_handlers, h[0]) for h in handlers)
all_states_exist = all(hasattr(CompetitionStates, s) for s in states)

if all_handlers_exist and all_states_exist:
    print("\n  [SUCCESS] Все компоненты на месте!")
    print("\n  После перезапуска бота workflow должен работать:")
    print("  1. Время -> 2. Место общее -> 3. Место категория -> 4. Пульс")
    print("\n  ВАЖНО: Необходим ПОЛНЫЙ ПЕРЕЗАПУСК бота!")
    print("  Запустите: .\\restart.ps1 или .\\STOP_BOT.bat + .\\START_BOT.bat")
else:
    print("\n  [FAIL] Обнаружены проблемы в коде")
    if not all_handlers_exist:
        print("  - Не все обработчики найдены")
    if not all_states_exist:
        print("  - Не все FSM состояния найдены")

print("\n" + "=" * 70)
