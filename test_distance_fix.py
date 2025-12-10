"""
Тест исправления конвертации дистанций
"""
from utils.unit_converter import convert_distance_name, safe_convert_distance_name

# Тестируем проблемные случаи
test_cases = [
    ("10 км", "мили", "Должно быть: 6.2 мили"),
    ("21,0 км", "мили", "Должно быть: 13.1 мили (не 21,0.6)"),
    ("10,34 км", "мили", "Должно быть: 6.4 мили (не 10,34.2)"),
    ("500м плавание", "мили", "Должно быть: 547 ярдов плавание (не ярдоиля)"),
    ("500м плавание + 3000м бег", "мили", "Должно быть с пробелами"),
    ("5 км", "мили", "Должно быть: 3.1 мили"),
    ("42.195 км", "мили", "Должно быть: 26.2 мили"),
]

print("Testing problematic distance conversions:")
print("=" * 70)

all_passed = True
for distance_name, target_unit, expected in test_cases:
    result = safe_convert_distance_name(distance_name, target_unit)
    print(f"Input:    '{distance_name}' -> {target_unit}")
    print(f"Output:   '{result}'")
    print(f"Expected: {expected}")

    # Проверяем что нет проблем
    has_issues = False
    if "," in result and "." in result:
        print("  [WARNING] Contains both comma and dot!")
        has_issues = True
        all_passed = False
    if "ярдо" in result and "иля" in result:
        print("  [WARNING] Contains word merge!")
        has_issues = True
        all_passed = False
    if not has_issues:
        print("  [OK]")

    print("-" * 70)

if all_passed:
    print("\n[SUCCESS] All tests passed!")
else:
    print("\n[FAILED] Some tests failed!")
