@echo off
chcp 65001 >nul
cls

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║            ОЧИСТКА ПРОЕКТА ОТ ВРЕМЕННЫХ ФАЙЛОВ               ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo ⚠️  ВНИМАНИЕ: Будут удалены/перемещены временные файлы!
echo.
echo Нажмите любую клавишу для продолжения или Ctrl+C для отмены...
pause >nul

echo.
echo [1/7] Создание архивной структуры...
if not exist "archive" mkdir archive
if not exist "archive\old_tests" mkdir archive\old_tests
if not exist "archive\old_migrations" mkdir archive\old_migrations
if not exist "archive\old_docs" mkdir archive\old_docs
if not exist "archive\old_scripts" mkdir archive\old_scripts
echo      [OK] Архивные папки созданы
echo.

echo [2/7] Перемещение тестовых файлов...
move /Y check_*.py archive\old_tests\ 2>nul
move /Y test_*.py archive\old_tests\ 2>nul
move /Y debug_*.py archive\old_tests\ 2>nul
move /Y diagnose_*.py archive\old_tests\ 2>nul
move /Y *_FIX.* archive\old_tests\ 2>nul
move /Y SIMULATION_TEST.py archive\old_tests\ 2>nul
move /Y EMERGENCY_FIX.py archive\old_tests\ 2>nul
move /Y FINAL_CHECK.py archive\old_tests\ 2>nul
move /Y force_reload_test.py archive\old_tests\ 2>nul
echo      [OK] Тестовые файлы перемещены
echo.

echo [3/7] Перемещение старых миграций...
move /Y add_goal_notification_field.py archive\old_migrations\ 2>nul
move /Y add_goal_notifications_field.py archive\old_migrations\ 2>nul
move /Y add_test_competitions.py archive\old_migrations\ 2>nul
move /Y add_timezone_migration.py archive\old_migrations\ 2>nul
move /Y migrate_coach_features.py archive\old_migrations\ 2>nul
move /Y migrate_coach_mode.py archive\old_migrations\ 2>nul
move /Y migrate_competitions.py archive\old_migrations\ 2>nul
move /Y migrate_health_table.py archive\old_migrations\ 2>nul
echo      [OK] Миграции перемещены
echo.

echo [4/7] Перемещение старых документов...
move /Y DEBUG_INSTRUCTIONS.md archive\old_docs\ 2>nul
move /Y FINAL_FIX.md archive\old_docs\ 2>nul
move /Y test_fix.md archive\old_docs\ 2>nul
move /Y БЫСТРЫЙ_СТАРТ.txt archive\old_docs\ 2>nul
move /Y ИНСТРУКЦИЯ_ПО_ЗАПУСКУ.txt archive\old_docs\ 2>nul
move /Y ОТВЕТ_НА_ВОПРОС.txt archive\old_docs\ 2>nul
move /Y СРОЧНО_ИСПРАВЛЕНИЯ.txt archive\old_docs\ 2>nul
echo      [OK] Документы перемещены
echo.

echo [5/7] Перемещение старых скриптов...
move /Y kill_and_restart.bat archive\old_scripts\ 2>nul
move /Y restart.ps1 archive\old_scripts\ 2>nul
move /Y restart_bot.bat archive\old_scripts\ 2>nul
move /Y START_BOT.bat archive\old_scripts\ 2>nul
move /Y STOP_BOT.bat archive\old_scripts\ 2>nul
echo      [OK] Скрипты перемещены
echo.

echo [6/7] Удаление старых баз данных и изображений...
del /Q database.sqlite 2>nul
del /Q training_diary.db 2>nul
del /Q test_health_graph.png 2>nul
echo      [OK] Старые БД удалены
echo.

echo [7/7] Очистка кэша Python...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
del /s /q *.pyc >nul 2>&1
echo      [OK] Кэш Python очищен
echo.

echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    ОЧИСТКА ЗАВЕРШЕНА!                        ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo ✅ Проект очищен от временных файлов
echo 📁 Старые файлы перемещены в папку archive/
echo 💾 Освобождено место на диске
echo.
echo Структура проекта теперь чище и понятнее!
echo.
pause
