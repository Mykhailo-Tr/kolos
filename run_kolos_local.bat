@echo off
setlocal

echo ==============================
echo 🚀 Kolos Local Launcher
echo ==============================

REM --- Перевірка наявності Python ---
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Python не знайдено!
    echo Завантаж і встанови Python з https://www.python.org/downloads/
    pause
    exit /b
)

REM --- Створення віртуального середовища, якщо немає ---
if not exist venv (
    echo 🧱 Створюємо віртуальне середовище...
    python -m venv venv
)

REM --- Активуємо середовище ---
call venv\Scripts\activate

REM --- Оновлюємо pip ---
echo 🔄 Оновлюємо pip...
python -m pip install --upgrade pip

REM --- Встановлюємо залежності ---
if exist requirements.txt (
    echo 📦 Встановлюємо залежності з requirements.txt...
    pip install -r requirements.txt
) else (
    echo ⚠️ Не знайдено requirements.txt, пропускаємо встановлення залежностей.
)

REM --- Мігруємо БД ---
echo 🗂 Виконуємо міграції бази даних...
python manage.py migrate

REM --- Перевіряємо статичні файли ---
echo 📁 Збираємо статичні файли...
python manage.py collectstatic --noinput >nul 2>nul

REM --- Запускаємо сервер ---
echo 🚀 Запускаємо Django сервер...
start http://127.0.0.1:8000
python manage.py runserver 127.0.0.1:8000

pause
endlocal
