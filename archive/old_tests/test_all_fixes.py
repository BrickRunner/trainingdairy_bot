"""
Финальный тест всех исправлений
"""
import sys
import os

print("=" * 80)
print("ФИНАЛЬНАЯ ПРОВЕРКА ВСЕХ ИСПРАВЛЕНИЙ")
print("=" * 80)

all_ok = True

# 1. Проверка что файлы изменены
print("\n[1] ПРОВЕРКА ИЗМЕНЁННЫХ ФАЙЛОВ")
print("-" * 80)

from competitions import custom_competitions_handlers
import inspect

# Проверяем что в custom_competitions_handlers есть обработка "change"
source = inspect.getsource(custom_competitions_handlers.handle_past_comp_calendar_navigation)
has_change_action = 'action == "change"' in source

print(f"  {'[OK]' if has_change_action else '[FAIL]'} Календарь: обработка action='change'")
if not has_change_action:
    all_ok = False
    print("       ОШИБКА: В handle_past_comp_calendar_navigation нет обработки 'change'")

# 2. Проверка workflow добавления результата
print("\n[2] ПРОВЕРКА WORKFLOW ДОБАВЛЕНИЯ РЕЗУЛЬТАТА")
print("-" * 80)

from competitions import competitions_handlers
from bot.fsm import CompetitionStates

handlers = {
    'start_add_result': 'Начало добавления результата (запрос времени)',
    'process_finish_time': 'Обработка времени (запрос места общее)',
    'process_place_overall': 'Обработка места общее (запрос места категория)',
    'process_place_age_category': 'Обработка места категория (запрос пульса)',
    'process_heart_rate': 'Обработка пульса (сохранение в БД)'
}

for handler_name, description in handlers.items():
    exists = hasattr(competitions_handlers, handler_name)
    print(f"  {'[OK]' if exists else '[FAIL]'} {handler_name}")
    print(f"       {description}")
    if not exists:
        all_ok = False

# 3. Проверка FSM состояний
print("\n[3] ПРОВЕРКА FSM СОСТОЯНИЙ")
print("-" * 80)

states = {
    'waiting_for_finish_time': 'Ожидание ввода времени',
    'waiting_for_place_overall': 'Ожидание ввода места общее',
    'waiting_for_place_age': 'Ожидание ввода места категория',
    'waiting_for_heart_rate': 'Ожидание ввода пульса'
}

for state_name, description in states.items():
    exists = hasattr(CompetitionStates, state_name)
    print(f"  {'[OK]' if exists else '[FAIL]'} CompetitionStates.{state_name}")
    print(f"       {description}")
    if not exists:
        all_ok = False

# 4. Проверка add_competition_result
print("\n[4] ПРОВЕРКА ФУНКЦИИ СОХРАНЕНИЯ")
print("-" * 80)

from competitions.competitions_queries import add_competition_result

sig = inspect.signature(add_competition_result)
params = list(sig.parameters.keys())

required_params = {
    'heart_rate': 'Средний пульс',
    'place_overall': 'Место в общем зачёте',
    'place_age_category': 'Место в возрастной категории'
}

for param, description in required_params.items():
    exists = param in params
    print(f"  {'[OK]' if exists else '[FAIL]'} Параметр: {param}")
    print(f"       {description}")
    if not exists:
        all_ok = False

# 5. Проверка кнопки "Добавить результат"
print("\n[5] ПРОВЕРКА ОТОБРАЖЕНИЯ КНОПКИ")
print("-" * 80)

view_source = inspect.getsource(competitions_handlers.view_my_competition)
checks = {
    'is_finished': 'Проверка что соревнование прошло',
    'comp:add_result:': 'Callback для добавления результата',
    'has_result': 'Проверка наличия результата'
}

for check, description in checks.items():
    exists = check in view_source
    print(f"  {'[OK]' if exists else '[FAIL]'} {check}")
    print(f"       {description}")
    if not exists:
        all_ok = False

# 6. Проверка компиляции
print("\n[6] ПРОВЕРКА КОМПИЛЯЦИИ")
print("-" * 80)

files_to_check = [
    'competitions/competitions_handlers.py',
    'competitions/custom_competitions_handlers.py',
    'bot/fsm.py',
    'competitions/competitions_queries.py'
]

import py_compile

for file in files_to_check:
    try:
        py_compile.compile(file, doraise=True)
        print(f"  [OK] {file}")
    except Exception as e:
        print(f"  [FAIL] {file}")
        print(f"       ОШИБКА: {e}")
        all_ok = False

# 7. Проверка скриптов перезапуска
print("\n[7] ПРОВЕРКА СКРИПТОВ ПЕРЕЗАПУСКА")
print("-" * 80)

scripts = [
    'FORCE_RESTART.bat',
    'FORCE_RESTART.ps1',
    'STOP_BOT.bat',
    'START_BOT.bat'
]

for script in scripts:
    exists = os.path.exists(script)
    print(f"  {'[OK]' if exists else '[WARN]'} {script}")
    if script.startswith('FORCE_RESTART') and not exists:
        all_ok = False

# Итог
print("\n" + "=" * 80)
print("ИТОГОВЫЙ РЕЗУЛЬТАТ")
print("=" * 80)

if all_ok:
    print("\n  [SUCCESS] ВСЕ ИСПРАВЛЕНИЯ ПРОВЕРЕНЫ И ГОТОВЫ!")
    print("\n  СЛЕДУЮЩИЙ ШАГ:")
    print("  ===============================================================")
    print("  |  ЗАПУСТИТЕ ПЕРЕЗАПУСК:                                    |")
    print("  |                                                            |")
    print("  |  .\\FORCE_RESTART.ps1                                       |")
    print("  |                                                            |")
    print("  |  ИЛИ                                                       |")
    print("  |                                                            |")
    print("  |  FORCE_RESTART.bat                                        |")
    print("  ===============================================================")
    print("\n  После перезапуска проверьте в Telegram:")
    print("  1. Соревнования -> Мои соревнования")
    print("  2. Выберите прошедшее соревнование")
    print("  3. Нажмите 'Добавить результат'")
    print("  4. Пройдите 4 шага: ВРЕМЯ -> МЕСТО -> КАТЕГОРИЯ -> ПУЛЬС")
    print()
else:
    print("\n  [FAIL] ОБНАРУЖЕНЫ ПРОБЛЕМЫ!")
    print("\n  Проверьте сообщения выше и исправьте ошибки.")
    print()

print("=" * 80)
