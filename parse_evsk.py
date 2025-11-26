"""
Скрипт для парсинга таблицы ЕВСК по легкой атлетике
"""
import pandas as pd
import sys

# Устанавливаем UTF-8 для вывода
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Читаем Excel файл
xls = pd.ExcelFile('evsk_running.xls')

print("=== ЛИСТЫ В ФАЙЛЕ ===")
for i, sheet_name in enumerate(xls.sheet_names):
    print(f"{i}: {sheet_name}")

print("\n=== ЧИТАЕМ КАЖДЫЙ ЛИСТ ===")
for sheet_name in xls.sheet_names:
    print(f"\n\n{'='*60}")
    print(f"ЛИСТ: {sheet_name}")
    print('='*60)

    df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
    print(f"Размер: {df.shape[0]} строк x {df.shape[1]} колонок")
    print("\nПервые 50 строк:")

    # Выводим построчно для лучшей читаемости
    for idx, row in df.head(50).iterrows():
        values = ' | '.join([str(v) if pd.notna(v) else '' for v in row])
        if values.strip(' |'):  # Пропускаем полностью пустые строки
            print(f"{idx:3d}: {values}")
