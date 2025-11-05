import sqlite3

conn = sqlite3.connect('database.sqlite')
cursor = conn.execute('PRAGMA table_info(user_settings)')
print('user_settings columns:')
for row in cursor:
    print(f'  {row[1]} ({row[2]})')

# Проверяем coach_links
cursor = conn.execute('PRAGMA table_info(coach_links)')
print('\ncoach_links columns:')
for row in cursor:
    print(f'  {row[1]} ({row[2]})')

conn.close()
print('\nDatabase structure check complete!')
