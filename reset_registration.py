"""
Скрипт для сброса регистрации пользователя
Используйте это для повторного тестирования процесса регистрации
"""

import aiosqlite
import asyncio
import os

# Путь к базе данных
DB_PATH = os.getenv('DB_PATH', 'bot_data.db')


async def reset_user_registration(user_id: int):
    """
    Сбросить данные регистрации пользователя

    Args:
        user_id: Telegram ID пользователя
    """
    async with aiosqlite.connect(DB_PATH) as db:
        # Очищаем основные поля регистрации
        await db.execute(
            """
            UPDATE user_settings
            SET name = NULL,
                birth_date = NULL,
                gender = NULL,
                height = NULL,
                weight = NULL,
                main_training_types = '[]',
                timezone = 'Europe/Moscow'
            WHERE user_id = ?
            """,
            (user_id,)
        )
        await db.commit()

        # Проверяем результат
        async with db.execute(
            "SELECT name, birth_date, gender FROM user_settings WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row and all(field is None for field in row):
                print(f"✅ Данные регистрации для пользователя {user_id} успешно сброшены!")
                print("Теперь отправьте команду /start боту для повторной регистрации.")
            else:
                print(f"⚠️ Возможно, пользователь {user_id} не найден в базе данных.")


async def main():
    """Главная функция"""
    print("=" * 60)
    print("СБРОС ДАННЫХ РЕГИСТРАЦИИ")
    print("=" * 60)
    print()

    # Запрашиваем user_id
    try:
        user_id = int(input("Введите ваш Telegram User ID: "))
    except ValueError:
        print("❌ Ошибка: введите корректный числовой ID")
        return

    # Подтверждение
    confirm = input(f"\n⚠️ Вы уверены, что хотите сбросить регистрацию для пользователя {user_id}? (yes/no): ")

    if confirm.lower() in ['yes', 'y', 'да']:
        await reset_user_registration(user_id)
    else:
        print("❌ Операция отменена")


if __name__ == "__main__":
    # Запускаем асинхронную функцию
    asyncio.run(main())
