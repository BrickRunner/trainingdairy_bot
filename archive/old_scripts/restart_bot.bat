@echo off
echo ================================================
echo Перезапуск бота с полной очисткой кэша
echo ================================================

echo.
echo [1/4] Останавливаем процесс Python...
taskkill /F /IM python.exe 2>nul
timeout /t 2 >nul

echo.
echo [2/4] Очищаем кэш Python (__pycache__ и .pyc)...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /s /q *.pyc 2>nul

echo.
echo [3/4] Компилируем обновленные модули...
venv\Scripts\python.exe -m py_compile bot\fsm.py
venv\Scripts\python.exe -m py_compile competitions\competitions_handlers.py
venv\Scripts\python.exe -m py_compile competitions\competitions_queries.py
venv\Scripts\python.exe -m py_compile utils\time_formatter.py

echo.
echo [4/4] Запускаем бота...
echo.
echo ================================================
echo Бот перезапущен! Проверьте работу обработчиков.
echo ================================================
echo.
venv\Scripts\python.exe main.py
