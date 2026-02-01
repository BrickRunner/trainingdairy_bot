"""
Проверка существующих соревнований в БД.
"""
import asyncio
import aiosqlite


async def check_competitions():
    """Проверка соревнований в БД"""
    try:
        async with aiosqlite.connect('database.sqlite') as db:
            db.row_factory = aiosqlite.Row

            # Проверяем все соревнования
            print("=" * 60)
            print("ПРОВЕРКА ВСЕХ СОРЕВНОВАНИЙ В БД:")
            print("=" * 60)

            async with db.execute(
                """
                SELECT COUNT(*) as cnt, sport_type
                FROM competitions
                GROUP BY sport_type
                """
            ) as cursor:
                rows = await cursor.fetchall()
                print("\nРаспределение по sport_type:")
                for row in rows:
                    print(f"  {row['sport_type']}: {row['cnt']} соревнований")

            # Проверяем соревнования с результатами
            print("\n" + "=" * 60)
            print("СОРЕВНОВАНИЯ С РЕЗУЛЬТАТАМИ:")
            print("=" * 60)

            async with db.execute(
                """
                SELECT DISTINCT c.id, c.name, c.sport_type, c.organizer
                FROM competitions c
                JOIN competition_participants cp ON cp.competition_id = c.id
                WHERE cp.finish_time IS NOT NULL
                ORDER BY c.id DESC
                LIMIT 20
                """
            ) as cursor:
                rows = await cursor.fetchall()
                if rows:
                    print(f"\nПоследние 20 соревнований с результатами:")
                    for row in rows:
                        print(f"  ID {row['id']}: {row['name']}")
                        print(f"    sport_type: {row['sport_type']}")
                        print(f"    organizer: {row['organizer']}")
                        print()
                else:
                    print("  Нет соревнований с результатами")

            # Ищем соревнования по названию (плавание/велоспорт)
            print("=" * 60)
            print("ПОИСК СОРЕВНОВАНИЙ ПО КЛЮЧЕВЫМ СЛОВАМ:")
            print("=" * 60)

            keywords = ['плав', 'велос', 'bike', 'swim', 'cycling', 'триатлон']
            for keyword in keywords:
                async with db.execute(
                    f"""
                    SELECT id, name, sport_type, organizer
                    FROM competitions
                    WHERE name LIKE '%{keyword}%' OR organizer LIKE '%{keyword}%'
                    LIMIT 5
                    """
                ) as cursor:
                    rows = await cursor.fetchall()
                    if rows:
                        print(f"\n'{keyword}':")
                        for row in rows:
                            print(f"  ID {row['id']}: {row['name']}, sport_type={row['sport_type']}")

    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_competitions())
