"""
Тест конвертации дистанций
"""
from utils.unit_converter import convert_distance_name, safe_convert_distance_name

# Тестируем различные форматы
test_cases = [
    ("10 км", "мили"),
    ("5 км", "мили"),
    ("500м плавание + 3000м бег", "мили"),
    ("42.195 км", "мили"),
    ("21.1 км", "мили"),
    ("1.5 км", "мили"),
]

print("Testing distance conversions:")
print("=" * 60)

for distance_name, target_unit in test_cases:
    result = safe_convert_distance_name(distance_name, target_unit)
    print(f"Input:  {distance_name} (to {target_unit})")
    print(f"Output: {result}")
    print("-" * 60)

print("\nAll tests completed!")
