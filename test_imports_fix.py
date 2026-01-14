#!/usr/bin/env python3
"""
Тестовая проверка исправлений импортов
"""

import sys

def test_notification_scheduler_imports():
    """Проверка импортов в планировщике уведомлений"""
    try:
        from notifications.notification_scheduler import (
            send_daily_reminders,
            send_weekly_reports,
            send_training_reminders,
            notification_scheduler
        )
        print("✅ Все импорты из notification_scheduler успешны")

        # Проверяем наличие правильных импортов внутри модуля
        import notifications.notification_scheduler as ns
        import inspect

        source = inspect.getsource(ns.send_weekly_reports)

        # Проверяем что старый импорт удален
        if "from reports.weekly_report_pdf import" in source:
            print("❌ ОШИБКА: Старый импорт 'reports.weekly_report_pdf' все еще присутствует!")
            return False

        # Проверяем что новый импорт есть
        if "from bot.pdf_export import create_training_pdf" in source:
            print("✅ Правильный импорт 'bot.pdf_export.create_training_pdf' найден")
        else:
            print("⚠️  ПРЕДУПРЕЖДЕНИЕ: Не найден импорт 'bot.pdf_export.create_training_pdf'")

        return True
    except Exception as e:
        print(f"❌ Ошибка импорта планировщика: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_coach_competitions_imports():
    """Проверка импортов в модуле тренера"""
    try:
        from coach.coach_competitions_handlers import router
        print("✅ Импорт coach_competitions_handlers успешен")

        # Проверяем наличие правильных импортов
        import coach.coach_competitions_handlers as cch
        import inspect

        source = inspect.getsource(cch)

        # Проверяем что старый импорт удален
        if "from utils.calendar_utils import" in source:
            print("❌ ОШИБКА: Старый импорт 'utils.calendar_utils' все еще присутствует!")
            return False

        # Проверяем что новый импорт есть
        if "from bot.calendar_keyboard import CalendarKeyboard" in source:
            print("✅ Правильный импорт 'bot.calendar_keyboard.CalendarKeyboard' найден")
        else:
            print("⚠️  ПРЕДУПРЕЖДЕНИЕ: Не найден импорт 'bot.calendar_keyboard.CalendarKeyboard'")

        return True
    except Exception as e:
        print(f"❌ Ошибка импорта модуля тренера: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pdf_export_function():
    """Проверка доступности функции генерации PDF"""
    try:
        from bot.pdf_export import create_training_pdf
        print("✅ Функция create_training_pdf доступна")

        # Проверяем что это async функция
        import inspect
        if inspect.iscoroutinefunction(create_training_pdf):
            print("✅ create_training_pdf - async функция (правильно)")
        else:
            print("⚠️  create_training_pdf - не async функция")

        return True
    except Exception as e:
        print(f"❌ Ошибка импорта create_training_pdf: {e}")
        return False

def test_calendar_keyboard():
    """Проверка модуля календаря"""
    try:
        from bot.calendar_keyboard import CalendarKeyboard
        print("✅ CalendarKeyboard импортирован")

        # Проверяем наличие методов
        methods = ['create_calendar', 'parse_callback_data', 'handle_navigation']
        for method in methods:
            if hasattr(CalendarKeyboard, method):
                print(f"  ✅ Метод {method} доступен")
            else:
                print(f"  ❌ Метод {method} отсутствует")
                return False

        return True
    except Exception as e:
        print(f"❌ Ошибка импорта CalendarKeyboard: {e}")
        return False

def main():
    print("=" * 70)
    print("ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЙ ИМПОРТОВ")
    print("=" * 70)
    print()

    results = []

    # Тест 1: Планировщик уведомлений
    print("Тест 1: Планировщик уведомлений (notification_scheduler)")
    print("-" * 70)
    results.append(test_notification_scheduler_imports())
    print()

    # Тест 2: Модуль тренера
    print("Тест 2: Модуль тренера (coach_competitions_handlers)")
    print("-" * 70)
    results.append(test_coach_competitions_imports())
    print()

    # Тест 3: Функция генерации PDF
    print("Тест 3: Функция генерации PDF (create_training_pdf)")
    print("-" * 70)
    results.append(test_pdf_export_function())
    print()

    # Тест 4: Модуль календаря
    print("Тест 4: Модуль календаря (CalendarKeyboard)")
    print("-" * 70)
    results.append(test_calendar_keyboard())
    print()

    # Итоги
    print("=" * 70)
    print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("=" * 70)
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"✅ Все тесты пройдены: {passed}/{total}")
        print()
        print("🎉 ВСЕ ИСПРАВЛЕНИЯ РАБОТАЮТ КОРРЕКТНО!")
        return 0
    else:
        print(f"❌ Провалено тестов: {total - passed}/{total}")
        print()
        print("⚠️  Некоторые исправления требуют дополнительной проверки")
        return 1

if __name__ == "__main__":
    sys.exit(main())
