"""Проверка данных велоспорта из БД"""
import sqlite3

conn = sqlite3.connect('database.sqlite')
cursor = conn.execute("""
    SELECT distance, discipline, gender, rank, time_seconds
    FROM cycling_standards
    WHERE version = 'EVSK 2022-2025 (frs24.ru)'
    ORDER BY distance, discipline, gender, time_seconds
    LIMIT 15
""")

print('Distance | Discipline              | Gender | Rank    | Time(sec)')
print('-' * 75)
for row in cursor:
    minutes = int(row[4] // 60)
    seconds = int(row[4] % 60)
    print(f'{row[0]:8.1f} | {row[1]:23s} | {row[2]:6s} | {row[3]:7s} | {row[4]:8.1f} ({minutes:02d}:{seconds:02d})')

cursor.close()
conn.close()
