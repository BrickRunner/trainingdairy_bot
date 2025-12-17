"""
Тест проверки обработки None в distance_km
"""

# Симуляция проблемного кода (старая версия)
def test_old_version():
    """Это вызовет ошибку"""
    distance_km = None  # Может прийти из API
    try:
        # Старый код - вызывает ошибку
        selected_distance = distance_km if distance_km > 0 else None
        print("❌ Старый код не должен был работать!")
    except TypeError as e:
        print(f"✅ Ожидаемая ошибка в старом коде: {e}")

# Симуляция исправленного кода
def test_new_version():
    """Это должно работать"""
    distance_km = None  # Может прийти из API

    # Новый код - проверяет на None перед сравнением
    if distance_km is not None and distance_km > 0:
        selected_distance = distance_km
    else:
        selected_distance = None

    print(f"✅ Новый код работает: selected_distance = {selected_distance}")

# Тест с разными значениями
def test_different_values():
    """Проверяем разные значения"""
    test_cases = [
        (None, None, "None должен превратиться в None"),
        (0, None, "0 должен превратиться в None"),
        (-5, None, "Отрицательное должно превратиться в None"),
        (5, 5, "Положительное должно остаться как есть"),
        (42.195, 42.195, "Дробное положительное должно остаться"),
    ]

    print("\nПроверка разных значений:")
    all_ok = True
    for distance_km, expected, description in test_cases:
        if distance_km is not None and distance_km > 0:
            selected_distance = distance_km
        else:
            selected_distance = None

        if selected_distance == expected:
            print(f"  ✅ {description}: {distance_km} → {selected_distance}")
        else:
            print(f"  ❌ {description}: {distance_km} → {selected_distance} (ожидалось {expected})")
            all_ok = False

    return all_ok

if __name__ == "__main__":
    print("="*60)
    print("ТЕСТ ОБРАБОТКИ None В distance_km")
    print("="*60)

    print("\n1. Тест старого кода (должен вызвать ошибку):")
    test_old_version()

    print("\n2. Тест нового кода (должен работать):")
    test_new_version()

    print("\n3. Тест разных значений:")
    if test_different_values():
        print("\n✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ")
    else:
        print("\n❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ")

    print("="*60)
