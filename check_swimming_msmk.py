"""Проверка нормативов МСМК по плаванию"""
import sqlite3

conn = sqlite3.connect('database.sqlite')
cursor = conn.execute("""
    SELECT distance, gender, pool_length, rank, time_seconds
    FROM swimming_standards
    WHERE version = 'EVSK 2022-2025 (frs24.ru)'
      AND rank LIKE '%СМК%'
      AND distance IN (0.05, 0.1, 0.2)
      AND pool_length = 50
    ORDER BY distance, gender
""")

print('Distance | Gender | Pool | Rank    | Time(sec)')
print('-' * 55)
for row in cursor:
    print(f'{row[0]:.2f}     | {row[1]:6s} | {row[2]:4d} | {row[3]:7s} | {row[4]:.2f}')

conn.close()
