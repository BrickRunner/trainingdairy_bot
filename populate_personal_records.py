"""
Populate personal records from existing competition results
"""
import asyncio
import aiosqlite
from utils.time_formatter import parse_time_to_seconds


async def populate_personal_records():
    """Создать личные рекорды из существующих результатов"""
    async with aiosqlite.connect('database.sqlite') as db:
        # Получаем все результаты с finish_time
        async with db.execute(
            """
            SELECT cp.user_id, cp.distance, cp.finish_time, cp.competition_id, c.date
            FROM competition_participants cp
            JOIN competitions c ON cp.competition_id = c.id
            WHERE cp.finish_time IS NOT NULL
            ORDER BY cp.user_id, cp.distance, c.date
            """
        ) as cursor:
            results = await cursor.fetchall()

        print(f"Found {len(results)} results with finish_time")

        # Группируем результаты по user_id и distance
        user_distance_results = {}
        for user_id, distance, finish_time, comp_id, date in results:
            key = (user_id, distance)
            if key not in user_distance_results:
                user_distance_results[key] = []
            user_distance_results[key].append((finish_time, comp_id, date))

        print(f"Processing {len(user_distance_results)} unique user-distance combinations")

        records_created = 0
        records_updated = 0

        for (user_id, distance), time_list in user_distance_results.items():
            # Находим лучшее время (минимальное количество секунд)
            best_result = None
            best_seconds = float('inf')

            for finish_time, comp_id, date in time_list:
                seconds = parse_time_to_seconds(finish_time)
                if seconds is not None and seconds < best_seconds:
                    best_seconds = seconds
                    best_result = (finish_time, comp_id, date)

            if best_result is None:
                continue

            finish_time, comp_id, date = best_result

            # Проверяем, есть ли уже рекорд
            async with db.execute(
                "SELECT id FROM personal_records WHERE user_id = ? AND distance = ?",
                (user_id, distance)
            ) as cursor:
                existing = await cursor.fetchone()

            if existing:
                # Обновляем
                await db.execute(
                    """
                    UPDATE personal_records
                    SET best_time = ?, competition_id = ?, date = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND distance = ?
                    """,
                    (finish_time, comp_id, date, user_id, distance)
                )
                records_updated += 1
            else:
                # Создаём новый
                await db.execute(
                    """
                    INSERT INTO personal_records (user_id, distance, best_time, competition_id, date)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (user_id, distance, finish_time, comp_id, date)
                )
                records_created += 1

        await db.commit()

        print(f"\n✅ DONE!")
        print(f"   Created: {records_created} records")
        print(f"   Updated: {records_updated} records")

        # Показываем созданные рекорды
        async with db.execute(
            """
            SELECT user_id, distance, best_time, date
            FROM personal_records
            ORDER BY user_id, distance
            """
        ) as cursor:
            records = await cursor.fetchall()

        print(f"\n📊 Total personal records: {len(records)}")
        for user_id, distance, best_time, date in records:
            print(f"   User {user_id}: {distance}km - {best_time} ({date})")


if __name__ == "__main__":
    asyncio.run(populate_personal_records())
