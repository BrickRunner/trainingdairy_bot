"""
Тест для проверки исправления отображения разрядов для плавания и велоспорта
"""
import asyncio
from utils.qualifications import get_qualification_async, time_to_seconds

async def test_swimming():
    """Тест расчета разрядов по плаванию"""
    print("=== Тест: Плавание ===")

    # Тест 1: 100м за 56.70 секунд (мужчины) - должен быть I разряд
    distance_km = 0.1
    time_seconds = time_to_seconds("0:56.70")
    gender = 'male'

    qual = await get_qualification_async('плавание', distance_km, time_seconds, gender, pool_length=50)
    print(f"100м, 56.70с, мужчины, бассейн 50м: {qual} (ожидается: I)")

    # Тест 2: 50м за 26.84 секунды (мужчины) - должен быть II разряд
    distance_km = 0.05
    time_seconds = time_to_seconds("0:26.84")

    qual = await get_qualification_async('плавание', distance_km, time_seconds, gender, pool_length=50)
    print(f"50м, 26.84с, мужчины, бассейн 50м: {qual} (ожидается: II)")

    print()

async def test_cycling():
    """Тест расчета разрядов по велоспорту"""
    print("=== Тест: Велоспорт ===")

    # Тест 1: 5км за 17:00 (мужчины) - нужно проверить, есть ли норматив
    distance_km = 5.0
    time_seconds = time_to_seconds("17:00")
    gender = 'male'

    qual = await get_qualification_async('велоспорт', distance_km, time_seconds, gender, discipline='индивидуальная гонка')
    print(f"5км, 17:00, мужчины, индивидуальная гонка: {qual}")

    # Тест 2: 50км за 1:12:30 (мужчины) - должен быть I разряд
    distance_km = 50.0
    time_seconds = time_to_seconds("1:12:30")

    qual = await get_qualification_async('велоспорт', distance_km, time_seconds, gender, discipline='индивидуальная гонка')
    print(f"50км, 1:12:30, мужчины, индивидуальная гонка: {qual} (ожидается: I)")

    # Тест 3: 50км за 1:15:38 (мужчины) - должен быть I разряд
    time_seconds = time_to_seconds("1:15:38")

    qual = await get_qualification_async('велоспорт', distance_km, time_seconds, gender, discipline='индивидуальная гонка')
    print(f"50км, 1:15:38, мужчины, индивидуальная гонка: {qual} (ожидается: I)")

    print()

async def test_old_vs_new():
    """Сравнение старой и новой функции"""
    print("=== Сравнение старой и новой функции ===")

    from utils.qualifications import get_qualification

    # Велоспорт - старая функция возвращает None
    distance_km = 50.0
    time_seconds = time_to_seconds("1:12:30")
    gender = 'male'

    old_qual = get_qualification('велоспорт', distance_km, time_seconds, gender)
    new_qual = await get_qualification_async('велоспорт', distance_km, time_seconds, gender, discipline='индивидуальная гонка')

    print(f"Велоспорт 50км, 1:12:30:")
    print(f"  Старая функция (get_qualification): {old_qual}")
    print(f"  Новая функция (get_qualification_async): {new_qual}")

    print()

async def main():
    await test_swimming()
    await test_cycling()
    await test_old_vs_new()
    print("✅ Тестирование завершено!")

if __name__ == '__main__':
    asyncio.run(main())
