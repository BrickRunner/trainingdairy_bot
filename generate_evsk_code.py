"""
Генерация Python кода с нормативами ЕВСК из официального файла ВФЛА
"""
import pandas as pd
import sys
import io

# UTF-8 для вывода
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Читаем файл
df = pd.read_excel('evsk_running.xls', sheet_name='нормы', header=None)

def parse_time_for_python(val):
    """Преобразуем значение во время для Python кода"""
    s = str(val).strip().replace(',', '.')
    # Формат 1.01:52 -> 1:01:52
    if '.' in s and ':' in s:
        parts = s.split('.')
        if len(parts) == 2 and len(parts[0]) <= 2:
            s = parts[0] + ':' + parts[1]
    return s

# Строки для мужчин (известные из анализа)
rows_men = {
    0.06: 10,   # 60м
    0.1: 12,    # 100м
    0.2: 14,    # 200м
    0.3: 16,    # 300м
    0.4: 20,    # 400м круг 200м
    0.6: 22,    # 600м
    0.8: 24,    # 800м
    1.0: 28,    # 1000м
    1.5: 32,    # 1500м круг 200м
    3.0: 36,    # 3000м (автохронометраж нужно найти)
    5.0: 40,    # 5000м
    10.0: 42,   # 10000м
    15.0: 43,   # 15км шоссе
    21.1: 44,   # полумарафон
    42.2: 45,   # марафон
    100.0: 46,  # 100км
}

standards = {'men': {}, 'women': {}}

# Извлекаем мужские нормативы
for dist_km, row_idx in rows_men.items():
    row = df.iloc[row_idx]
    ranks = {}
    rank_names = ['МСМК', 'МС', 'КМС', 'I', 'II', 'III', '1ю', '2ю', '3ю']
    rank_cols = [5, 6, 7, 8, 9, 10, 11, 12, 13]

    for rank_name, col_idx in zip(rank_names, rank_cols):
        val = row[col_idx]
        if pd.notna(val) and str(val).strip() and str(val) != 'nan':
            time_val = parse_time_for_python(val)
            ranks[rank_name] = time_val

    if ranks:
        standards['men'][dist_km] = ranks

# Ищем 3000м авто для мужчин
for idx in range(35, 40):
    row = df.iloc[idx]
    if pd.notna(row[1]) and '3000' in str(row[1]):
        for offset in range(1, 4):
            check_row = df.iloc[idx + offset]
            chrono = str(check_row[3]) if pd.notna(check_row[3]) else ''
            if 'Авто' in chrono and '400' not in chrono:  # Не круг 400м
                ranks = {}
                rank_names = ['МСМК', 'МС', 'КМС', 'I', 'II', 'III', '1ю', '2ю', '3ю']
                rank_cols = [5, 6, 7, 8, 9, 10, 11, 12, 13]
                for rank_name, col_idx in zip(rank_names, rank_cols):
                    val = check_row[col_idx]
                    if pd.notna(val) and str(val).strip():
                        time_val = parse_time_for_python(val)
                        ranks[rank_name] = time_val
                if ranks:
                    standards['men'][3.0] = ranks
                break

# Теперь ищем женские нормативы (начинаются примерно со строки 80)
print("=== ПОИСК ЖЕНСКИХ НОРМАТИВОВ ===\n")
women_start = None
for idx in range(50, 150):
    row = df.iloc[idx]
    if pd.notna(row[0]) and 'ЖЕНСКИЙ' in str(row[0]):
        women_start = idx
        print(f"Найдено начало женских нормативов на строке {idx}\n")
        break

if women_start:
    # Аналогично мужским, смещение примерно +73
    offset = women_start - 6  # 6 - это строка с "МУЖСКОЙ ПОЛ"
    rows_women = {k: v + offset for k, v in rows_men.items()}

    for dist_km, row_idx in rows_women.items():
        if row_idx >= len(df):
            continue
        row = df.iloc[row_idx]
        ranks = {}
        rank_names = ['МСМК', 'МС', 'КМС', 'I', 'II', 'III', '1ю', '2ю', '3ю']
        rank_cols = [5, 6, 7, 8, 9, 10, 11, 12, 13]

        for rank_name, col_idx in zip(rank_names, rank_cols):
            val = row[col_idx]
            if pd.notna(val) and str(val).strip() and str(val) != 'nan':
                time_val = parse_time_for_python(val)
                ranks[rank_name] = time_val

        if ranks:
            standards['women'][dist_km] = ranks

# Генерируем Python код
print("\n\n" + "="*70)
print("PYTHON КОД ДЛЯ qualifications.py")
print("="*70 + "\n")

print("RUNNING_STANDARDS = {")
for gender in ['men', 'women']:
    print(f"    '{gender}': {{")
    for dist_km in sorted(standards[gender].keys()):
        dist_m = int(dist_km * 1000)
        print(f"        {dist_km}: {{  # {dist_m} м")
        for rank, value in standards[gender][dist_km].items():
            if ':' in value:
                print(f"            '{rank}': time_to_seconds(\"{value}\"),")
            else:
                print(f"            '{rank}': {value},")
        print("        },")
    print("    },")
print("}")

print("\n\n=== СТАТИСТИКА ===")
print(f"Мужчины: {len(standards['men'])} дистанций")
print(f"Женщины: {len(standards['women'])} дистанций")
print(f"\nДистанции (мужчины): {sorted(standards['men'].keys())}")
print(f"Дистанции (женщины): {sorted(standards['women'].keys())}")
