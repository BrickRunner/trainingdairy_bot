import asyncio
import aiosqlite

async def check():
    async with aiosqlite.connect('database.sqlite') as db:
        db.row_factory = aiosqlite.Row

        # Проверяем swimming_standards
        cursor = await db.execute('SELECT COUNT(*) as count FROM swimming_standards')
        count = await cursor.fetchone()
        print(f'Swimming standards: {count["count"]}')

        # Проверяем cycling_standards
        cursor = await db.execute('SELECT COUNT(*) as count FROM cycling_standards')
        count = await cursor.fetchone()
        print(f'Cycling standards: {count["count"]}')

        # Проверяем running_standards
        cursor = await db.execute('SELECT COUNT(*) as count FROM running_standards')
        count = await cursor.fetchone()
        print(f'Running standards: {count["count"]}')

        # Проверяем versions
        cursor = await db.execute('SELECT sport_type, version, is_active FROM standards_versions')
        rows = await cursor.fetchall()
        print('\nStandards versions:')
        for row in rows:
            print(f'  {row["sport_type"]}: {row["version"]}, active: {row["is_active"]}')

        # Проверяем примеры из swimming_standards
        cursor = await db.execute('SELECT distance, pool_length, gender, rank, time_seconds FROM swimming_standards LIMIT 10')
        rows = await cursor.fetchall()
        print('\nSwimming standards examples:')
        for row in rows:
            print(f'  {row["distance"]}km, {row["pool_length"]}m, {row["gender"]}, {row["rank"]}: {row["time_seconds"]}s')

        # Проверяем примеры из cycling_standards
        cursor = await db.execute('SELECT distance, discipline, gender, rank, time_seconds FROM cycling_standards LIMIT 10')
        rows = await cursor.fetchall()
        print('\nCycling standards examples:')
        for row in rows:
            print(f'  {row["distance"]}km, {row["discipline"]}, {row["gender"]}, {row["rank"]}: {row["time_seconds"]}s')

asyncio.run(check())
