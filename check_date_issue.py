"""
Проверка проблемы с датами
"""

import asyncio
import aiosqlite
from database.queries import DB_PATH

async def check_date_issue():
    """Проверка проблемы с пустыми датами"""

    print("=" * 70)
    print("ПРОВЕРКА ПРОБЛЕМЫ С ДАТАМИ")
    print("=" * 70)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Находим соревнования с пустой датой
        print("\n1. Соревнования с пустой или NULL датой:")
        query = """
            SELECT c.id, c.name, c.date, c.source_url,
                   (SELECT COUNT(*) FROM competition_participants WHERE competition_id = c.id) as participants
            FROM competitions c
            WHERE c.date IS NULL OR c.date = '' OR LENGTH(c.date) = 0
            ORDER BY c.id DESC
            LIMIT 10
        """
        async with db.execute(query) as cursor:
            rows = await cursor.fetchall()
            if rows:
                print(f"   Найдено {len(rows)} соревнований с пустой датой:")
                for row in rows:
                    r = dict(row)
                    print(f"   [ID:{r['id']}] {r['name'][:50]}")
                    print(f"      date={repr(r['date'])} | participants={r['participants']} | url={r['source_url'][:60] if r['source_url'] else 'None'}")
            else:
                print("   Все соревнования имеют дату")

        # Проверяем регистрации на соревнования с пустой датой
        print("\n2. Регистрации на соревнования с пустой датой:")
        query = """
            SELECT cp.user_id, c.name, c.date, cp.proposal_status, cp.distance_name
            FROM competition_participants cp
            JOIN competitions c ON cp.competition_id = c.id
            WHERE c.date IS NULL OR c.date = '' OR LENGTH(c.date) = 0
            ORDER BY cp.id DESC
            LIMIT 10
        """
        async with db.execute(query) as cursor:
            rows = await cursor.fetchall()
            if rows:
                print(f"   Найдено {len(rows)} регистраций:")
                for row in rows:
                    r = dict(row)
                    status = f"[{r['proposal_status']}]" if r['proposal_status'] else ""
                    print(f"   user={r['user_id']} | {r['name'][:40]} | date={repr(r['date'])} {status}")
            else:
                print("   Все регистрации на соревнования с датой")

        # Проверяем источники данных для соревнований с пустой датой
        print("\n3. Источники соревнований с пустой датой:")
        query = """
            SELECT DISTINCT
                CASE
                    WHEN source_url LIKE '%russiarunning%' THEN 'RussiaRunning'
                    WHEN source_url LIKE '%heroleague%' THEN 'HeroLeague'
                    WHEN source_url LIKE '%timerman%' THEN 'Timerman'
                    WHEN source_url LIKE '%reg.place%' THEN 'reg.place'
                    WHEN source_url IS NULL OR source_url = '' THEN 'Custom (user-created)'
                    ELSE 'Other'
                END as source,
                COUNT(*) as count
            FROM competitions
            WHERE date IS NULL OR date = '' OR LENGTH(date) = 0
            GROUP BY source
        """
        async with db.execute(query) as cursor:
            rows = await cursor.fetchall()
            if rows:
                for row in rows:
                    r = dict(row)
                    print(f"   {r['source']}: {r['count']} соревнований")
            else:
                print("   Нет данных")

        # Проверяем примеры с корректными датами
        print("\n4. Примеры соревнований с корректными датами:")
        query = """
            SELECT c.id, c.name, c.date, c.source_url
            FROM competitions c
            WHERE c.date IS NOT NULL AND c.date != '' AND LENGTH(c.date) > 0
            ORDER BY c.id DESC
            LIMIT 5
        """
        async with db.execute(query) as cursor:
            rows = await cursor.fetchall()
            if rows:
                for row in rows:
                    r = dict(row)
                    print(f"   [ID:{r['id']}] {r['name'][:40]} | date={r['date']}")
            else:
                print("   Нет соревнований с датой")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    asyncio.run(check_date_issue())
