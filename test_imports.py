#!/usr/bin/env python3
"""
Тестовая проверка импортов для исправленного модуля
"""

import sys

def test_calendar_imports():
    """Проверка импорта календаря"""
    try:
        from bot.calendar_keyboard import CalendarKeyboard
        print("✅ Импорт bot.calendar_keyboard.CalendarKeyboard успешен")

        # Проверяем наличие методов
        assert hasattr(CalendarKeyboard, 'create_calendar'), "Метод create_calendar не найден"
        assert hasattr(CalendarKeyboard, 'parse_callback_data'), "Метод parse_callback_data не найден"
        assert hasattr(CalendarKeyboard, 'handle_navigation'), "Метод handle_navigation не найден"
        print("✅ Все методы CalendarKeyboard доступны")

        return True
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

def test_coach_competitions_handler():
    """Проверка импорта модуля тренера"""
    try:
        from coach import coach_competitions_handlers
        print("✅ Импорт coach.coach_competitions_handlers успешен")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта модуля тренера: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ ИМПОРТОВ ПОСЛЕ ИСПРАВЛЕНИЯ")
    print("=" * 60)
    print()

    results = []

    # Тест 1: Импорт календаря
    print("Тест 1: Проверка импорта календаря")
    results.append(test_calendar_imports())
    print()

    # Тест 2: Импорт модуля тренера
    print("Тест 2: Проверка импорта модуля тренера (coach_competitions_handlers)")
    results.append(test_coach_competitions_handler())
    print()

    # Итоги
    print("=" * 60)
    print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"✅ Все тесты пройдены: {passed}/{total}")
        return 0
    else:
        print(f"❌ Провалено тестов: {total - passed}/{total}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
