"""
Проверка структуры БД и данных по соревнованиям
"""
import asyncio
import aiosqlite
import os

async def check_db():
    db_path = os.getenv('DB_PATH', 'bot_data.db')
    print(f"Проверка БД: {db_path}\n")

    if not os.path.exists(db_path):
        print(f"[ERROR] База данных не найдена: {db_path}")
        return

    async with aiosqlite.connect(db_path) as db:
        # Проверяем структуру таблицы competition_participants
        print("=" * 70)
        print("СТРУКТУРА ТАБЛИЦЫ competition_participants:")
        print("=" * 70)

        cursor = await db.execute('PRAGMA table_info(competition_participants)')
        columns = await cursor.fetchall()

        has_heart_rate = False
        has_place_overall = False
        has_place_age_category = False

        for col in columns:
            col_id, name, col_type, notnull, default, pk = col
            print(f"{col_id:2}. {name:25} {col_type:15} {'NOT NULL' if notnull else ''}")

            if name == 'heart_rate':
                has_heart_rate = True
            if name == 'place_overall':
                has_place_overall = True
            if name == 'place_age_category':
                has_place_age_category = True

        print("\n" + "=" * 70)
        print("ПРОВЕРКА ОБЯЗАТЕЛЬНЫХ ПОЛЕЙ:")
        print("=" * 70)
        print(f"place_overall:       {'[OK]' if has_place_overall else '[MISSING]'}")
        print(f"place_age_category:  {'[OK]' if has_place_age_category else '[MISSING]'}")
        print(f"heart_rate:          {'[OK]' if has_heart_rate else '[MISSING]'}")

        if not has_heart_rate:
            print("\n[WARNING] Поле heart_rate отсутствует! Запустите миграцию:")
            print("  python migrations/add_heart_rate_field.py")
            print("\nДОБАВЛЯЮ ПОЛЕ СЕЙЧАС...")
            await db.execute('ALTER TABLE competition_participants ADD COLUMN heart_rate INTEGER')
            await db.commit()
            print("[OK] Поле heart_rate добавлено!")

        # Проверяем данные
        print("\n" + "=" * 70)
        print("ПРИМЕРЫ ДАННЫХ (последние 5 записей):")
        print("=" * 70)

        query = """
            SELECT id, user_id, competition_id, distance, finish_time,
                   place_overall, place_age_category, heart_rate, status
            FROM competition_participants
            ORDER BY id DESC
            LIMIT 5
        """

        cursor = await db.execute(query)
        rows = await cursor.fetchall()

        if rows:
            print(f"\n{'ID':<5} {'User':<8} {'Comp':<6} {'Dist':<6} {'Time':<12} {'Overall':<8} {'Category':<9} {'HR':<5} {'Status'}")
            print("-" * 70)
            for row in rows:
                id_, user_id, comp_id, dist, time, overall, category, hr, status = row
                print(f"{id_:<5} {user_id:<8} {comp_id:<6} {dist:<6.1f} {time or 'N/A':<12} {overall or '-':<8} {category or '-':<9} {hr or '-':<5} {status}")
        else:
            print("[INFO] Нет данных в таблице")

        # Проверяем есть ли соревнования со статусом finished
        print("\n" + "=" * 70)
        print("ЗАВЕРШЕННЫЕ СОРЕВНОВАНИЯ (для тестирования):")
        print("=" * 70)

        cursor = await db.execute("""
            SELECT c.id, c.name, c.date, cp.user_id, cp.distance, cp.finish_time
            FROM competitions c
            JOIN competition_participants cp ON c.id = cp.competition_id
            WHERE c.date < date('now') OR cp.status = 'finished'
            ORDER BY c.date DESC
            LIMIT 5
        """)
        rows = await cursor.fetchall()

        if rows:
            print(f"\n{'CompID':<7} {'UserID':<8} {'Название':<30} {'Дата':<12} {'Результат'}")
            print("-" * 70)
            for row in rows:
                comp_id, name, date, user_id, dist, time = row
                name_short = name[:27] + "..." if len(name) > 30 else name
                print(f"{comp_id:<7} {user_id:<8} {name_short:<30} {date:<12} {time or 'Нет'}")
        else:
            print("[INFO] Нет завершенных соревнований")

if __name__ == '__main__':
    asyncio.run(check_db())
