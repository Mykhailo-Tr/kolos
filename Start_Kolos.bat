@echo off
setlocal
title Kolos System Loader

:: 1. Переходимо в директорію, де лежить цей bat-файл
cd /d "%~dp0"

:: 2. Перевіряємо, чи існує файл лаунчера
if not exist "launcher.py" (
    echo [ERROR] Файл launcher.py не знайдено у цій папці!
    echo Будь ласка, переконайтеся, що bat-файл лежить поруч із кодом.
    pause
    exit /b
)

:: 3. Шукаємо Python (спочатку pythonw для прихованої консолі, потім звичайний python)
where pythonw >nul 2>nul
if %errorlevel% equ 0 (
    start "" pythonw launcher.py
    exit
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    start "" python launcher.py
    exit
)

:: 4. Якщо Python не знайдено зовсім
cls
echo ======================================================
echo [ПОМИЛКА] Python не встановлено на цьому комп'ютері!
echo ======================================================
echo.
echo Для роботи програми потрібно встановити Python з офіційного сайту:
echo https://www.python.org/downloads/
echo.
echo Під час встановлення ОБОВ'ЯЗКОВО поставте галочку 
echo "Add Python to PATH".
echo.
pause
exit