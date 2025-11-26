"""
Извлечение нормативов ЕВСК из официального файла ВФЛА
ТОЛЬКО АВТОХРОНОМЕТРАЖ, круг 200м для 400м и 1500м
"""
import pandas as pd
import sys
import io

# UTF-8 для вывода
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Читаем файл
df = pd.read_excel('evsk_running.xls', sheet_name='нормы', header=None)

def parse_time(val):
    """Преобразуем значение в строку времени"""
    s = str(val).strip()
    # Убираем пробелы
    s = s.replace(' ', '')
    # Заменяем точку на двоеточие для времени
    if '.' in s and ':' not in s and len(s.split('.')[0]) <= 2:
        # Это формат ч.мм:сс
        parts = s.split('.')
        if len(parts) == 2 and ':' in parts[1]:
            s = parts[0] + ':' + parts[1]
    return s

# Мануально извлекаем нужные дистанции
standards = {
    'men': {},
    'women': {}
}

# Для мужчин - строки известны из анализа
rows_men = {
    0.06: 10,   # 60м - автохронометраж
    0.1: 12,    # 100м - автохронометраж
    0.2: 14,    # 200м - автохронометраж
    0.3: 16,    # 300м - автохронометраж
    0.4: 20,    # 400м - круг 200м автохронометраж
    0.6: 22,    # 600м - автохронометраж
    0.8: 24,    # 800м - автохронометраж
    1.0: 28,    # 1000м - автохронометраж
    1.5: 32,    # 1500м - круг 200м автохронометраж
    3.0: 36,    # 3000м - автохронометраж (нужно найти)
    5.0: 40,    # 5000м - автохронометраж
    10.0: 42,   # 10000м - автохронометраж
}

print("=== ИЗВЛЕЧЕНИЕ НОРМАТИВОВ МУЖЧИНЫ ===\n")

for dist_km, row_idx in rows_men.items():
    row = df.iloc[row_idx]
    print(f"\nДистанция: {dist_km} км (строка {row_idx})")

    ranks = {}
    rank_names = ['МСМК', 'МС', 'КМС', 'I', 'II', 'III', '1ю', '2ю', '3ю']
    rank_cols = [5, 6, 7, 8, 9, 10, 11, 12, 13]

    for rank_name, col_idx in zip(rank_names, rank_cols):
        val = row[col_idx]
        if pd.notna(val) and str(val).strip() and str(val) != 'nan':
            time_val = parse_time(val)
            print(f"  {rank_name}: {time_val}")
            ranks[rank_name] = time_val

    if ranks:
        standards['men'][dist_km] = ranks

# Ищем 3000м автохронометраж для мужчин
print("\n\nПОИСК 3000м автохронометраж:")
for idx in range(35, 45):
    row = df.iloc[idx]
    if pd.notna(row[1]) and '3000' in str(row[1]):
        print(f"Строка {idx}: {row[1]}")
        # Проверяем следующие строки на автохронометраж
        for offset in range(1, 4):
            check_row = df.iloc[idx + offset]
            chrono = str(check_row[3]) if pd.notna(check_row[3]) else ''
            if 'Авто' in chrono:
                print(f"  Найден автохронометраж на строке {idx + offset}")
                ranks = {}
                rank_names = ['МСМК', 'МС', 'КМС', 'I', 'II', 'III', '1ю', '2ю', '3ю']
                rank_cols = [5, 6, 7, 8, 9, 10, 11, 12, 13]
                for rank_name, col_idx in zip(rank_names, rank_cols):
                    val = check_row[col_idx]
                    if pd.notna(val) and str(val).strip():
                        time_val = parse_time(val)
                        print(f"    {rank_name}: {time_val}")
                        ranks[rank_name] = time_val
                if ranks:
                    standards['men'][3.0] = ranks
                break

# Ищем шоссейные дистанции
print("\n\nПОИСК ШОССЕЙНЫХ ДИСТАНЦИЙ:")
for idx in range(40, 50):
    row = df.iloc[idx]
    disc = str(row[1]) if pd.notna(row[1]) else ''
    if 'шоссе' in disc or '21,0975' in disc or '42,195' in disc or '15 км' in disc or '100 км' in disc:
        print(f"\nСтрока {idx}: {disc}")
        # Проверяем строки на автохронометраж
        for offset in range(0, 3):
            check_row = df.iloc[idx + offset]
            chrono = str(check_row[3]) if pd.notna(check_row[3]) else ''

            if 'Авто' in chrono or 'шоссе' in chrono:
                print(f"  Хронометраж: {chrono}")

                # Определяем дистанцию
                if '15 км' in disc or '15000' in disc:
                    dist_km = 15.0
                elif '21' in disc:
                    dist_km = 21.1
                elif '42' in disc:
                    dist_km = 42.2
                elif '100 км' in disc or '100000' in disc:
                    dist_km = 100.0
                else:
                    continue

                ranks = {}
                rank_names = ['МСМК', 'МС', 'КМС', 'I', 'II', 'III', '1ю', '2ю', '3ю']
                rank_cols = [5, 6, 7, 8, 9, 10, 11, 12, 13]
                for rank_name, col_idx in zip(rank_names, rank_cols):
                    val = check_row[col_idx]
                    if pd.notna(val) and str(val).strip() and str(val) != 'nan':
                        time_val = parse_time(val)
                        print(f"    {rank_name}: {time_val}")
                        ranks[rank_name] = time_val
                if ranks:
                    standards['men'][dist_km] = ranks
                break

print("\n\n=== ИТОГОВЫЕ ДИСТАНЦИИ (МУЖЧИНЫ) ===")
print("Найдено дистанций:", len(standards['men']))
print("Дистанции:", sorted(standards['men'].keys()))
