"""
Тест проверки sport_type
"""
sport_type = "пла"

print(f"Sport type: '{sport_type}'")
print(f"Lower: '{sport_type.lower()}'")
print(f"Starts with 'пла': {sport_type.lower().startswith('пла')}")
print(f"'плав' in lower: {'плав' in sport_type.lower()}")

# Проверим байты
print(f"\nБайты sport_type: {sport_type.encode('utf-8')}")
print(f"Байты 'пла': {'пла'.encode('utf-8')}")

# Проверим прямое сравнение
if sport_type.lower().startswith('пла'):
    print("\nПРОВЕРКА ПРОШЛА!")
    pool_length = 50
    print(f"pool_length = {pool_length}")
else:
    print("\nПРОВЕРКА НЕ ПРОШЛА!")
