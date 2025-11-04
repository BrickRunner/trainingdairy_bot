@echo off
chcp 65001 >nul
cls

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║         ПРИНУДИТЕЛЬНЫЙ ПЕРЕЗАПУСК БОТА С ОЧИСТКОЙ КЭША       ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

echo [1/5] Остановка всех процессов Python...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM pythonw.exe /T >nul 2>&1
timeout /t 2 >nul
echo      [OK] Процессы остановлены
echo.

echo [2/5] Удаление кэша Python (__pycache__)...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
echo      [OK] Кэш __pycache__ удалён
echo.

echo [3/5] Удаление .pyc файлов...
del /s /q *.pyc >nul 2>&1
echo      [OK] Файлы .pyc удалены
echo.

echo [4/5] Проверка критических файлов...
if not exist "venv\Scripts\python.exe" (
    echo      [ОШИБКА] venv не найден!
    pause
    exit /b 1
)
if not exist "main.py" (
    echo      [ОШИБКА] main.py не найден!
    pause
    exit /b 1
)
echo      [OK] Все файлы на месте
echo.

echo [5/5] Запуск бота...
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║  БОТ ЗАПУСКАЕТСЯ С ЧИСТЫМ КЭШЕМ!                             ║
echo ║                                                                ║
echo ║  ИСПРАВЛЕНО:                                                   ║
echo ║  ✓ Ввод пульса при добавлении результата                       ║
echo ║  ✓ Ввод места в общем зачёте                                   ║
echo ║  ✓ Ввод места в возрастной категории                           ║
echo ║  ✓ Календарь для прошедших соревнований                        ║
echo ║                                                                ║
echo ║  КАК ПРОВЕРИТЬ:                                                ║
echo ║  1. Соревнования → Мои соревнования                            ║
echo ║  2. Выберите ПРОШЕДШЕЕ соревнование                            ║
echo ║  3. Нажмите "Добавить результат"                               ║
echo ║  4. Пройдите 4 шага: ВРЕМЯ → МЕСТО → КАТЕГОРИЯ → ПУЛЬС        ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

venv\Scripts\python.exe main.py
