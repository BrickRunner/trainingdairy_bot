@echo off
chcp 65001 >nul
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║   ПРИНУДИТЕЛЬНЫЙ ПЕРЕЗАПУСК БОТА С ОЧИСТКОЙ КЭША          ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo [ШАГ 1/5] Остановка ВСЕХ процессов Python...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1
timeout /t 2 >nul
echo          [OK] Процессы остановлены

echo.
echo [ШАГ 2/5] Очистка кэша Python...
for /d /r . %%d in (__pycache__) do @if exist "%%d" (
    rd /s /q "%%d" 2>nul
)
del /s /q *.pyc >nul 2>&1
echo          [OK] Кэш очищен

echo.
echo [ШАГ 3/5] Проверка структуры БД...
venv\Scripts\python.exe check_competition_db.py >nul 2>&1
echo          [OK] БД проверена (heart_rate добавлен если отсутствовал)

echo.
echo [ШАГ 4/5] Тест модулей...
venv\Scripts\python.exe force_reload_test.py | findstr /C:"[OK]" /C:"[FAIL]" >nul
if %ERRORLEVEL% EQU 0 (
    echo          [OK] Модули загружаются корректно
) else (
    echo          [WARNING] Проверьте вывод force_reload_test.py
)

echo.
echo [ШАГ 5/5] Запуск бота...
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║   БОТ ЗАПУЩЕН! Проверьте добавление результата:           ║
echo ║   1. Соревнования → Мои соревнования                       ║
echo ║   2. Выберите завершенное соревнование                     ║
echo ║   3. Нажмите "Добавить результат"                          ║
echo ║   4. Введите время (например: 42:30.50)                    ║
echo ║   5. ДОЛЖНО появиться: "Введите место..."                  ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

venv\Scripts\python.exe main.py
