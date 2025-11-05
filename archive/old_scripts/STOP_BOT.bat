@echo off
echo ================================================
echo ОСТАНОВКА БОТА
echo ================================================
echo.

taskkill /F /IM python.exe /T 2>nul
taskkill /F /IM pythonw.exe /T 2>nul

timeout /t 3 >nul

echo.
echo [OK] Все процессы Python остановлены
echo.
echo Теперь запустите: START_BOT.bat
echo.
pause
