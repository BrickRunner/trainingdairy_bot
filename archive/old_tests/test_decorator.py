"""
Тест - выполняются ли декораторы
"""
import sys

print("Импортируем competitions_handlers...")

# Принудительно удаляем из кэша
if 'competitions.competitions_handlers' in sys.modules:
    del sys.modules['competitions.competitions_handlers']
if 'competitions' in sys.modules:
    del sys.modules['competitions']

from competitions import competitions_handlers

print(f"Модуль импортирован: {competitions_handlers}")
print(f"Роутер: {competitions_handlers.router}")
print(f"Обработчиков в роутере: {len(competitions_handlers.router.observers)}")

# Проверяем конкретно наши обработчики
print("\nПроверка наших обработчиков:")

# Получаем все handlers из модуля
import inspect

all_functions = [name for name, obj in inspect.getmembers(competitions_handlers)
                if inspect.isfunction(obj) or inspect.iscoroutinefunction(obj)]

our_handlers = [
    'start_add_result',
    'process_finish_time',
    'process_place_overall',
    'process_place_age_category',
    'process_heart_rate'
]

print(f"\nВсего функций в модуле: {len(all_functions)}")
print(f"Наши обработчики:")
for handler in our_handlers:
    exists = handler in all_functions
    print(f"  {handler}: {'[EXISTS]' if exists else '[MISSING]'}")

# Проверяем декораторы
print("\nПроверка декораторов:")
for handler_name in our_handlers:
    if hasattr(competitions_handlers, handler_name):
        handler_func = getattr(competitions_handlers, handler_name)
        # Проверяем есть ли у функции атрибуты aiogram
        has_decorator = hasattr(handler_func, '__wrapped__')
        print(f"  {handler_name}: decorator={'[YES]' if has_decorator else '[NO]'}")

# Смотрим что в роутере
print(f"\nОбработчики в роутере:")
for idx, observer in enumerate(competitions_handlers.router.observers[:5], 1):
    if hasattr(observer, 'callback'):
        callback = observer.callback
        name = getattr(callback, '__name__', 'unknown')
        print(f"  {idx}. {name}")

print("\nВЫВОД:")
if len(competitions_handlers.router.observers) > 0:
    print("  Роутер содержит обработчики")
    print("  Декораторы ВЫПОЛНИЛИСЬ при импорте")
else:
    print("  Роутер ПУСТОЙ")
    print("  Декораторы НЕ ВЫПОЛНИЛИСЬ")
