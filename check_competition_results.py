"""
Проверка записей результатов соревнований по плаванию и велоспорту в БД.
"""
import asyncio
import aiosqlite


async def check_competition_results():
    """Проверка записей с результатами"""
    try:
        async with aiosqlite.connect('database.sqlite') as db:
            db.row_factory = aiosqlite.Row

            # Проверяем записи по плаванию
            print("=" * 60)
            print("Записи результатов по ПЛАВАНИЮ:")
            print("=" * 60)
            async with db.execute(
                """
                SELECT
                    cp.user_id,
                    cp.competition_id,
                    c.name as comp_name,
                    c.sport_type,
                    cp.distance,
                    cp.finish_time,
                    cp.qualification,
                    us.gender
                FROM competition_participants cp
                JOIN competitions c ON c.id = cp.competition_id
                LEFT JOIN user_settings us ON us.user_id = cp.user_id
                WHERE c.sport_type LIKE '%плав%'
                  AND cp.finish_time IS NOT NULL
                LIMIT 10
                """
            ) as cursor:
                rows = await cursor.fetchall()
                if rows:
                    print(f"\nНайдено {len(rows)} записей:")
                    for row in rows:
                        print(f"  User {row['user_id']}, {row['comp_name']}")
                        print(f"    Дистанция: {row['distance']} км")
                        print(f"    Время: {row['finish_time']}")
                        print(f"    Разряд: {row['qualification']}")
                        print(f"    Пол: {row['gender']}")
                        print()
                else:
                    print("  Записей не найдено")

            # Проверяем записи по велоспорту
            print("=" * 60)
            print("Записи результатов по ВЕЛОСПОРТУ:")
            print("=" * 60)
            async with db.execute(
                """
                SELECT
                    cp.user_id,
                    cp.competition_id,
                    c.name as comp_name,
                    c.sport_type,
                    cp.distance,
                    cp.finish_time,
                    cp.qualification,
                    us.gender
                FROM competition_participants cp
                JOIN competitions c ON c.id = cp.competition_id
                LEFT JOIN user_settings us ON us.user_id = cp.user_id
                WHERE c.sport_type LIKE '%велос%'
                  AND cp.finish_time IS NOT NULL
                LIMIT 10
                """
            ) as cursor:
                rows = await cursor.fetchall()
                if rows:
                    print(f"\nНайдено {len(rows)} записей:")
                    for row in rows:
                        print(f"  User {row['user_id']}, {row['comp_name']}")
                        print(f"    Дистанция: {row['distance']} км")
                        print(f"    Время: {row['finish_time']}")
                        print(f"    Разряд: {row['qualification']}")
                        print(f"    Пол: {row['gender']}")
                        print()
                else:
                    print("  Записей не найдено")

            # Общая статистика
            print("=" * 60)
            print("ОБЩАЯ СТАТИСТИКА:")
            print("=" * 60)

            async with db.execute(
                """
                SELECT
                    c.sport_type,
                    COUNT(*) as total,
                    COUNT(cp.finish_time) as with_results,
                    COUNT(CASE WHEN cp.qualification = 'Нет разряда' OR cp.qualification IS NULL THEN 1 END) as no_rank
                FROM competition_participants cp
                JOIN competitions c ON c.id = cp.competition_id
                WHERE c.sport_type LIKE '%плав%' OR c.sport_type LIKE '%велос%'
                GROUP BY c.sport_type
                """
            ) as cursor:
                rows = await cursor.fetchall()
                for row in rows:
                    print(f"\n{row['sport_type']}:")
                    print(f"  Всего участников: {row['total']}")
                    print(f"  С результатами: {row['with_results']}")
                    print(f"  Без разряда/NULL: {row['no_rank']}")

    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_competition_results())
