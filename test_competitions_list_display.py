"""Тест отображения списка соревнований с целевым темпом"""
import asyncio
from competitions.competitions_queries import get_user_competitions
from utils.time_formatter import calculate_pace_with_unit
from competitions.competitions_utils import format_competition_distance, format_competition_date


def format_time_until_competition(comp_date):
    """Упрощенная версия для теста"""
    from datetime import datetime
    try:
        target = datetime.strptime(comp_date, '%Y-%m-%d').date()
        today = datetime.now().date()
        delta = (target - today).days

        if delta < 0:
            return "прошло"
        elif delta == 0:
            return "сегодня"
        elif delta == 1:
            return "завтра"
        else:
            return f"{delta} дней"
    except:
        return "?"


async def test_list_display():
    user_id = 1611441720

    print("="*70)
    print("ПРЕДПРОСМОТР: МОИ СОРЕВНОВАНИЯ")
    print("="*70)

    competitions = await get_user_competitions(user_id, status_filter='upcoming')

    if not competitions:
        print("У вас пока нет запланированных соревнований.")
        return

    text = "МОИ СОРЕВНОВАНИЯ\n\n"

    for i, comp in enumerate(competitions[:10], 1):
        time_until = format_time_until_competition(comp['date'])

        # Форматируем дистанцию
        dist_str = await format_competition_distance(comp['distance'], user_id)

        # Форматируем дату
        date_str = await format_competition_date(comp['date'], user_id)

        # Форматируем целевое время И темп
        target_time = comp.get('target_time')
        if target_time is None or target_time == 'None' or target_time == '':
            target_time_str = 'Нет цели'
            target_pace_str = ''
        else:
            target_time_str = target_time
            # Рассчитываем темп для целевого времени
            target_pace = await calculate_pace_with_unit(target_time, comp['distance'], user_id)
            target_pace_str = f" ({target_pace})" if target_pace else ''

        comp_name = comp.get('name', 'Без названия')[:50]

        text += (
            f"{i}. {comp_name}\n"
            f"   Дистанция: {dist_str}\n"
            f"   Дата: {date_str} ({time_until})\n"
            f"   Цель: {target_time_str}{target_pace_str}\n\n"
        )

    print(text)
    print("="*70)
    print("\nПРИМЕРЫ С ЦЕЛЕВЫМ ТЕМПОМ:")

    # Показываем только соревнования с целевым временем
    with_target = [c for c in competitions if c.get('target_time') and c.get('target_time') != 'None']

    if with_target:
        for comp in with_target[:3]:
            target_time = comp.get('target_time')
            distance = comp.get('distance')
            pace = await calculate_pace_with_unit(target_time, distance, user_id)

            print(f"\n  Соревнование: {comp.get('name', 'N/A')[:40]}")
            print(f"  Отображение: 'Цель: {target_time} ({pace})'")
    else:
        print("\n  Нет соревнований с установленным целевым временем")

    print("\n" + "="*70)


if __name__ == "__main__":
    asyncio.run(test_list_display())
