"""
Тестовый скрипт для проверки системы поздравлений с днём рождения
"""

import asyncio
from datetime import datetime
import sys
import os

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.queries import get_all_users_with_birthdays


async def test_birthday_check():
    """Проверка наличия пользователей с днями рождения"""

    # Настройка кодировки для Windows консоли
    import sys
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("=" * 60)
    print("ТЕСТ СИСТЕМЫ ПОЗДРАВЛЕНИЙ С ДНЁМ РОЖДЕНИЯ")
    print("=" * 60)

    # Получаем текущую дату
    today = datetime.now()
    print(f"\nТекущая дата: {today.strftime('%d.%m.%Y')}")
    print(f"Текущий день: {today.day}")
    print(f"Текущий месяц: {today.month}")

    # Получаем пользователей с днями рождения
    print("\n" + "-" * 60)
    print("Проверка базы данных...")
    print("-" * 60)

    users = await get_all_users_with_birthdays()

    if not users:
        print("❌ В базе данных НЕТ пользователей с указанной датой рождения!")
        print("\nВозможные причины:")
        print("1. Пользователь не указал дату рождения в настройках профиля")
        print("2. Дата рождения записана в неправильном формате")
        print("3. Поле birth_date в таблице user_settings пустое")
        return

    print(f"✅ Найдено пользователей с датой рождения: {len(users)}")
    print("\nСписок пользователей:")

    birthdays_today = []

    for user in users:
        user_id = user['user_id']
        birth_date = user['birth_date']

        # Вычисляем возраст
        age = today.year - birth_date.year
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1

        # Проверяем, совпадает ли день рождения с сегодняшним днём
        is_birthday_today = (birth_date.day == today.day and birth_date.month == today.month)

        status = "🎉 СЕГОДНЯ ДЕНЬ РОЖДЕНИЯ!" if is_birthday_today else ""

        print(f"\n  User ID: {user_id}")
        print(f"  Дата рождения: {birth_date.strftime('%d.%m.%Y')}")
        print(f"  Возраст: {age} лет")
        print(f"  {status}")

        if is_birthday_today:
            birthdays_today.append(user)

    print("\n" + "=" * 60)

    if birthdays_today:
        print(f"\n✅ СЕГОДНЯ ДЕНЬ РОЖДЕНИЯ У {len(birthdays_today)} пользователей!")
        print("Им ДОЛЖНЫ быть отправлены поздравления в 9:10 утра")
    else:
        print("\n❌ Сегодня НЕТ пользователей с днём рождения")
        print("Поздравления НЕ будут отправлены")

    print("\n" + "=" * 60)
    print("РЕКОМЕНДАЦИИ:")
    print("=" * 60)

    if not birthdays_today and users:
        # Находим ближайший день рождения
        from datetime import timedelta
        min_days = float('inf')
        next_birthday_user = None

        for user in users:
            birth_date = user['birth_date']
            # Создаём дату дня рождения в этом году
            this_year_birthday = datetime(today.year, birth_date.month, birth_date.day)

            # Если день рождения уже прошёл в этом году, берём следующий год
            if this_year_birthday < today:
                this_year_birthday = datetime(today.year + 1, birth_date.month, birth_date.day)

            days_until = (this_year_birthday - today).days

            if days_until < min_days:
                min_days = days_until
                next_birthday_user = user

        if next_birthday_user:
            next_date = next_birthday_user['birth_date']
            print(f"\nБлижайший день рождения: {next_date.strftime('%d.%m')} (через {min_days} дней)")
            print(f"User ID: {next_birthday_user['user_id']}")

    if not users:
        print("\n1. Проверьте, указал ли пользователь дату рождения:")
        print("   Настройки → Профиль → Дата рождения")
        print("\n2. Проверьте базу данных напрямую:")
        print("   SELECT id, birth_date FROM user_settings WHERE birth_date IS NOT NULL;")


if __name__ == "__main__":
    asyncio.run(test_birthday_check())
