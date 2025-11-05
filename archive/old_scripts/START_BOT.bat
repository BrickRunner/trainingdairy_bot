@echo off
chcp 65001 >nul
cls

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                     ЗАПУСК БОТА                               ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

echo [1/3] Очистка кэша Python...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
del /s /q *.pyc >nul 2>&1
echo      [OK] Кэш очищен

echo.
echo [2/3] Проверка БД...
venv\Scripts\python.exe -c "import asyncio, aiosqlite, os; asyncio.run((lambda: (lambda db: db.execute('ALTER TABLE competition_participants ADD COLUMN heart_rate INTEGER'))(aiosqlite.connect(os.getenv('DB_PATH', 'bot_data.db'))))())" 2>nul
echo      [OK] БД готова

echo.
echo [3/3] Запуск бота...
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║  БОТ ЗАПУЩЕН!                                                 ║
echo ║                                                                ║
echo ║  Как проверить:                                                ║
echo ║  1. Соревнования → Мои соревнования                            ║
echo ║  2. Выберите ПРОШЕДШЕЕ соревнование                            ║
echo ║  3. Должна появиться кнопка "Добавить результат"               ║
echo ║  4. Нажмите её                                                 ║
echo ║  5. Введите время (например: 42:30.50)                         ║
echo ║  6. Должен запроситься: МЕСТО, КАТЕГОРИЯ, ПУЛЬС                ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

venv\Scripts\python.exe main.py
