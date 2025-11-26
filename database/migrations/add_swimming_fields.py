"""
Миграция для добавления полей плавания в таблицу trainings
Добавляет:
- swimming_location (место: 'бассейн' или 'открытая вода')
- pool_length (длина бассейна: 25 или 50 метров)
- swimming_styles (JSON массив стилей, использованных в тренировке)
- swimming_sets (TEXT описание отрезков)
"""

import aiosqlite
import asyncio
import sys
import io

# UTF-8 для вывода в Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


async def migrate():
    """Добавляет поля для плавания в таблицу trainings"""
    async with aiosqlite.connect('database.sqlite') as db:
        print("=" * 60)
        print("Миграция: Добавление полей для плавания")
        print("=" * 60)

        # Проверяем, существуют ли уже колонки
        cursor = await db.execute("PRAGMA table_info(trainings)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]

        fields_to_add = []

        if 'swimming_location' not in column_names:
            fields_to_add.append(('swimming_location', "ADD COLUMN swimming_location TEXT"))

        if 'pool_length' not in column_names:
            fields_to_add.append(('pool_length', "ADD COLUMN pool_length INTEGER"))

        if 'swimming_styles' not in column_names:
            fields_to_add.append(('swimming_styles', "ADD COLUMN swimming_styles TEXT"))

        if 'swimming_sets' not in column_names:
            fields_to_add.append(('swimming_sets', "ADD COLUMN swimming_sets TEXT"))

        if not fields_to_add:
            print("\n✅ Все поля уже существуют. Миграция не требуется.")
            return

        # Добавляем отсутствующие поля
        for field_name, alter_command in fields_to_add:
            try:
                await db.execute(f"ALTER TABLE trainings {alter_command}")
                print(f"✅ Добавлено поле: {field_name}")
            except Exception as e:
                print(f"⚠️ Ошибка при добавлении поля {field_name}: {e}")

        await db.commit()

        print("\n" + "=" * 60)
        print("✅ Миграция успешно завершена!")
        print("=" * 60)

        # Показываем обновленную схему таблицы
        cursor = await db.execute("PRAGMA table_info(trainings)")
        columns = await cursor.fetchall()

        print("\nОбновленная схема таблицы trainings:")
        print("-" * 60)
        for col in columns:
            col_id, name, col_type, not_null, default, pk = col
            print(f"  {name:25} {col_type:15} {'NOT NULL' if not_null else ''}")
        print("-" * 60)


if __name__ == "__main__":
    asyncio.run(migrate())
