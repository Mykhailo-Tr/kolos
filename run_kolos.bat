@echo off
setlocal

echo ==============================
echo 🚀 Kolos Project Launcher
echo ==============================

REM --- Перевірка, чи встановлений Docker ---
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Docker не знайдено! Встанови Docker Desktop і повтори запуск.
    pause
    exit /b
)

REM --- Перевірка, чи Docker запущений ---
docker info >nul 2>nul
if %errorlevel% neq 0 (
    echo ⚠️ Docker не запущено. Запусти Docker Desktop і натисни Enter.
    pause
)

REM --- Назва контейнера ---
set CONTAINER=my_django_app
set IMAGE=kolos-web

echo 🔍 Перевірка, чи контейнер вже працює...
docker ps --filter "name=%CONTAINER%" --format "{{.Names}}" | find "%CONTAINER%" >nul
if %errorlevel%==0 (
    echo ✅ Контейнер вже запущений.
) else (
    echo ⚙️ Перевірка, чи образ вже збілджений...
    docker images | find "%IMAGE%" >nul
    if %errorlevel%==0 (
        echo 🧠 Образ знайдено — запускаємо контейнер...
        docker compose up -d
    ) else (
        echo 🛠 Збираємо Docker образ...
        docker compose up --build -d
    )
)

REM --- Очікуємо запуск сервера ---
echo ⏳ Очікуємо запуск Django-сервера...
timeout /t 5 >nul

REM --- Відкриваємо у браузері ---
echo 🌐 Відкриваємо сайт: http://localhost:8000
start http://localhost:8000

echo ✅ Проєкт Kolos запущено!
pause
endlocal
