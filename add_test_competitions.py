"""
Скрипт для добавления тестовых соревнований в базу данных
"""

import asyncio
import json
from datetime import datetime, timedelta
from competitions.competitions_queries import add_competition


async def add_test_competitions():
    """Добавить тестовые соревнования"""

    # Текущая дата для расчёта будущих дат
    today = datetime.now().date()

    test_competitions = [
        {
            'name': 'Московский марафон 2025',
            'date': (today + timedelta(days=120)).strftime('%Y-%m-%d'),
            'city': 'Москва',
            'country': 'Россия',
            'location': 'Лужники',
            'distances': json.dumps([42.195, 21.1, 10, 5]),
            'type': 'марафон',
            'description': 'Крупнейший марафон в России. Старт и финиш в Лужниках.',
            'official_url': 'https://moscowmarathon.org',
            'organizer': 'Беговое сообщество',
            'registration_status': 'open',
            'status': 'upcoming',
            'is_official': 1,
            'source_url': 'https://moscowmarathon.org'
        },
        {
            'name': 'Зеленый марафон Сбербанка',
            'date': (today + timedelta(days=45)).strftime('%Y-%m-%d'),
            'city': 'Москва',
            'country': 'Россия',
            'location': 'Парк Горького',
            'distances': json.dumps([21.1, 10, 5, 3]),
            'type': 'марафон',
            'description': 'Благотворительный забег в поддержку здорового образа жизни.',
            'official_url': 'https://green.sberbank.ru',
            'organizer': 'Беговое сообщество',
            'registration_status': 'open',
            'status': 'upcoming',
            'is_official': 1,
            'source_url': 'https://green.sberbank.ru'
        },
        {
            'name': 'Санкт-Петербургский марафон "Белые ночи"',
            'date': (today + timedelta(days=180)).strftime('%Y-%m-%d'),
            'city': 'Санкт-Петербург',
            'country': 'Россия',
            'location': 'Дворцовая площадь',
            'distances': json.dumps([42.195, 21.1, 10]),
            'type': 'марафон',
            'description': 'Международный марафон в северной столице России.',
            'official_url': 'https://spbmarathon.ru',
            'organizer': 'Russia Running',
            'registration_status': 'open',
            'status': 'upcoming',
            'is_official': 1,
            'source_url': 'https://spbmarathon.ru'
        },
        {
            'name': 'Rosa Run',
            'date': (today + timedelta(days=90)).strftime('%Y-%m-%d'),
            'city': 'Сочи',
            'country': 'Россия',
            'location': 'Роза Хутор',
            'distances': json.dumps([42.195, 21.1, 10, 5]),
            'type': 'трейл',
            'description': 'Горный забег на курорте Роза Хутор с живописными видами.',
            'official_url': 'https://rosaski.com',
            'organizer': 'Timerman',
            'registration_status': 'open',
            'status': 'upcoming',
            'is_official': 1,
            'source_url': 'https://rosaski.com/rosa-run'
        },
        {
            'name': 'Пробег "Лужники"',
            'date': (today + timedelta(days=30)).strftime('%Y-%m-%d'),
            'city': 'Москва',
            'country': 'Россия',
            'location': 'Лужники',
            'distances': json.dumps([21.1, 10, 5]),
            'type': 'полумарафон',
            'description': 'Традиционный весенний полумарафон в Лужниках.',
            'official_url': 'https://probeg.org',
            'organizer': 'Беговое сообщество',
            'registration_status': 'open',
            'status': 'upcoming',
            'is_official': 1,
            'source_url': 'https://probeg.org/luzhniki'
        },
        {
            'name': 'Wings for Life World Run',
            'date': (today + timedelta(days=60)).strftime('%Y-%m-%d'),
            'city': 'Москва',
            'country': 'Россия',
            'location': 'Крылатское',
            'distances': json.dumps([0]),  # Бег до момента пока тебя не догонит машина
            'type': 'забег',
            'description': 'Глобальный благотворительный забег, где все участники бегут одновременно по всему миру.',
            'official_url': 'https://www.wingsforlifeworldrun.com/ru',
            'organizer': 'Лига героев',
            'registration_status': 'open',
            'status': 'upcoming',
            'is_official': 1,
            'source_url': 'https://www.wingsforlifeworldrun.com'
        },
        {
            'name': 'Казанский марафон',
            'date': (today + timedelta(days=150)).strftime('%Y-%m-%d'),
            'city': 'Казань',
            'country': 'Россия',
            'location': 'Площадь Тысячелетия',
            'distances': json.dumps([42.195, 21.1, 10, 3]),
            'type': 'марафон',
            'description': 'Один из крупнейших марафонов в Поволжье.',
            'official_url': 'https://kazanmarathon.org',
            'organizer': 'Russia Running',
            'registration_status': 'open',
            'status': 'upcoming',
            'is_official': 1,
            'source_url': 'https://kazanmarathon.org'
        },
        {
            'name': 'Фруктовый забег',
            'date': (today + timedelta(days=75)).strftime('%Y-%m-%d'),
            'city': 'Москва',
            'country': 'Россия',
            'location': 'Коломенское',
            'distances': json.dumps([10, 5, 3]),
            'type': 'забег',
            'description': 'Веселый летний забег с фруктами на финише!',
            'official_url': 'https://fruitzabeg.ru',
            'organizer': 'Фруктовые забеги',
            'registration_status': 'open',
            'status': 'upcoming',
            'is_official': 1,
            'source_url': 'https://fruitzabeg.ru'
        }
    ]

    print("=" * 60)
    print("ADDING TEST COMPETITIONS")
    print("=" * 60)
    print()

    for i, comp_data in enumerate(test_competitions, 1):
        try:
            comp_id = await add_competition(comp_data)
            print(f"OK {i}. {comp_data['name']}")
            print(f"   ID: {comp_id}")
            print(f"   Date: {comp_data['date']}")
            print(f"   City: {comp_data['city']}")
            print()
        except Exception as e:
            print(f"ERROR {i}. Failed to add '{comp_data['name']}': {e}")
            print()

    print("=" * 60)
    print(f"Competitions added: {len(test_competitions)}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(add_test_competitions())
