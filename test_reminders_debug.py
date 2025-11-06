"""
Скрипт для диагностики системы напоминаний
"""
import asyncio
import aiosqlite
import os
from datetime import datetime, date, timedelta

DB_PATH = os.getenv('DB_PATH', 'bot_data.db')


async def check_reminders():
    """Проверка состояния напоминаний в БД"""

    print("=" * 60)
    print("ДИАГНОСТИКА СИСТЕМЫ НАПОМИНАНИЙ")
    print("=" * 60)
    print()

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # 1. Проверяем наличие таблицы
        print("1. Проверка таблицы competition_reminders...")
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='competition_reminders'"
        )
        table_exists = await cursor.fetchone()

        if not table_exists:
            print("   [X] Tablitsa competition_reminders NE SUSCHESTVUET!")
            return
        else:
            print("   [OK] Tablitsa suschestvuet")

        # 2. Проверяем структуру таблицы
        print("\n2. Структура таблицы:")
        cursor = await db.execute("PRAGMA table_info(competition_reminders)")
        columns = await cursor.fetchall()
        for col in columns:
            print(f"   - {col['name']}: {col['type']}")

        # 3. Считаем все напоминания
        print("\n3. Статистика напоминаний:")
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM competition_reminders")
        row = await cursor.fetchone()
        total_reminders = row['cnt']
        print(f"   Всего напоминаний: {total_reminders}")

        cursor = await db.execute("SELECT COUNT(*) as cnt FROM competition_reminders WHERE sent = 0")
        row = await cursor.fetchone()
        pending_reminders = row['cnt']
        print(f"   Неотправленных: {pending_reminders}")

        cursor = await db.execute("SELECT COUNT(*) as cnt FROM competition_reminders WHERE sent = 1")
        row = await cursor.fetchone()
        sent_reminders = row['cnt']
        print(f"   Отправленных: {sent_reminders}")

        # 4. Показываем неотправленные напоминания
        if pending_reminders > 0:
            print("\n4. Неотправленные напоминания:")
            cursor = await db.execute(
                """
                SELECT
                    r.id,
                    r.user_id,
                    r.competition_id,
                    r.reminder_type,
                    r.scheduled_date,
                    c.name as competition_name,
                    c.date as competition_date
                FROM competition_reminders r
                JOIN competitions c ON r.competition_id = c.id
                WHERE r.sent = 0
                ORDER BY r.scheduled_date
                LIMIT 20
                """
            )
            rows = await cursor.fetchall()

            today = date.today()

            for row in rows:
                scheduled = datetime.strptime(row['scheduled_date'], '%Y-%m-%d').date()
                comp_date = datetime.strptime(row['competition_date'], '%Y-%m-%d').date()
                days_diff = (scheduled - today).days

                status = ""
                if days_diff < 0:
                    status = f"[!] PROSROCHENO ({abs(days_diff)} dn. nazad)"
                elif days_diff == 0:
                    status = "[!!!] SEGODNYA"
                else:
                    status = f"cherez {days_diff} dn."

                print(f"\n   ID: {row['id']}")
                print(f"   Пользователь: {row['user_id']}")
                print(f"   Соревнование: {row['competition_name']}")
                print(f"   Дата соревнования: {comp_date.strftime('%d.%m.%Y')}")
                print(f"   Тип: {row['reminder_type']}")
                print(f"   Запланировано на: {scheduled.strftime('%d.%m.%Y')} {status}")
        else:
            print("\n4. [X] Net neotpravlennyh napominaniy")

        # 5. Проверяем соревнования пользователей
        print("\n5. Проверка зарегистрированных пользователей на соревнования:")
        cursor = await db.execute(
            """
            SELECT
                cp.user_id,
                cp.competition_id,
                c.name,
                c.date,
                cp.distance,
                cp.status
            FROM competition_participants cp
            JOIN competitions c ON cp.competition_id = c.id
            WHERE cp.status = 'registered'
            ORDER BY c.date
            LIMIT 10
            """
        )
        registrations = await cursor.fetchall()

        if registrations:
            for reg in registrations:
                comp_date = datetime.strptime(reg['date'], '%Y-%m-%d').date()
                days_until = (comp_date - today).days

                print(f"\n   Пользователь: {reg['user_id']}")
                print(f"   Соревнование: {reg['name']}")
                print(f"   Дата: {comp_date.strftime('%d.%m.%Y')} (через {days_until} дн.)")
                print(f"   Дистанция: {reg['distance']} км")

                # Проверяем, есть ли напоминания для этой регистрации
                cursor2 = await db.execute(
                    """
                    SELECT COUNT(*) as cnt FROM competition_reminders
                    WHERE user_id = ? AND competition_id = ?
                    """,
                    (reg['user_id'], reg['competition_id'])
                )
                rem_row = await cursor2.fetchone()
                print(f"   Напоминаний создано: {rem_row['cnt']}")
        else:
            print("   [X] Net zaregistrirovannyh polzovateley")

        # 6. Проверка текущего времени
        print("\n6. Информация о времени:")
        now = datetime.now()
        print(f"   Текущее время: {now.strftime('%H:%M:%S')}")
        print(f"   Текущая дата: {now.strftime('%Y-%m-%d')}")
        print(f"   Планировщик запускается: в 10:20-10:25")

        if now.hour == 10 and 20 <= now.minute < 25:
            print("   [!!!] SEYCHAS VREMYA OTPRAVKI NAPOMINANIY!")
        elif now.hour < 10 or (now.hour == 10 and now.minute < 20):
            if now.hour == 10:
                mins_until = 20 - now.minute
                print(f"   Do vremeni otpravki ostalos {mins_until} minut")
            else:
                hours_until = 10 - now.hour
                print(f"   Do vremeni otpravki ostalos ~{hours_until} chasov")
        else:
            print("   Vremya otpravki uzhe proshlo, sleduyuschaya otpravka zavtra v 10:20")


if __name__ == "__main__":
    asyncio.run(check_reminders())
