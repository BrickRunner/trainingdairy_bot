"""
Тест фильтрации событий Лиги Путешествий
Проверяем что скрывается только конкретное событие на которое зарегистрировался
"""

import sys
import io

# Установка правильной кодировки для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def test_camp_filtering_logic():
    """
    Симуляция логики фильтрации для Лиги Путешествий
    """

    print("="*60)
    print("ТЕСТ ФИЛЬТРАЦИИ ЛИГИ ПУТЕШЕСТВИЙ")
    print("="*60)

    # Симулируем список всех событий Лиги Путешествий
    all_camps = [
        {
            'name': 'Лига Путешествий: Карелия',
            'url': 'https://heroleague.ru/event/karelia',
            'sport_code': 'camp'
        },
        {
            'name': 'Лига Путешествий: Байкал',
            'url': 'https://heroleague.ru/event/baikal',
            'sport_code': 'camp'
        },
        {
            'name': 'Лига Путешествий: Алтай',
            'url': 'https://heroleague.ru/event/altai',
            'sport_code': 'camp'
        },
    ]

    # Пользователь зарегистрировался только на Карелию
    participant_urls = ['https://heroleague.ru/event/karelia']

    print(f"\nВсего событий Лиги Путешествий: {len(all_camps)}")
    print(f"Пользователь зарегистрирован на: {len(participant_urls)}")
    print(f"  - {participant_urls[0]}")

    # Применяем логику фильтрации
    filtered_camps = []
    for comp in all_camps:
        comp_url = comp['url']
        sport_code = comp['sport_code']

        if sport_code == "camp":
            # Логика из кода
            if comp_url not in participant_urls:
                filtered_camps.append(comp)
                print(f"\n✅ ПОКАЗАТЬ: {comp['name']}")
                print(f"   URL: {comp_url}")
                print(f"   Причина: URL не в списке зарегистрированных")
            else:
                print(f"\n❌ СКРЫТЬ: {comp['name']}")
                print(f"   URL: {comp_url}")
                print(f"   Причина: Пользователь зарегистрирован")

    print("\n" + "="*60)
    print("РЕЗУЛЬТАТ ФИЛЬТРАЦИИ")
    print("="*60)
    print(f"Всего событий: {len(all_camps)}")
    print(f"Зарегистрирован на: {len(participant_urls)}")
    print(f"Должно показаться: {len(all_camps) - len(participant_urls)}")
    print(f"Показывается: {len(filtered_camps)}")

    if len(filtered_camps) == len(all_camps) - len(participant_urls):
        print("\n✅ ТЕСТ ПРОЙДЕН: Скрывается только зарегистрированное событие")
        print(f"\nСобытия в поиске:")
        for comp in filtered_camps:
            print(f"  - {comp['name']}")
        return True
    else:
        print("\n❌ ТЕСТ НЕ ПРОЙДЕН")
        return False

if __name__ == "__main__":
    test_camp_filtering_logic()
