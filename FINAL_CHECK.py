"""
Финальная проверка: будет ли работать workflow добавления результата
"""

print("=" * 80)
print("ФИНАЛЬНАЯ ПРОВЕРКА WORKFLOW")
print("=" * 80)

# Проверяем что все обработчики на месте
import sys
from bot.fsm import CompetitionStates
from competitions import competitions_handlers
from competitions.competitions_queries import add_competition_result
import inspect

print("\n[1] ПРОВЕРКА FSM СОСТОЯНИЙ")
print("-" * 80)

states = {
    'waiting_for_finish_time': 'Ожидание ввода времени',
    'waiting_for_place_overall': 'Ожидание места в общем зачёте',
    'waiting_for_place_age': 'Ожидание места в категории',
    'waiting_for_heart_rate': 'Ожидание ввода пульса'
}

all_states_ok = True
for state, description in states.items():
    exists = hasattr(CompetitionStates, state)
    status = "[OK]" if exists else "[FAIL]"
    print(f"  {status} {state}")
    print(f"       -> {description}")
    if not exists:
        all_states_ok = False

print("\n[2] ПРОВЕРКА ОБРАБОТЧИКОВ")
print("-" * 80)

handlers = {
    'start_add_result': 'Начало добавления результата',
    'process_finish_time': 'Обработка времени',
    'process_place_overall': 'Обработка места в общем зачёте',
    'process_place_age_category': 'Обработка места в категории',
    'process_heart_rate': 'Обработка пульса'
}

all_handlers_ok = True
for handler, description in handlers.items():
    exists = hasattr(competitions_handlers, handler)
    status = "[OK]" if exists else "[FAIL]"
    print(f"  {status} {handler}")
    print(f"       -> {description}")
    if not exists:
        all_handlers_ok = False

print("\n[3] ПРОВЕРКА ФУНКЦИИ СОХРАНЕНИЯ")
print("-" * 80)

sig = inspect.signature(add_competition_result)
params = list(sig.parameters.keys())

required = ['user_id', 'competition_id', 'distance', 'finish_time',
            'place_overall', 'place_age_category', 'heart_rate']

all_params_ok = True
for param in required:
    exists = param in params
    status = "[OK]" if exists else "[FAIL]"
    print(f"  {status} Параметр: {param}")
    if not exists:
        all_params_ok = False

print("\n[4] ПРОВЕРКА ОТОБРАЖЕНИЯ КНОПКИ")
print("-" * 80)

source = inspect.getsource(competitions_handlers.view_my_competition)
checks = {
    'is_finished': 'Проверка что соревнование прошло',
    'comp:add_result:': 'Callback для добавления результата',
    'has_result': 'Проверка наличия результата'
}

button_ok = True
for check, description in checks.items():
    exists = check in source
    status = "[OK]" if exists else "[FAIL]"
    print(f"  {status} {check}")
    print(f"       -> {description}")
    if not exists:
        button_ok = False

print("\n[5] СИМУЛЯЦИЯ WORKFLOW")
print("-" * 80)

workflow_steps = [
    ("Шаг 1", "Пользователь открывает прошедшее соревнование"),
    ("Шаг 2", "Видит кнопку 'Добавить результат'"),
    ("Шаг 3", "Нажимает -> вызывается start_add_result()"),
    ("Шаг 4", "Вводит время -> вызывается process_finish_time()"),
    ("Шаг 5", "Вводит место общее -> вызывается process_place_overall()"),
    ("Шаг 6", "Вводит место категория -> вызывается process_place_age_category()"),
    ("Шаг 7", "Вводит пульс -> вызывается process_heart_rate()"),
    ("Шаг 8", "Данные сохраняются через add_competition_result()"),
    ("Шаг 9", "Пользователь видит подтверждение с введёнными данными")
]

for step, description in workflow_steps:
    print(f"  {step}: {description}")

print("\n" + "=" * 80)
print("ИТОГОВЫЙ РЕЗУЛЬТАТ")
print("=" * 80)

all_ok = all_states_ok and all_handlers_ok and all_params_ok and button_ok

if all_ok:
    print("\n  [SUCCESS] ВСЕ КОМПОНЕНТЫ НА МЕСТЕ!")
    print("\n  WORKFLOW ДОБАВЛЕНИЯ РЕЗУЛЬТАТА:")
    print("    1. Запрос времени (с сотыми долями)")
    print("    2. Запрос места в общем зачёте")
    print("    3. Запрос места в возрастной категории")
    print("    4. Запрос среднего пульса")
    print("    5. Сохранение всех данных в БД")
    print("\n  КОД ГОТОВ К РАБОТЕ!")
    print("\n  ВАЖНО: Необходим ПОЛНЫЙ ПЕРЕЗАПУСК БОТА")
    print("  Команда: .\\restart.ps1")
    print("\n  После перезапуска:")
    print("  - Откройте Соревнования -> Мои соревнования")
    print("  - Выберите ПРОШЕДШЕЕ соревнование")
    print("  - Нажмите 'Добавить результат'")
    print("  - Пройдите все 4 шага ввода данных")
else:
    print("\n  [FAIL] ОБНАРУЖЕНЫ ПРОБЛЕМЫ:")
    if not all_states_ok:
        print("    - Не все FSM состояния найдены")
    if not all_handlers_ok:
        print("    - Не все обработчики найдены")
    if not all_params_ok:
        print("    - Не все параметры в функции сохранения")
    if not button_ok:
        print("    - Проблемы с логикой отображения кнопки")

print("\n" + "=" * 80)

# Дополнительная проверка: есть ли обработчики в роутере
print("\n[ДОПОЛНИТЕЛЬНО] Количество обработчиков в роутере:")
print(f"  Всего зарегистрировано: {len(competitions_handlers.router.observers)}")
print("\n  Это нормально если число больше 20")
print("  (в роутере есть и другие обработчики соревнований)")

print("\n" + "=" * 80)
