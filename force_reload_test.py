"""
Тест принудительной перезагрузки модулей
"""
import sys
import importlib

print("=" * 70)
print("ТЕСТ ПРИНУДИТЕЛЬНОЙ ПЕРЕЗАГРУЗКИ МОДУЛЕЙ")
print("=" * 70)

# Удаляем модули из кэша
modules_to_reload = [
    'bot.fsm',
    'competitions.competitions_handlers',
    'competitions.competitions_queries',
    'utils.time_formatter'
]

print("\n1. Удаление модулей из sys.modules...")
for module_name in modules_to_reload:
    if module_name in sys.modules:
        print(f"   Удаляю: {module_name}")
        del sys.modules[module_name]
    else:
        print(f"   Не загружен: {module_name}")

# Импортируем заново
print("\n2. Импорт модулей заново...")
from bot.fsm import CompetitionStates
from competitions import competitions_handlers
from competitions.competitions_queries import add_competition_result
import utils.time_formatter as time_formatter

print("   [OK] Модули импортированы")

# Проверяем FSM состояния
print("\n3. Проверка FSM состояний...")
states = ['waiting_for_finish_time', 'waiting_for_place_overall',
          'waiting_for_place_age', 'waiting_for_heart_rate']

for state in states:
    if hasattr(CompetitionStates, state):
        print(f"   [OK] {state}")
    else:
        print(f"   [FAIL] {state}")

# Проверяем обработчики
print("\n4. Проверка обработчиков...")
handlers = ['start_add_result', 'process_finish_time',
            'process_place_overall', 'process_place_age_category',
            'process_heart_rate']

for handler in handlers:
    if hasattr(competitions_handlers, handler):
        print(f"   [OK] {handler}")
    else:
        print(f"   [FAIL] {handler}")

# Проверяем сигнатуру add_competition_result
print("\n5. Проверка add_competition_result...")
import inspect
sig = inspect.signature(add_competition_result)
params = list(sig.parameters.keys())
print(f"   Параметры: {params}")

if 'heart_rate' in params:
    print("   [OK] heart_rate присутствует в параметрах")
else:
    print("   [FAIL] heart_rate ОТСУТСТВУЕТ в параметрах")

# Проверяем поддержку сотых
print("\n6. Проверка поддержки сотых долей...")
test_times = ["01:23:45.50", "42:30.25", "1:23:45"]
for test_time in test_times:
    is_valid = time_formatter.validate_time_format(test_time)
    normalized = time_formatter.normalize_time(test_time)
    print(f"   {test_time:15} -> {normalized:15} (valid: {is_valid})")

print("\n" + "=" * 70)
print("ТЕСТ ЗАВЕРШЕН")
print("=" * 70)
