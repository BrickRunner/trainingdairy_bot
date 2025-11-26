"""
Извлечение нормативов ЕВСК из официального файла ВФЛА
ТОЛЬКО АВТОХРОНОМЕТРАЖ, круг 200м (конец осени - начало весны)
"""
import pandas as pd
import sys
import io
import re

# UTF-8 для вывода
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Читаем файл
df = pd.read_excel('evsk_running.xls', sheet_name='нормы', header=None)

print("=== НОРМАТИВЫ БЕГА ДЛЯ МУЖЧИН (ТОЛЬКО АВТОХРОНОМЕТРАЖ, КРУГ 200М) ===\n")

standards_men = {}
standards_women = {}
current_gender = 'men'

for idx in range(5, len(df)):
    row = df.iloc[idx]

    # Переключаемся на женщин
    if pd.notna(row[0]) and 'ЖЕНСКИЙ' in str(row[0]):
        current_gender = 'women'
        print("\n\n=== ПЕРЕХОД К ЖЕНСКИМ НОРМАТИВАМ ===\n")
        continue

    # Проверяем, есть ли название дисциплины
    if pd.notna(row[1]):
        discipline = str(row[1]).strip()

        # Пропускаем всё кроме простого бега
        if 'Бег' not in discipline:
            continue
        if any(x in discipline for x in ['барьер', 'эстафет', 'препятствием', '2000']):
            continue

        # Извлекаем дистанцию
        distance_match = re.search(r'(\d+)\s*м', discipline)
        if not distance_match:
            # Проверяем километры
            distance_match = re.search(r'(\d+(?:,\d+)?)\s*км', discipline)
            if distance_match:
                distance_km = float(distance_match.group(1).replace(',', '.'))
                distance_m = int(distance_km * 1000)
            else:
                continue
        else:
            distance_m = int(distance_match.group(1))
            distance_km = distance_m / 1000

        # Ищем строки с автохронометражем
        # Проверяем текущую и следующие 3 строки
        for offset in range(4):
            check_idx = idx + offset
            if check_idx >= len(df):
                break

            check_row = df.iloc[check_idx]
            chrono = str(check_row[3]) if pd.notna(check_row[3]) else ''

            # ТОЛЬКО автохронометраж
            if 'Автохронометраж' not in chrono:
                continue

            # Для 400м и 1500м проверяем круг 200м
            if distance_m in [400, 1500]:
                if 'Круг 200' not in chrono:
                    continue

            # Извлекаем нормативы
            print(f"\n{distance_m}м ({distance_km} км) - автохронометраж:")

            ranks = {}
            rank_names = ['МСМК', 'МС', 'КМС', 'I', 'II', 'III', '1ю', '2ю', '3ю']
            rank_cols = [5, 6, 7, 8, 9, 10, 11, 12, 13]

            for rank_name, col_idx in zip(rank_names, rank_cols):
                val = check_row[col_idx]
                if pd.notna(val) and str(val).strip() and str(val) != 'nan':
                    print(f"  {rank_name}: {val}")
                    ranks[rank_name] = str(val)

            if ranks:
                if current_gender == 'men':
                    standards_men[distance_km] = ranks
                else:
                    standards_women[distance_km] = ranks

            break  # Нашли автохронометраж, переходим к следующей дистанции

print("\n\n=== ИТОГОВЫЕ ДИСТАНЦИИ (МУЖЧИНЫ) ===")
print("Дистанции:", sorted(standards_men.keys()))

print("\n\n=== ИТОГОВЫЕ ДИСТАНЦИИ (ЖЕНЩИНЫ) ===")
print("Дистанции:", sorted(standards_women.keys()))
