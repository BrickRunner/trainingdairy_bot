import asyncio
import aiosqlite


async def check_cycling_standards():
    """Проверка наличия данных в таблице cycling_standards"""
    try:
        async with aiosqlite.connect('database.sqlite') as db:
            db.row_factory = aiosqlite.Row

            # Проверяем количество записей
            async with db.execute('SELECT COUNT(*) as cnt FROM cycling_standards') as cursor:
                row = await cursor.fetchone()
                count = row['cnt']
                print(f"Всего записей в cycling_standards: {count}")

            # Проверяем данные для индивидуальной гонки
            print("\nПроверяем наличие дисциплины 'индивидуальная гонка':")
            async with db.execute(
                """
                SELECT distance, gender, discipline, rank, time_seconds, version
                FROM cycling_standards
                WHERE discipline = 'индивидуальная гонка'
                ORDER BY distance, gender, rank
                LIMIT 10
                """
            ) as cursor:
                rows = await cursor.fetchall()
                if rows:
                    print(f"[OK] Найдено {len(rows)} записей для 'индивидуальная гонка':")
                    for row in rows:
                        print(f"  {row['distance']} км, {row['gender']}, {row['rank']}: {row['time_seconds']} сек")
                else:
                    print("[WARN] Нет данных для 'индивидуальная гонка'!")

            # Проверяем swimming_standards
            print("\n" + "="*60)
            print("Проверка swimming_standards:")
            async with db.execute('SELECT COUNT(*) as cnt FROM swimming_standards') as cursor:
                row = await cursor.fetchone()
                count = row['cnt']
                print(f"Всего записей в swimming_standards: {count}")

            # Проверяем данные для бассейна 50м
            async with db.execute(
                """
                SELECT distance, gender, pool_length, rank, time_seconds
                FROM swimming_standards
                WHERE pool_length = 50
                ORDER BY distance, gender, rank
                LIMIT 10
                """
            ) as cursor:
                rows = await cursor.fetchall()
                if rows:
                    print(f"\n[OK] Примеры данных для бассейна 50м:")
                    for row in rows:
                        print(f"  {row['distance']} км, {row['gender']}, {row['rank']}: {row['time_seconds']} сек")
                else:
                    print("\n[WARN] Нет данных для бассейна 50м!")

            # Проверяем уникальные дисциплины
            async with db.execute('SELECT DISTINCT discipline FROM cycling_standards') as cursor:
                rows = await cursor.fetchall()
                print(f"\nДоступные дисциплины:")
                for row in rows:
                    print(f"  - {row[0]}")

    except Exception as e:
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(check_cycling_standards())
