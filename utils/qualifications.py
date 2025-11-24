"""
Модуль для определения спортивных разрядов по результатам соревнований.
Использует официальные нормативы ЕВСК 2022-2025 гг. (действуют с 26 ноября 2024 г.)

Официальные источники:
- Легкая атлетика: https://rusathletics.info/ (ВФЛА)
  Файл: https://rusathletics.info/wp-content/uploads/2025/01/legkaya_atletika_dejstvuyut_c_26_noyabrya_2024_g_87b8cad5ee.xls
- Плавание: https://www.russwimming.ru/ (ФВВСР)
  Файл: https://www.russwimming.ru/upload/iblock/454/2p9mhknbbs3fltf01qc1d5lhn5ijb41c/plavanie_dejstvuyut_c_26_noyabrya_2024_g_197d4117d4.xls
- Велоспорт: https://fvsr.ru/ (ФВСР)
"""

from typing import Optional, Dict


def time_to_seconds(time_str: str) -> float:
    """
    Преобразует время в секунды.

    Форматы:
    - "сс.сс" (например, "23.95")
    - "мм:сс" или "мм:сс.сс" (например, "15:30" или "1:05.34")
    - "ч:мм:сс" или "ч:мм:сс.сс" (например, "1:15:30" или "2:12:00")
    """
    time_str = str(time_str).strip()
    parts = time_str.split(':')

    if len(parts) == 1:
        # Только секунды (например, "23.95")
        return float(parts[0].replace(',', '.'))
    elif len(parts) == 2:
        # Минуты:Секунды
        minutes = int(parts[0])
        seconds = float(parts[1].replace(',', '.'))
        return minutes * 60 + seconds
    elif len(parts) == 3:
        # Часы:Минуты:Секунды
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2].replace(',', '.'))
        return hours * 3600 + minutes * 60 + seconds
    else:
        raise ValueError(f"Неверный формат времени: {time_str}")


# Нормативы по легкой атлетике (бег) - ЕВСК 2022-2025
# Официальный источник: https://rusathletics.info/ (ВФЛА)
# Файл: https://rusathletics.info/wp-content/uploads/2025/01/legkaya_atletika_dejstvuyut_c_26_noyabrya_2024_g_87b8cad5ee.xls
# Действуют с 26 ноября 2024 года
RUNNING_STANDARDS = {
    'men': {
        0.06: {  # 60 м
            'I': 7.60,
            'II': 8.00,
            'III': 8.60,
            '1ю': 9.40,
            '2ю': 10.40,
            '3ю': 11.40,
        },
        0.1: {  # 100 м
            'МСМК': 10.05,
            'МС': 10.44,
            'КМС': 10.84,
            'I': 11.44,
            'II': 12.04,
            'III': 12.94,
            '1ю': 14.14,
            '2ю': 15.74,
            '3ю': 17.34,
        },
        0.2: {  # 200 м
            'МСМК': 20.24,
            'МС': 21.04,
            'КМС': 21.84,
            'I': 23.04,
            'II': 24.24,
            'III': 26.04,
            '1ю': 28.44,
            '2ю': 31.64,
            '3ю': 34.84,
        },
        0.3: {  # 300 м
            'I': 37.00,
            'II': 39.00,
            'III': 42.00,
            '1ю': 46.00,
            '2ю': 51.00,
            '3ю': 56.00,
        },
        0.4: {  # 400 м
            'МСМК': 45.00,
            'МС': 46.80,
            'КМС': 48.60,
            'I': 51.30,
            'II': 54.00,
            'III': 58.00,
            '1ю': time_to_seconds("1:03.40"),
            '2ю': time_to_seconds("1:10.60"),
            '3ю': time_to_seconds("1:17.80"),
        },
        0.6: {  # 600 м
            'I': time_to_seconds("1:28.00"),
            'II': time_to_seconds("1:34.00"),
            'III': time_to_seconds("1:43.00"),
            '1ю': time_to_seconds("1:54.00"),
            '2ю': time_to_seconds("2:08.00"),
            '3ю': time_to_seconds("2:22.00"),
        },
        0.8: {  # 800 м
            'МСМК': time_to_seconds("1:45.20"),
            'МС': time_to_seconds("1:48.60"),
            'КМС': time_to_seconds("1:52.00"),
            'I': time_to_seconds("1:57.50"),
            'II': time_to_seconds("2:03.00"),
            'III': time_to_seconds("2:11.00"),
            '1ю': time_to_seconds("2:23.00"),
            '2ю': time_to_seconds("2:38.00"),
            '3ю': time_to_seconds("2:53.00"),
        },
        1.0: {  # 1000 м
            'I': time_to_seconds("2:35.00"),
            'II': time_to_seconds("2:45.00"),
            'III': time_to_seconds("2:58.00"),
            '1ю': time_to_seconds("3:15.00"),
            '2ю': time_to_seconds("3:35.00"),
            '3ю': time_to_seconds("3:55.00"),
        },
        1.5: {  # 1500 м
            'МСМК': time_to_seconds("3:33.00"),
            'МС': time_to_seconds("3:40.60"),
            'КМС': time_to_seconds("3:48.20"),
            'I': time_to_seconds("4:02.00"),
            'II': time_to_seconds("4:15.80"),
            'III': time_to_seconds("4:35.00"),
            '1ю': time_to_seconds("5:00.00"),
            '2ю': time_to_seconds("5:30.00"),
            '3ю': time_to_seconds("6:00.00"),
        },
        2.0: {  # 2000 м
            'I': time_to_seconds("5:40.00"),
            'II': time_to_seconds("6:00.00"),
            'III': time_to_seconds("6:30.00"),
            '1ю': time_to_seconds("7:05.00"),
            '2ю': time_to_seconds("7:45.00"),
            '3ю': time_to_seconds("8:30.00"),
        },
        3.0: {  # 3000 м
            'МСМК': time_to_seconds("7:39.00"),
            'МС': time_to_seconds("7:54.50"),
            'КМС': time_to_seconds("8:10.00"),
            'I': time_to_seconds("8:40.00"),
            'II': time_to_seconds("9:10.00"),
            'III': time_to_seconds("9:55.00"),
            '1ю': time_to_seconds("10:50.00"),
            '2ю': time_to_seconds("11:55.00"),
            '3ю': time_to_seconds("13:00.00"),
        },
        5.0: {  # 5 км (стадион, автохронометраж)
            'МСМК': time_to_seconds("13:26.55"),
            'МС': time_to_seconds("14:06.83"),
            'КМС': time_to_seconds("14:50.24"),
            'I': time_to_seconds("15:45.24"),
            'II': time_to_seconds("17:00.24"),
            'III': time_to_seconds("18:20.24"),
            '1ю': time_to_seconds("19:50.24"),
            '2ю': time_to_seconds("21:30.24"),
            '3ю': time_to_seconds("23:20.24"),
        },
        10.0: {  # 10 км (стадион, автохронометраж)
            'МСМК': time_to_seconds("28:00.00"),
            'МС': time_to_seconds("29:20.00"),
            'КМС': time_to_seconds("31:10.34"),
            'I': time_to_seconds("33:20.34"),
            'II': time_to_seconds("35:50.34"),
            'III': time_to_seconds("38:40.34"),
            '1ю': time_to_seconds("42:00.00"),
            '2ю': time_to_seconds("46:00.00"),
            '3ю': time_to_seconds("50:00.00"),
        },
        21.1: {  # Полумарафон (шоссе)
            'МСМК': time_to_seconds("1:01:52"),
            'МС': time_to_seconds("1:06:30"),
            'КМС': time_to_seconds("1:12:00"),
            'I': time_to_seconds("1:17:20"),
            'II': time_to_seconds("1:22:35"),
            'III': time_to_seconds("1:28:50"),
        },
        42.2: {  # Марафон (шоссе)
            'МСМК': time_to_seconds("2:14:00"),
            'МС': time_to_seconds("2:22:00"),
            'КМС': time_to_seconds("2:30:30"),
            'I': time_to_seconds("2:40:00"),
            'II': time_to_seconds("2:50:00"),
            'III': time_to_seconds("3:02:00"),
        },
    },
    'women': {
        0.06: {  # 60 м
            'I': 8.40,
            'II': 8.90,
            'III': 9.60,
            '1ю': 10.50,
            '2ю': 11.70,
            '3ю': 12.90,
        },
        0.1: {  # 100 м
            'МСМК': 11.15,
            'МС': 11.60,
            'КМС': 12.05,
            'I': 12.74,
            'II': 13.44,
            'III': 14.44,
            '1ю': 15.84,
            '2ю': 17.64,
            '3ю': 19.44,
        },
        0.2: {  # 200 м
            'МСМК': 22.63,
            'МС': 23.54,
            'КМС': 24.45,
            'I': 25.85,
            'II': 27.24,
            'III': 29.24,
            '1ю': 32.04,
            '2ю': 35.64,
            '3ю': 39.24,
        },
        0.3: {  # 300 м
            'I': 42.00,
            'II': 44.50,
            'III': 48.00,
            '1ю': 52.50,
            '2ю': 58.50,
            '3ю': 64.50,
        },
        0.4: {  # 400 м
            'МСМК': 51.35,
            'МС': 53.40,
            'КМС': 55.45,
            'I': 58.60,
            'II': time_to_seconds("1:01.75"),
            'III': time_to_seconds("1:06.30"),
            '1ю': time_to_seconds("1:12.70"),
            '2ю': time_to_seconds("1:21.30"),
            '3ю': time_to_seconds("1:29.90"),
        },
        0.6: {  # 600 м
            'I': time_to_seconds("1:42.00"),
            'II': time_to_seconds("1:48.50"),
            'III': time_to_seconds("1:58.00"),
            '1ю': time_to_seconds("2:10.00"),
            '2ю': time_to_seconds("2:26.00"),
            '3ю': time_to_seconds("2:42.00"),
        },
        0.8: {  # 800 м
            'МСМК': time_to_seconds("1:59.50"),
            'МС': time_to_seconds("2:04.00"),
            'КМС': time_to_seconds("2:08.50"),
            'I': time_to_seconds("2:16.00"),
            'II': time_to_seconds("2:23.50"),
            'III': time_to_seconds("2:34.50"),
            '1ю': time_to_seconds("2:49.50"),
            '2ю': time_to_seconds("3:09.50"),
            '3ю': time_to_seconds("3:29.50"),
        },
        1.0: {  # 1000 м
            'I': time_to_seconds("3:00.00"),
            'II': time_to_seconds("3:15.00"),
            'III': time_to_seconds("3:30.00"),
            '1ю': time_to_seconds("3:50.00"),
            '2ю': time_to_seconds("4:15.00"),
            '3ю': time_to_seconds("4:40.00"),
        },
        1.5: {  # 1500 м
            'МСМК': time_to_seconds("4:05.50"),
            'МС': time_to_seconds("4:14.50"),
            'КМС': time_to_seconds("4:23.50"),
            'I': time_to_seconds("4:40.00"),
            'II': time_to_seconds("4:56.50"),
            'III': time_to_seconds("5:20.50"),
            '1ю': time_to_seconds("5:50.50"),
            '2ю': time_to_seconds("6:30.50"),
            '3ю': time_to_seconds("7:10.50"),
        },
        2.0: {  # 2000 м
            'I': time_to_seconds("6:35.00"),
            'II': time_to_seconds("7:00.00"),
            'III': time_to_seconds("7:35.00"),
            '1ю': time_to_seconds("8:15.00"),
            '2ю': time_to_seconds("9:05.00"),
            '3ю': time_to_seconds("10:00.00"),
        },
        3.0: {  # 3000 м
            'МСМК': time_to_seconds("8:52.00"),
            'МС': time_to_seconds("9:10.00"),
            'КМС': time_to_seconds("9:28.00"),
            'I': time_to_seconds("10:03.00"),
            'II': time_to_seconds("10:38.00"),
            'III': time_to_seconds("11:30.50"),
            '1ю': time_to_seconds("12:35.50"),
            '2ю': time_to_seconds("13:55.50"),
            '3ю': time_to_seconds("15:15.50"),
        },
        5.0: {  # 5 км (стадион, автохронометраж)
            'МСМК': time_to_seconds("15:10.00"),
            'МС': time_to_seconds("15:21.88"),
            'КМС': time_to_seconds("16:07.05"),
            'I': time_to_seconds("17:20.34"),
            'II': time_to_seconds("18:45.34"),
            'III': time_to_seconds("20:20.34"),
            '1ю': time_to_seconds("22:05.34"),
            '2ю': time_to_seconds("24:00.34"),
            '3ю': time_to_seconds("26:05.34"),
        },
        10.0: {  # 10 км (стадион, автохронометраж)
            'МСМК': time_to_seconds("31:35.00"),
            'МС': time_to_seconds("33:00.00"),
            'КМС': time_to_seconds("34:06.19"),
            'I': time_to_seconds("37:00.34"),
            'II': time_to_seconds("40:00.34"),
            'III': time_to_seconds("43:40.34"),
            '1ю': time_to_seconds("47:30.00"),
            '2ю': time_to_seconds("52:00.00"),
            '3ю': time_to_seconds("56:30.00"),
        },
        21.1: {  # Полумарафон (шоссе)
            'МСМК': time_to_seconds("1:10:40"),
            'МС': time_to_seconds("1:15:58"),
            'КМС': time_to_seconds("1:25:00"),
            'I': time_to_seconds("1:35:00"),
            'II': time_to_seconds("1:46:40"),
            'III': time_to_seconds("2:00:00"),
        },
        42.2: {  # Марафон (шоссе)
            'МСМК': time_to_seconds("2:31:42"),
            'МС': time_to_seconds("2:43:05"),
            'КМС': time_to_seconds("3:00:00"),
            'I': time_to_seconds("3:25:00"),
            'II': time_to_seconds("3:50:00"),
            'III': time_to_seconds("4:15:00"),
        },
    }
}

# Нормативы по плаванию (вольный стиль, бассейн 50м) - ЕВСК 2024
# Источник: https://marathonec.ru/razryadi-normativi-po-plavaniu/
# Действуют с 26 ноября 2024 года
SWIMMING_STANDARDS_50M = {
    'men': {
        0.05: {  # 50м
            'МСМК': 21.91,
            'МС': 23.20,
            'КМС': 23.95,
            'I': 25.20,
            'II': 27.60,
            'III': 29.80,
            '1ю': 35.80,
            '2ю': 45.80,
            '3ю': 55.80,
        },
        0.1: {  # 100м
            'МСМК': 48.25,
            'МС': 51.50,
            'КМС': 54.90,
            'I': 58.30,
            'II': time_to_seconds("1:04.60"),
            'III': time_to_seconds("1:12.10"),
            '1ю': time_to_seconds("1:24.60"),
            '2ю': time_to_seconds("1:44.60"),
            '3ю': time_to_seconds("2:04.60"),
        },
        0.2: {  # 200м
            'МСМК': time_to_seconds("1:46.50"),
            'МС': time_to_seconds("1:53.95"),
            'КМС': time_to_seconds("2:00.65"),
            'I': time_to_seconds("2:08.95"),
            'II': time_to_seconds("2:23.20"),
            'III': time_to_seconds("2:41.70"),
            '1ю': time_to_seconds("3:07.20"),
            '2ю': time_to_seconds("3:47.20"),
            '3ю': time_to_seconds("4:27.20"),
        },
        0.4: {  # 400м
            'МСМК': time_to_seconds("3:47.71"),
            'МС': time_to_seconds("4:02.00"),
            'КМС': time_to_seconds("4:14.50"),
            'I': time_to_seconds("4:31.00"),
            'II': time_to_seconds("5:06.00"),
            'III': time_to_seconds("5:47.00"),
            '1ю': time_to_seconds("6:43.00"),
            '2ю': time_to_seconds("7:39.00"),
            '3ю': time_to_seconds("8:35.00"),
        },
        0.8: {  # 800м
            'МСМК': time_to_seconds("7:52.60"),
            'МС': time_to_seconds("8:25.00"),
            'КМС': time_to_seconds("8:58.00"),
            'I': time_to_seconds("9:37.00"),
            'II': time_to_seconds("11:14.00"),
            'III': time_to_seconds("12:36.00"),
            '1ю': time_to_seconds("14:38.00"),
            '2ю': time_to_seconds("16:38.00"),
            '3ю': time_to_seconds("18:38.00"),
        },
        1.5: {  # 1500м
            'МСМК': time_to_seconds("15:06.19"),
            'МС': time_to_seconds("15:51.00"),
            'КМС': time_to_seconds("17:29.00"),
            'I': time_to_seconds("18:29.00"),
            'II': time_to_seconds("20:50.00"),
            'III': time_to_seconds("23:50.00"),
            '1ю': time_to_seconds("27:52.50"),
            '2ю': time_to_seconds("31:52.50"),
            '3ю': time_to_seconds("35:52.50"),
        },
    },
    'women': {
        0.05: {  # 50м
            'МСМК': 24.82,
            'МС': 26.50,
            'КМС': 27.30,
            'I': 28.60,
            'II': 31.30,
            'III': 33.30,
            '1ю': 40.30,
            '2ю': 50.30,
            '3ю': 59.80,
        },
        0.1: {  # 100м
            'МСМК': 53.99,
            'МС': 57.50,
            'КМС': time_to_seconds("1:01.50"),
            'I': time_to_seconds("1:05.34"),
            'II': time_to_seconds("1:12.90"),
            'III': time_to_seconds("1:20.60"),
            '1ю': time_to_seconds("1:34.60"),
            '2ю': time_to_seconds("1:54.60"),
            '3ю': time_to_seconds("2:13.60"),
        },
        0.2: {  # 200м
            'МСМК': time_to_seconds("1:56.90"),
            'МС': time_to_seconds("2:06.45"),
            'КМС': time_to_seconds("2:14.76"),
            'I': time_to_seconds("2:23.45"),
            'II': time_to_seconds("2:38.20"),
            'III': time_to_seconds("2:57.20"),
            '1ю': time_to_seconds("3:28.20"),
            '2ю': time_to_seconds("4:08.20"),
            '3ю': time_to_seconds("4:46.20"),
        },
        0.4: {  # 400м
            'МСМК': time_to_seconds("4:08.04"),
            'МС': time_to_seconds("4:26.00"),
            'КМС': time_to_seconds("4:41.00"),
            'I': time_to_seconds("4:59.00"),
            'II': time_to_seconds("5:40.00"),
            'III': time_to_seconds("6:24.00"),
            '1ю': time_to_seconds("7:35.00"),
            '2ю': time_to_seconds("8:46.00"),
            '3ю': time_to_seconds("9:57.00"),
        },
        0.8: {  # 800м
            'МСМК': time_to_seconds("8:31.12"),
            'МС': time_to_seconds("9:08.00"),
            'КМС': time_to_seconds("9:42.00"),
            'I': time_to_seconds("10:23.00"),
            'II': time_to_seconds("11:54.00"),
            'III': time_to_seconds("13:27.00"),
            '1ю': time_to_seconds("16:12.00"),
            '2ю': time_to_seconds("18:42.00"),
            '3ю': time_to_seconds("21:12.00"),
        },
        1.5: {  # 1500м
            'МСМК': time_to_seconds("16:20.88"),
            'МС': time_to_seconds("17:35.00"),
            'КМС': time_to_seconds("18:44.00"),
            'I': time_to_seconds("20:27.00"),
            'II': time_to_seconds("22:57.00"),
            'III': time_to_seconds("26:20.00"),
            '1ю': time_to_seconds("30:27.50"),
            '2ю': time_to_seconds("34:32.50"),
            '3ю': time_to_seconds("38:42.50"),
        },
    }
}

# Нормативы по плаванию (вольный стиль, бассейн 25м) - ЕВСК 2024
SWIMMING_STANDARDS_25M = {
    'men': {
        0.05: {  # 50м
            'МСМК': 21.18,
            'МС': 22.45,
            'КМС': 23.20,
            'I': 24.45,
            'II': 26.85,
            'III': 29.05,
            '1ю': 35.05,
            '2ю': 45.05,
            '3ю': 55.05,
        },
        0.1: {  # 100м
            'МСМК': 46.72,
            'МС': 50.00,
            'КМС': 53.30,
            'I': 56.70,
            'II': time_to_seconds("1:03.10"),
            'III': time_to_seconds("1:10.60"),
            '1ю': time_to_seconds("1:23.10"),
            '2ю': time_to_seconds("1:43.10"),
            '3ю': time_to_seconds("2:03.10"),
        },
        0.2: {  # 200м
            'МСМК': time_to_seconds("1:43.02"),
            'МС': time_to_seconds("1:50.95"),
            'КМС': time_to_seconds("1:57.45"),
            'I': time_to_seconds("2:05.70"),
            'II': time_to_seconds("2:20.20"),
            'III': time_to_seconds("2:38.70"),
            '1ю': time_to_seconds("3:04.20"),
            '2ю': time_to_seconds("3:45.00"),
            '3ю': time_to_seconds("4:24.20"),
        },
        0.4: {  # 400м
            'МСМК': time_to_seconds("3:40.94"),
            'МС': time_to_seconds("3:56.00"),
            'КМС': time_to_seconds("4:08.50"),
            'I': time_to_seconds("4:25.00"),
            'II': time_to_seconds("5:00.00"),
            'III': time_to_seconds("5:41.00"),
            '1ю': time_to_seconds("6:37.00"),
            '2ю': time_to_seconds("7:33.00"),
            '3ю': time_to_seconds("8:29.00"),
        },
        0.8: {  # 800м
            'МСМК': time_to_seconds("7:42.70"),
            'МС': time_to_seconds("8:17.00"),
            'КМС': time_to_seconds("8:50.00"),
            'I': time_to_seconds("9:24.00"),
            'II': time_to_seconds("11:02.00"),
            'III': time_to_seconds("12:24.00"),
            '1ю': time_to_seconds("14:26.00"),
            '2ю': time_to_seconds("16:26.00"),
            '3ю': time_to_seconds("18:26.00"),
        },
        1.5: {  # 1500м
            'МСМК': time_to_seconds("14:44.74"),
            'МС': time_to_seconds("15:28.50"),
            'КМС': time_to_seconds("17:06.50"),
            'I': time_to_seconds("18:05.00"),
            'II': time_to_seconds("20:27.50"),
            'III': time_to_seconds("23:27.50"),
            '1ю': time_to_seconds("27:30.00"),
            '2ю': time_to_seconds("31:30.00"),
            '3ю': time_to_seconds("35:30.00"),
        },
    },
    'women': {
        0.05: {  # 50м
            'МСМК': 24.13,
            'МС': 25.75,
            'КМС': 26.55,
            'I': 27.85,
            'II': 30.55,
            'III': 32.55,
            '1ю': 39.55,
            '2ю': 49.55,
            '3ю': 59.05,
        },
        0.1: {  # 100м
            'МСМК': 52.68,
            'МС': 56.00,
            'КМС': time_to_seconds("1:00.00"),
            'I': time_to_seconds("1:03.84"),
            'II': time_to_seconds("1:11.40"),
            'III': time_to_seconds("1:19.10"),
            '1ю': time_to_seconds("1:33.10"),
            '2ю': time_to_seconds("1:53.10"),
            '3ю': time_to_seconds("2:12.10"),
        },
        0.2: {  # 200м
            'МСМК': time_to_seconds("1:55.02"),
            'МС': time_to_seconds("2:03.45"),
            'КМС': time_to_seconds("2:11.75"),
            'I': time_to_seconds("2:20.45"),
            'II': time_to_seconds("2:36.20"),
            'III': time_to_seconds("2:54.20"),
            '1ю': time_to_seconds("3:25.20"),
            '2ю': time_to_seconds("4:05.20"),
            '3ю': time_to_seconds("4:43.20"),
        },
        0.4: {  # 400м
            'МСМК': time_to_seconds("4:03.32"),
            'МС': time_to_seconds("4:20.00"),
            'КМС': time_to_seconds("4:30.00"),
            'I': time_to_seconds("4:52.00"),
            'II': time_to_seconds("5:34.00"),
            'III': time_to_seconds("6:18.00"),
            '1ю': time_to_seconds("7:29.00"),
            '2ю': time_to_seconds("8:40.00"),
            '3ю': time_to_seconds("9:51.00"),
        },
        0.8: {  # 800м
            'МСМК': time_to_seconds("8:23.99"),
            'МС': time_to_seconds("9:00.00"),
            'КМС': time_to_seconds("9:30.00"),
            'I': time_to_seconds("10:11.00"),
            'II': time_to_seconds("11:42.00"),
            'III': time_to_seconds("13:15.00"),
            '1ю': time_to_seconds("16:00.00"),
            '2ю': time_to_seconds("18:30.00"),
            '3ю': time_to_seconds("21:00.00"),
        },
        1.5: {  # 1500м
            'МСМК': time_to_seconds("16:12.06"),
            'МС': time_to_seconds("17:12.50"),
            'КМС': time_to_seconds("18:21.50"),
            'I': time_to_seconds("20:04.50"),
            'II': time_to_seconds("22:34.50"),
            'III': time_to_seconds("25:57.50"),
            '1ю': time_to_seconds("30:05.00"),
            '2ю': time_to_seconds("34:10.00"),
            '3ю': time_to_seconds("38:20.00"),
        },
    }
}


def get_qualification_running(distance_km: float, time_seconds: float, gender: str) -> Optional[str]:
    """
    Определяет разряд по бегу на основе дистанции и времени.

    Args:
        distance_km: Дистанция в километрах (5.0, 10.0, 21.1, 42.2)
        time_seconds: Время прохождения дистанции в секундах
        gender: Пол ('male' или 'female')

    Returns:
        Строка с разрядом (МСМК, МС, КМС, I, II, III, 1ю, 2ю, 3ю, бр) или None
    """
    gender_key = 'men' if gender.lower() in ['male', 'м', 'мужской'] else 'women'

    # Проверяем, есть ли нормативы для данной дистанции
    if distance_km not in RUNNING_STANDARDS[gender_key]:
        return None

    standards = RUNNING_STANDARDS[gender_key][distance_km]

    # Проверяем от высшего разряда к низшему
    for rank in ['МСМК', 'МС', 'КМС', 'I', 'II', 'III', '1ю', '2ю', '3ю']:
        if rank in standards and time_seconds <= standards[rank]:
            return rank

    # Если результат медленнее самого низкого разряда - без разряда
    return 'бр'


def get_qualification_swimming(distance_km: float, time_seconds: float, gender: str, pool_length: int = 50) -> Optional[str]:
    """
    Определяет разряд по плаванию на основе дистанции и времени.

    Args:
        distance_km: Дистанция в километрах (0.05, 0.1, 0.2, 0.4, 0.8, 1.5)
        time_seconds: Время прохождения дистанции в секундах
        gender: Пол ('male' или 'female')
        pool_length: Длина бассейна (25 или 50 метров)

    Returns:
        Строка с разрядом (МСМК, МС, КМС, I, II, III, 1ю, 2ю, 3ю, бр) или None
    """
    gender_key = 'men' if gender.lower() in ['male', 'м', 'мужской'] else 'women'

    # Выбираем нормативы в зависимости от длины бассейна
    standards_dict = SWIMMING_STANDARDS_50M if pool_length == 50 else SWIMMING_STANDARDS_25M

    # Проверяем, есть ли нормативы для данной дистанции
    if distance_km not in standards_dict[gender_key]:
        return None

    standards = standards_dict[gender_key][distance_km]

    # Проверяем от высшего разряда к низшему
    for rank in ['МСМК', 'МС', 'КМС', 'I', 'II', 'III', '1ю', '2ю', '3ю']:
        if rank in standards and time_seconds <= standards[rank]:
            return rank

    # Если результат медленнее самого низкого разряда - без разряда
    return 'бр'


def get_qualification(sport_type: str, distance_km: float, time_seconds: float, gender: str, **kwargs) -> Optional[str]:
    """
    Универсальная функция для определения разряда.

    Args:
        sport_type: Тип спорта ('running', 'swimming', 'cycling', 'бег', 'плавание', 'велоспорт')
        distance_km: Дистанция в километрах
        time_seconds: Время прохождения дистанции в секундах
        gender: Пол ('male' или 'female')
        **kwargs: Дополнительные параметры (например, pool_length для плавания)

    Returns:
        Строка с разрядом или None
    """
    if sport_type.lower() in ['running', 'бег', 'легкая атлетика']:
        return get_qualification_running(distance_km, time_seconds, gender)
    elif sport_type.lower() in ['swimming', 'плавание']:
        pool_length = kwargs.get('pool_length', 50)
        return get_qualification_swimming(distance_km, time_seconds, gender, pool_length)
    elif sport_type.lower() in ['cycling', 'велоспорт']:
        # Для велоспорта разряды присваиваются по занятым местам, а не по времени
        # Здесь нужна другая логика
        return None

    return None


def format_qualification(rank: Optional[str]) -> str:
    """
    Форматирует разряд для отображения.

    Args:
        rank: Строка с разрядом (МСМК, МС, КМС, I, II, III, 1ю, 2ю, 3ю)

    Returns:
        Отформатированная строка
    """
    if not rank:
        return ""

    rank_names = {
        'МСМК': 'МСМК (Мастер спорта международного класса)',
        'МС': 'МС (Мастер спорта)',
        'КМС': 'КМС (Кандидат в мастера спорта)',
        'I': 'I разряд',
        'II': 'II разряд',
        'III': 'III разряд',
        '1ю': 'I юношеский разряд',
        '2ю': 'II юношеский разряд',
        '3ю': 'III юношеский разряд',
    }

    return rank_names.get(rank, rank)
