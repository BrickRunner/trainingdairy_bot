# Очистка проекта от временных файлов
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║            ОЧИСТКА ПРОЕКТА ОТ ВРЕМЕННЫХ ФАЙЛОВ               ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  ВНИМАНИЕ: Будут удалены/перемещены временные файлы!" -ForegroundColor Yellow
Write-Host ""
$confirm = Read-Host "Продолжить? (Y/N)"
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "Операция отменена" -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "[1/7] Создание архивной структуры..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "archive" | Out-Null
New-Item -ItemType Directory -Force -Path "archive\old_tests" | Out-Null
New-Item -ItemType Directory -Force -Path "archive\old_migrations" | Out-Null
New-Item -ItemType Directory -Force -Path "archive\old_docs" | Out-Null
New-Item -ItemType Directory -Force -Path "archive\old_scripts" | Out-Null
Write-Host "      [OK] Архивные папки созданы" -ForegroundColor Green

Write-Host ""
Write-Host "[2/7] Перемещение тестовых файлов..." -ForegroundColor Yellow
Get-ChildItem -File "check_*.py" -ErrorAction SilentlyContinue | Move-Item -Destination "archive\old_tests\" -Force
Get-ChildItem -File "test_*.py" -ErrorAction SilentlyContinue | Move-Item -Destination "archive\old_tests\" -Force
Get-ChildItem -File "debug_*.py" -ErrorAction SilentlyContinue | Move-Item -Destination "archive\old_tests\" -Force
Get-ChildItem -File "diagnose_*.py" -ErrorAction SilentlyContinue | Move-Item -Destination "archive\old_tests\" -Force
Get-ChildItem -File "*_FIX.*" -ErrorAction SilentlyContinue | Move-Item -Destination "archive\old_tests\" -Force
Get-ChildItem -File "SIMULATION_TEST.py" -ErrorAction SilentlyContinue | Move-Item -Destination "archive\old_tests\" -Force
Get-ChildItem -File "EMERGENCY_FIX.py" -ErrorAction SilentlyContinue | Move-Item -Destination "archive\old_tests\" -Force
Get-ChildItem -File "FINAL_CHECK.py" -ErrorAction SilentlyContinue | Move-Item -Destination "archive\old_tests\" -Force
Get-ChildItem -File "force_reload_test.py" -ErrorAction SilentlyContinue | Move-Item -Destination "archive\old_tests\" -Force
Write-Host "      [OK] Тестовые файлы перемещены" -ForegroundColor Green

Write-Host ""
Write-Host "[3/7] Перемещение старых миграций..." -ForegroundColor Yellow
@(
    "add_goal_notification_field.py",
    "add_goal_notifications_field.py",
    "add_test_competitions.py",
    "add_timezone_migration.py",
    "migrate_coach_features.py",
    "migrate_coach_mode.py",
    "migrate_competitions.py",
    "migrate_health_table.py"
) | ForEach-Object {
    if (Test-Path $_) {
        Move-Item $_ "archive\old_migrations\" -Force
    }
}
Write-Host "      [OK] Миграции перемещены" -ForegroundColor Green

Write-Host ""
Write-Host "[4/7] Перемещение старых документов..." -ForegroundColor Yellow
@(
    "DEBUG_INSTRUCTIONS.md",
    "FINAL_FIX.md",
    "test_fix.md",
    "БЫСТРЫЙ_СТАРТ.txt",
    "ИНСТРУКЦИЯ_ПО_ЗАПУСКУ.txt",
    "ОТВЕТ_НА_ВОПРОС.txt",
    "СРОЧНО_ИСПРАВЛЕНИЯ.txt"
) | ForEach-Object {
    if (Test-Path $_) {
        Move-Item $_ "archive\old_docs\" -Force
    }
}
Write-Host "      [OK] Документы перемещены" -ForegroundColor Green

Write-Host ""
Write-Host "[5/7] Перемещение старых скриптов..." -ForegroundColor Yellow
@(
    "kill_and_restart.bat",
    "restart.ps1",
    "restart_bot.bat",
    "START_BOT.bat",
    "STOP_BOT.bat"
) | ForEach-Object {
    if (Test-Path $_) {
        Move-Item $_ "archive\old_scripts\" -Force
    }
}
Write-Host "      [OK] Скрипты перемещены" -ForegroundColor Green

Write-Host ""
Write-Host "[6/7] Удаление старых баз данных и изображений..." -ForegroundColor Yellow
Remove-Item "database.sqlite" -ErrorAction SilentlyContinue -Force
Remove-Item "training_diary.db" -ErrorAction SilentlyContinue -Force
Remove-Item "test_health_graph.png" -ErrorAction SilentlyContinue -Force
Write-Host "      [OK] Старые БД удалены" -ForegroundColor Green

Write-Host ""
Write-Host "[7/7] Очистка кэша Python..." -ForegroundColor Yellow
Get-ChildItem -Path . -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path . -Recurse -File -Filter *.pyc | Remove-Item -Force -ErrorAction SilentlyContinue
Write-Host "      [OK] Кэш Python очищен" -ForegroundColor Green

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                    ОЧИСТКА ЗАВЕРШЕНА!                        ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "✅ Проект очищен от временных файлов" -ForegroundColor Green
Write-Host "📁 Старые файлы перемещены в папку archive/" -ForegroundColor Cyan
Write-Host "💾 Освобождено место на диске" -ForegroundColor Cyan
Write-Host ""
Write-Host "Структура проекта теперь чище и понятнее!" -ForegroundColor Yellow
Write-Host ""
