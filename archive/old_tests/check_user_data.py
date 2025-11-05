"""
Скрипт для проверки данных пользователя в базе данных
"""

import aiosqlite
import asyncio
import os
import json

# Путь к базе данных
DB_PATH = os.getenv('DB_PATH', 'bot_data.db')


async def check_user_data(user_id: int):
    """
    Показать все данные пользователя

    Args:
        user_id: Telegram ID пользователя
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM user_settings WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()

            if row:
                data = dict(row)
                print("=" * 60)
                print(f"ДАННЫЕ ПОЛЬЗОВАТЕЛЯ {user_id}")
                print("=" * 60)
                print()

                # Основные данные профиля
                print("📋 ПРОФИЛЬ:")
                print(f"  👤 Имя: {data.get('name') or 'не указано'}")
                print(f"  🎂 Дата рождения: {data.get('birth_date') or 'не указана'}")

                # Пол с форматированием
                gender = data.get('gender')
                if gender == 'male':
                    gender_text = '👨 Мужской'
                elif gender == 'female':
                    gender_text = '👩 Женский'
                else:
                    gender_text = 'не указан'
                print(f"  ⚧️ Пол: {gender_text}")

                print(f"  📏 Рост: {data.get('height') or 'не указан'} см")
                print(f"  ⚖️ Вес: {data.get('weight') or 'не указан'} {data.get('weight_unit', 'кг')}")

                # Основные типы тренировок
                try:
                    main_types = json.loads(data.get('main_training_types', '[]'))
                    print(f"  🏃 Основные типы тренировок: {', '.join(main_types) if main_types else 'не выбраны'}")
                except:
                    print(f"  🏃 Основные типы тренировок: не выбраны")

                print()

                # Пульсовые зоны
                print("💓 ПУЛЬСОВЫЕ ЗОНЫ:")
                print(f"  Макс. пульс: {data.get('max_pulse') or 'не установлен'}")
                if data.get('max_pulse'):
                    print(f"  Зона 1: {data.get('zone1_min')}-{data.get('zone1_max')} уд/мин")
                    print(f"  Зона 2: {data.get('zone2_min')}-{data.get('zone2_max')} уд/мин")
                    print(f"  Зона 3: {data.get('zone3_min')}-{data.get('zone3_max')} уд/мин")
                    print(f"  Зона 4: {data.get('zone4_min')}-{data.get('zone4_max')} уд/мин")
                    print(f"  Зона 5: {data.get('zone5_min')}-{data.get('zone5_max')} уд/мин")
                print()

                # Настройки
                print("⚙️ НАСТРОЙКИ:")
                print(f"  🌍 Часовой пояс: {data.get('timezone', 'Europe/Moscow')}")
                print(f"  📏 Единица дистанции: {data.get('distance_unit', 'км')}")
                print(f"  ⚖️ Единица веса: {data.get('weight_unit', 'кг')}")
                print(f"  📅 Формат даты: {data.get('date_format', 'ДД.ММ.ГГГГ')}")
                print()

                # Цели
                print("🎯 ЦЕЛИ:")
                print(f"  📊 Недельный объём: {data.get('weekly_volume_goal') or 'не установлен'} км")
                print(f"  🔢 Тренировок в неделю: {data.get('weekly_trainings_goal') or 'не установлено'}")
                print(f"  ⚖️ Целевой вес: {data.get('weight_goal') or 'не установлен'} {data.get('weight_unit', 'кг')}")

                # Цели по типам
                try:
                    type_goals = json.loads(data.get('training_type_goals', '{}'))
                    if type_goals:
                        print(f"  🏃 Цели по типам:")
                        for t_type, goal in type_goals.items():
                            print(f"    - {t_type}: {goal} км")
                except:
                    pass

                print()
                print("=" * 60)
            else:
                print(f"❌ Пользователь с ID {user_id} не найден в базе данных.")


async def main():
    """Главная функция"""
    print()
    try:
        user_id = int(input("Введите ваш Telegram User ID: "))
        print()
        await check_user_data(user_id)
    except ValueError:
        print("❌ Ошибка: введите корректный числовой ID")


if __name__ == "__main__":
    asyncio.run(main())
