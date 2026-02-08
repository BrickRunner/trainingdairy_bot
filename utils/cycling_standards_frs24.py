"""
Официальные нормативы по велоспорту-шоссе ЕВСК 2022-2025гг.
Источник: http://frs24.ru/st/velosport-shosse-normativ/
Актуальны для 2025 года.

МСМК выполняется с 18 лет, МС - с 15 лет, КМС - с 14 лет, остальные разряды - с 13 лет.
"""

from typing import List, Dict


def parse_time_to_seconds(time_str: str) -> float:
    """
    Конвертирует строку времени в секунды.

    Args:
        time_str: Строка времени (например "1:06:05", "32:03")

    Returns:
        Время в секундах
    """
    time_str = str(time_str).strip()

    if time_str.count(':') == 2:
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
        return hours * 3600 + minutes * 60 + seconds

    if ':' in time_str:
        parts = time_str.split(':')
        minutes = int(parts[0])
        seconds = int(parts[1])
        return minutes * 60 + seconds

    return float(time_str)


def get_frs24_cycling_standards() -> List[Dict]:
    """
    Возвращает нормативы ЕВСК по велоспорту-шоссе.

    Returns:
        Список нормативов с дистанцией, дисциплиной, полом, разрядом и временем
    """
    standards = []

    male_individual = {
        50: {  
            'МС': '1:06:05', 'КМС': '1:09:30', 'I': '1:15:39',
            'II': '1:21:30', 'III': '1:31:00'
        },
        25: {
            'МС': '32:03', 'КМС': '34:02', 'I': '36:45',
            'II': '38:30', 'III': '41:30'
        },
        20: {
            'МС': '25:24', 'КМС': '26:58', 'I': '29:00',
            'II': '30:30', 'III': '32:00', 'I юн.': '34:00'
        },
        15: {
            'МС': '18:49', 'КМС': '19:59', 'I': '21:30',
            'II': '22:30', 'III': '24:00', 'I юн.': '25:15',
            'II юн.': '31:34', 'III юн.': '34:11'
        },
        10: {
            'МС': '12:20', 'КМС': '13:06', 'I': '14:07',
            'II': '15:12', 'III': '16:00', 'I юн.': '18:47',
            'II юн.': '20:41', 'III юн.': '22:24'
        }
    }

    male_team = {
        50: {
            'МС': '1:02:55', 'КМС': '1:06:50', 'I': '1:12:30',
            'II': '1:17:30', 'III': '1:26:45'
        },
        25: {
            'МС': '30:30', 'КМС': '32:25', 'I': '35:30',
            'II': '37:30', 'III': '38:00', 'I юн.': '41:00',
            'II юн.': '51:10', 'III юн.': '55:25'
        }
    }

    female_individual = {
        25: {
            'МС': '36:30', 'КМС': '38:50', 'I': '41:55',
            'II': '45:05', 'III': '50:25'
        },
        20: {
            'МС': '28:59', 'КМС': '30:47', 'I': '33:12',
            'II': '35:44', 'III': '39:57'
        },
        15: {
            'МС': '21:29', 'КМС': '22:49', 'I': '24:36',
            'II': '26:28', 'III': '29:00', 'I юн.': '31:00',
            'II юн.': '36:02', 'III юн.': '39:02'
        },
        10: {
            'МС': '14:04', 'КМС': '14:57', 'I': '16:07',
            'II': '17:21', 'III': '19:00', 'I юн.': '21:00',
            'II юн.': '23:37', 'III юн.': '25:35'
        },
        5: {
            'МС': '06:50', 'КМС': '07:16', 'I': '07:50',
            'II': '08:26', 'III': '09:00', 'I юн.': '09:30',
            'II юн.': '11:28', 'III юн.': '12:26'
        }
    }

    female_team = {
        50: {
            'МС': '1:11:50', 'КМС': '1:16:20', 'I': '1:22:15',
            'II': '1:28:30', 'III': '1:39:00'
        },
        25: {
            'МС': '34:50', 'КМС': '36:59', 'I': '40:00',
            'II': '41:00', 'III': '43:00'
        }
    }

    datasets = [
        (male_individual, 'male', 'индивидуальная гонка'),
        (male_team, 'male', 'парная гонка'),
        (female_individual, 'female', 'индивидуальная гонка'),
        (female_team, 'female', 'парная гонка')
    ]

    for data, gender, discipline in datasets:
        for distance_km, ranks in data.items():
            for rank, time_str in ranks.items():
                standards.append({
                    'distance': distance_km,
                    'discipline': discipline,
                    'gender': gender,
                    'rank': rank,
                    'time_seconds': parse_time_to_seconds(time_str)
                })

    return standards


if __name__ == "__main__":
    standards = get_frs24_cycling_standards()
    print(f"Всего нормативов: {len(standards)}")

    print("\nПримеры (мужчины, индивидуальная гонка, 25 км):")
    for s in standards:
        if (s['distance'] == 25 and s['discipline'] == 'индивидуальная гонка' and
            s['gender'] == 'male'):
            minutes = int(s['time_seconds'] // 60)
            seconds = int(s['time_seconds'] % 60)
            print(f"  {s['rank']}: {minutes}:{seconds:02d}")

    print("\nПримеры (женщины, индивидуальная гонка, 10 км):")
    for s in standards:
        if (s['distance'] == 10 and s['discipline'] == 'индивидуальная гонка' and
            s['gender'] == 'female'):
            minutes = int(s['time_seconds'] // 60)
            seconds = int(s['time_seconds'] % 60)
            print(f"  {s['rank']}: {minutes}:{seconds:02d}")

    print("\n\nСтатистика:")
    disciplines = set(s['discipline'] for s in standards)
    print(f"Дисциплины: {', '.join(disciplines)}")

    male_count = sum(1 for s in standards if s['gender'] == 'male')
    female_count = sum(1 for s in standards if s['gender'] == 'female')
    print(f"Мужчины: {male_count}, Женщины: {female_count}")
