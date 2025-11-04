# Скрипт перезапуска бота
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ПЕРЕЗАПУСК БОТА" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Остановка процессов
Write-Host "[1/4] Остановка Python процессов..." -ForegroundColor Yellow
Get-Process python* -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
Write-Host "      [OK] Процессы остановлены" -ForegroundColor Green

# Очистка кэша
Write-Host ""
Write-Host "[2/4] Очистка кэша..." -ForegroundColor Yellow
Get-ChildItem -Path . -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path . -Recurse -File -Filter *.pyc | Remove-Item -Force -ErrorAction SilentlyContinue
Write-Host "      [OK] Кэш очищен" -ForegroundColor Green

# Проверка БД
Write-Host ""
Write-Host "[3/4] Проверка БД..." -ForegroundColor Yellow
& venv\Scripts\python.exe check_competition_db.py 2>$null | Select-String -Pattern "\[OK\]|\[MISSING\]" | Write-Host
Write-Host "      [OK] БД проверена" -ForegroundColor Green

# Запуск
Write-Host ""
Write-Host "[4/4] Запуск бота..." -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  БОТ ЗАПУСКАЕТСЯ!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Как проверить:" -ForegroundColor Yellow
Write-Host "1. Соревнования → Мои соревнования"
Write-Host "2. Выберите ПРОШЕДШЕЕ соревнование"
Write-Host "3. Нажмите 'Добавить результат'"
Write-Host "4. Должны появиться запросы: ВРЕМЯ → МЕСТО → КАТЕГОРИЯ → ПУЛЬС"
Write-Host ""
Write-Host "Для остановки нажмите Ctrl+C" -ForegroundColor Red
Write-Host ""

& venv\Scripts\python.exe main.py
