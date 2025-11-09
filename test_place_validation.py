"""
Демонстрация валидации места в возрастной категории
"""

def validate_place_age(place_overall, place_age):
    """
    Проверить, что место в возрастной категории корректно

    Args:
        place_overall: Место в общем зачёте (может быть None)
        place_age: Место в возрастной категории

    Returns:
        tuple: (is_valid, error_message)
    """
    if place_age <= 0:
        return False, "Место должно быть положительным числом"

    if place_overall is not None and place_age > place_overall:
        return False, (
            f"Место в возрастной категории ({place_age}) не может быть больше "
            f"места в общем зачёте ({place_overall})"
        )

    return True, None


def test_validation():
    """Тестирование различных сценариев"""

    print("="*70)
    print("ТЕСТИРОВАНИЕ ВАЛИДАЦИИ МЕСТА В ВОЗРАСТНОЙ КАТЕГОРИИ")
    print("="*70)
    print()

    test_cases = [
        # (place_overall, place_age, expected_valid, description)
        (10, 5, True, "Место в категории меньше общего - OK"),
        (10, 10, True, "Место в категории равно общему - OK"),
        (10, 15, False, "Место в категории больше общего - ОШИБКА"),
        (None, 5, True, "Общее место не указано - OK"),
        (5, 1, True, "Место в категории 1, общее 5 - OK"),
        (1, 1, True, "Оба места = 1 - OK"),
        (1, 2, False, "Место в категории 2, общее 1 - ОШИБКА"),
        (100, 50, True, "Место в категории 50, общее 100 - OK"),
        (50, 100, False, "Место в категории 100, общее 50 - ОШИБКА"),
    ]

    for i, (place_overall, place_age, expected_valid, description) in enumerate(test_cases, 1):
        is_valid, error = validate_place_age(place_overall, place_age)

        status = "PASS" if is_valid == expected_valid else "FAIL"
        symbol = "[OK]" if is_valid == expected_valid else "[X]"

        print(f"{i}. {description}")
        print(f"   Overall: {place_overall}, Age category: {place_age}")
        print(f"   Result: {symbol} {status}")

        if not is_valid:
            print(f"   Error: {error}")

        if is_valid != expected_valid:
            print(f"   [!] TEST FAILED! Expected: {'valid' if expected_valid else 'invalid'}")

        print()

    print("="*70)
    print("ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ В БОТЕ")
    print("="*70)
    print()
    print("Сценарий 1: Пользователь занял 10 место в общем зачёте")
    print("  - Вводит место в категории: 5 → ✓ Принято")
    print("  - Вводит место в категории: 10 → ✓ Принято")
    print("  - Вводит место в категории: 15 → ✗ Ошибка!")
    print("    'Место в возрастной категории (15) не может быть больше")
    print("     места в общем зачёте (10)'")
    print()
    print("Сценарий 2: Пользователь пропустил место в общем зачёте")
    print("  - Вводит место в категории: 5 → ✓ Принято (валидация пропущена)")
    print()
    print("Сценарий 3: Пользователь занял 1 место в общем зачёте")
    print("  - Вводит место в категории: 1 → ✓ Принято")
    print("  - Вводит место в категории: 2 → ✗ Ошибка!")
    print()
    print("="*70)


if __name__ == "__main__":
    test_validation()
