"""
Скрипт для обновления разрядов для существующих результатов соревнований и личных рекордов
"""

import asyncio
import sys
import os
import io

# Устанавливаем UTF-8 кодировку для вывода на Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aiosqlite
from utils.qualifications import get_qualification, time_to_seconds


async def update_competition_qualifications():
    """
    Обновить разряды для всех результатов соревнований
    """
    db_path = 'trainingdiary.db'

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row

        # Получаем все завершенные соревнования
        async with db.execute(
            """
            SELECT
                cp.id,
                cp.user_id,
                cp.competition_id,
                cp.distance,
                cp.finish_time,
                c.sport_type,
                us.gender
            FROM competition_participants cp
            JOIN competitions c ON cp.competition_id = c.id
            LEFT JOIN user_settings us ON us.user_id = cp.user_id
            WHERE cp.status = 'finished' AND cp.finish_time IS NOT NULL
            """
        ) as cursor:
            rows = await cursor.fetchall()

        print(f"Найдено {len(rows)} результатов для обновления")

        updated_count = 0
        skipped_count = 0

        for row in rows:
            participant_id = row['id']
            user_id = row['user_id']
            distance = row['distance']
            finish_time = row['finish_time']
            sport_type = row['sport_type'] or 'бег'
            gender = row['gender'] or 'male'

            try:
                # Рассчитываем разряд
                time_sec = time_to_seconds(finish_time)
                qualification = get_qualification(sport_type, distance, time_sec, gender)

                if qualification:
                    # Обновляем разряд в БД
                    await db.execute(
                        """
                        UPDATE competition_participants
                        SET qualification = ?
                        WHERE id = ?
                        """,
                        (qualification, participant_id)
                    )
                    print(f"  Пользователь {user_id}, дистанция {distance} км, время {finish_time} -> {qualification}")
                    updated_count += 1
                else:
                    skipped_count += 1

            except Exception as e:
                print(f"  Ошибка для пользователя {user_id}, дистанция {distance} км: {e}")
                skipped_count += 1

        await db.commit()

        print(f"\nОбновлено разрядов в соревнованиях: {updated_count}")
        print(f"Пропущено: {skipped_count}")

        return updated_count


async def update_personal_records_qualifications():
    """
    Обновить разряды для всех личных рекордов
    """
    db_path = 'trainingdiary.db'

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row

        # Получаем все личные рекорды
        async with db.execute(
            """
            SELECT
                pr.id,
                pr.user_id,
                pr.distance,
                pr.best_time,
                pr.competition_id,
                us.gender
            FROM personal_records pr
            LEFT JOIN user_settings us ON us.user_id = pr.user_id
            """
        ) as cursor:
            rows = await cursor.fetchall()

        print(f"\nНайдено {len(rows)} личных рекордов для обновления")

        updated_count = 0
        skipped_count = 0

        for row in rows:
            record_id = row['id']
            user_id = row['user_id']
            distance = row['distance']
            best_time = row['best_time']
            competition_id = row['competition_id']
            gender = row['gender'] or 'male'

            # Получаем тип спорта из соревнования
            sport_type = 'бег'  # По умолчанию
            if competition_id:
                async with db.execute(
                    "SELECT sport_type FROM competitions WHERE id = ?",
                    (competition_id,)
                ) as comp_cursor:
                    comp_row = await comp_cursor.fetchone()
                    if comp_row and comp_row['sport_type']:
                        sport_type = comp_row['sport_type']

            try:
                # Рассчитываем разряд
                time_sec = time_to_seconds(best_time)
                qualification = get_qualification(sport_type, distance, time_sec, gender)

                if qualification:
                    # Обновляем разряд в БД
                    await db.execute(
                        """
                        UPDATE personal_records
                        SET qualification = ?
                        WHERE id = ?
                        """,
                        (qualification, record_id)
                    )
                    print(f"  Пользователь {user_id}, дистанция {distance} км, время {best_time} -> {qualification}")
                    updated_count += 1
                else:
                    skipped_count += 1

            except Exception as e:
                print(f"  Ошибка для пользователя {user_id}, дистанция {distance} км: {e}")
                skipped_count += 1

        await db.commit()

        print(f"\nОбновлено разрядов в личных рекордах: {updated_count}")
        print(f"Пропущено: {skipped_count}")

        return updated_count


async def main():
    """
    Основная функция
    """
    print("=" * 60)
    print("Обновление разрядов для существующих результатов")
    print("=" * 60)

    # Проверяем существование базы данных
    if not os.path.exists('trainingdiary.db'):
        print("\n⚠️ База данных trainingdiary.db не найдена")
        print("\n📝 Это нормально, если бот еще не запускался.")
        print("   База данных будет создана при первом запуске бота.")
        print("\n💡 Что делать:")
        print("   1. Запустите бота: python main.py")
        print("   2. Зарегистрируйтесь и добавьте результаты соревнований")
        print("   3. Снова запустите этот скрипт для обновления разрядов")
        print("\n✅ Для новых результатов разряды будут рассчитываться автоматически!")
        return

    try:
        # Проверяем наличие таблиц
        async with aiosqlite.connect('trainingdiary.db') as db:
            async with db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='competition_participants'"
            ) as cursor:
                if not await cursor.fetchone():
                    print("\n⚠️ Таблица competition_participants не найдена в базе данных")
                    print("\n📝 База данных существует, но еще не инициализирована.")
                    print("   Таблицы будут созданы при первом запуске бота.")
                    print("\n💡 Запустите бота: python main.py")
                    print("✅ Для новых результатов разряды будут рассчитываться автоматически!")
                    return

        # Обновляем разряды в соревнованиях
        comp_count = await update_competition_qualifications()

        # Обновляем разряды в личных рекордах
        records_count = await update_personal_records_qualifications()

        print("\n" + "=" * 60)
        print(f"✅ Всего обновлено: {comp_count + records_count}")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Ошибка при выполнении скрипта: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
