# Принудительный перезапуск бота с очисткой кэша
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ПРИНУДИТЕЛЬНЫЙ ПЕРЕЗАПУСК БОТА" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Остановка процессов
Write-Host "[1/5] Остановка Python процессов..." -ForegroundColor Yellow
Get-Process python* -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
Write-Host "      [OK] Процессы остановлены" -ForegroundColor Green

# Очистка кэша __pycache__
Write-Host ""
Write-Host "[2/5] Удаление __pycache__..." -ForegroundColor Yellow
Get-ChildItem -Path . -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "      [OK] Кэш __pycache__ удалён" -ForegroundColor Green

# Очистка .pyc файлов
Write-Host ""
Write-Host "[3/5] Удаление .pyc файлов..." -ForegroundColor Yellow
Get-ChildItem -Path . -Recurse -File -Filter *.pyc | Remove-Item -Force -ErrorAction SilentlyContinue
Write-Host "      [OK] Файлы .pyc удалены" -ForegroundColor Green

# Проверка
Write-Host ""
Write-Host "[4/5] Проверка критических файлов..." -ForegroundColor Yellow
if (-not (Test-Path "venv\Scripts\python.exe")) {
    Write-Host "      [ОШИБКА] venv не найден!" -ForegroundColor Red
    pause
    exit 1
}
if (-not (Test-Path "main.py")) {
    Write-Host "      [ОШИБКА] main.py не найден!" -ForegroundColor Red
    pause
    exit 1
}
Write-Host "      [OK] Все файлы на месте" -ForegroundColor Green

# Запуск
Write-Host ""
Write-Host "[5/5] Запуск бота..." -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  БОТ ЗАПУСКАЕТСЯ!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "ИСПРАВЛЕНО:" -ForegroundColor Yellow
Write-Host "  ✓ Ввод пульса при добавлении результата"
Write-Host "  ✓ Ввод места в общем зачёте"
Write-Host "  ✓ Ввод места в возрастной категории"
Write-Host "  ✓ Календарь для прошедших соревнований"
Write-Host ""
Write-Host "КАК ПРОВЕРИТЬ:" -ForegroundColor Yellow
Write-Host "  1. Соревнования → Мои соревнования"
Write-Host "  2. Выберите ПРОШЕДШЕЕ соревнование"
Write-Host "  3. Нажмите 'Добавить результат'"
Write-Host "  4. Пройдите 4 шага:"
Write-Host "     - Введите время (например: 42:30.50)"
Write-Host "     - Введите место в общем зачёте (или пропустите)"
Write-Host "     - Введите место в категории (или пропустите)"
Write-Host "     - Введите пульс в уд/мин (или пропустите)"
Write-Host ""
Write-Host "Для остановки нажмите Ctrl+C" -ForegroundColor Red
Write-Host ""

& venv\Scripts\python.exe main.py
