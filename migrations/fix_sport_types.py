"""
Миграция: Обновление sport_type для существующих соревнований и пересчет разрядов.

Логика определения sport_type:
- Плавание: дистанции < 2 км (50м, 100м, 200м, 400м, 800м, 1500м)
- Велоспорт: дистанции > 5 км и <= 200 км
- Бег: все остальное
"""
import asyncio
import aiosqlite
import os
import sys

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.qualifications import get_qualification_async, time_to_seconds


DB_PATH = os.getenv('DB_PATH', 'database.sqlite')


async def detect_sport_type(distances, name, organizer):
    """
    Определяет тип спорта на основе дистанций и названия.

    Args:
        distances: JSON строка с дистанциями или список
        name: Название соревнования
        organizer: Организатор

    Returns:
        Тип спорта: 'плавание', 'велоспорт', 'триатлон' или 'бег'
    """
    # Проверяем название
    name_lower = (name or '').lower()
    organizer_lower = (organizer or '').lower()

    if any(keyword in name_lower or keyword in organizer_lower
           for keyword in ['плав', 'swim', 'бассейн', 'pool']):
        return 'плавание'

    if any(keyword in name_lower or keyword in organizer_lower
           for keyword in ['велос', 'bike', 'cycling', 'вело']):
        return 'велоспорт'

    if any(keyword in name_lower or keyword in organizer_lower
           for keyword in ['триатлон', 'triathlon', 'акватлон', 'дуатлон']):
        return 'триатлон'

    # Проверяем дистанции
    if isinstance(distances, str):
        import json
        try:
            distances = json.loads(distances)
        except:
            distances = []

    if not distances or not isinstance(distances, list):
        return 'бег'

    # Плавание: все дистанции < 2 км
    if distances and all(float(d) < 2.0 for d in distances if isinstance(d, (int, float)) or (isinstance(d, str) and d.replace('.', '').isdigit())):
        return 'плавание'

    # Велоспорт: дистанции от 5 до 200 км
    if distances and all(5.0 <= float(d) <= 200.0 for d in distances if isinstance(d, (int, float)) or (isinstance(d, str) and d.replace('.', '').isdigit())):
        # Но не марафон/полумарафон
        if not any(float(d) in [21.1, 42.195, 42.2] for d in distances if isinstance(d, (int, float)) or (isinstance(d, str) and d.replace('.', '').isdigit())):
            return 'велоспорт'

    return 'бег'


async def update_sport_types():
    """Обновляет sport_type для всех соревнований в БД"""
    print("=" * 60)
    print("ОБНОВЛЕНИЕ SPORT_TYPE ДЛЯ СОРЕВНОВАНИЙ")
    print("=" * 60)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Получаем все соревнования
        async with db.execute(
            "SELECT id, name, distances, organizer, sport_type FROM competitions"
        ) as cursor:
            competitions = await cursor.fetchall()

        updated_count = 0
        for comp in competitions:
            # Определяем правильный sport_type
            new_sport_type = await detect_sport_type(
                comp['distances'],
                comp['name'],
                comp['organizer']
            )

            # Обновляем если изменился
            if comp['sport_type'] != new_sport_type:
                await db.execute(
                    "UPDATE competitions SET sport_type = ? WHERE id = ?",
                    (new_sport_type, comp['id'])
                )
                print(f"ID {comp['id']}: {comp['name']}")
                print(f"  {comp['sport_type']} -> {new_sport_type}")
                updated_count += 1

        await db.commit()
        print(f"\nОбновлено соревнований: {updated_count}")


async def recalculate_qualifications():
    """Пересчитывает разряды для существующих результатов"""
    print("\n" + "=" * 60)
    print("ПЕРЕСЧЕТ РАЗРЯДОВ ДЛЯ СУЩЕСТВУЮЩИХ РЕЗУЛЬТАТОВ")
    print("=" * 60)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Получаем все результаты
        async with db.execute(
            """
            SELECT
                cp.id,
                cp.user_id,
                cp.competition_id,
                cp.distance,
                cp.finish_time,
                cp.qualification as old_qualification,
                c.sport_type,
                us.gender
            FROM competition_participants cp
            JOIN competitions c ON c.id = cp.competition_id
            LEFT JOIN user_settings us ON us.user_id = cp.user_id
            WHERE cp.finish_time IS NOT NULL
            """
        ) as cursor:
            results = await cursor.fetchall()

        updated_count = 0
        for result in results:
            try:
                # Рассчитываем новый разряд
                time_seconds = time_to_seconds(result['finish_time'])
                gender = result['gender'] or 'male'
                sport_type = result['sport_type'] or 'бег'

                kwargs = {}
                if 'плав' in sport_type.lower():
                    kwargs['pool_length'] = 50
                elif 'велос' in sport_type.lower():
                    kwargs['discipline'] = 'индивидуальная гонка'

                new_qualification = await get_qualification_async(
                    sport_type,
                    result['distance'],
                    time_seconds,
                    gender,
                    **kwargs
                )

                # Обновляем если изменился
                if new_qualification and new_qualification != result['old_qualification']:
                    await db.execute(
                        "UPDATE competition_participants SET qualification = ? WHERE id = ?",
                        (new_qualification, result['id'])
                    )
                    print(f"User {result['user_id']}, Comp {result['competition_id']}, {result['distance']}км")
                    print(f"  {result['old_qualification']} -> {new_qualification} ({sport_type})")
                    updated_count += 1

            except Exception as e:
                print(f"Ошибка для результата ID {result['id']}: {e}")

        await db.commit()
        print(f"\nОбновлено результатов: {updated_count}")


async def main():
    """Запуск миграции"""
    print("МИГРАЦИЯ: Исправление sport_type и пересчет разрядов")
    print("=" * 60)

    # Шаг 1: Обновляем sport_type
    await update_sport_types()

    # Шаг 2: Пересчитываем разряды
    await recalculate_qualifications()

    print("\n" + "=" * 60)
    print("МИГРАЦИЯ ЗАВЕРШЕНА")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
