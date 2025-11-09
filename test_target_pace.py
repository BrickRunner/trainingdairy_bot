"""Тест отображения целевого темпа"""
import asyncio
from utils.time_formatter import calculate_pace_with_unit

async def test_pace():
    # Тестируем функцию расчета темпа
    print("Тест 1: Время 3:30:00 на 42.195 км")
    pace = await calculate_pace_with_unit("3:30:00", 42.195, 1)
    print(f"Результат: {pace}")
    print()

    print("Тест 2: Время 1:45:00 на 21.1 км")
    pace = await calculate_pace_with_unit("1:45:00", 21.1, 1)
    print(f"Результат: {pace}")
    print()

    print("Тест 3: Время 00:45:00 на 10 км")
    pace = await calculate_pace_with_unit("00:45:00", 10.0, 1)
    print(f"Результат: {pace}")
    print()

    print("Тест 4: Проверка с None")
    pace = await calculate_pace_with_unit(None, 10.0, 1)
    print(f"Результат: {pace}")
    print()

    print("Тест 5: Проверка с пустой строкой")
    pace = await calculate_pace_with_unit("", 10.0, 1)
    print(f"Результат: {pace}")

if __name__ == "__main__":
    asyncio.run(test_pace())
