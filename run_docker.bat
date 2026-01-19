@echo off
setlocal

REM ====================================
REM Kolos Django Docker Launcher (Windows)
REM ====================================

REM Force correct working directory
cd /d "%~dp0"

echo ====================================
echo Project directory:
echo %cd%
echo ====================================

REM ------------------------------------
REM Check docker
REM ------------------------------------
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Docker not found!
    echo Please install Docker Desktop
    pause
    exit /b
)

REM ------------------------------------
REM Check docker-compose.yml
REM ------------------------------------
if not exist docker-compose.yml (
    echo ERROR: docker-compose.yml not found!
    pause
    exit /b
)

REM ------------------------------------
REM Build containers
REM ------------------------------------
echo Building Docker containers...
docker compose build
if %errorlevel% neq 0 (
    echo ERROR: Docker build failed!
    pause
    exit /b
)

REM ------------------------------------
REM Start containers
REM ------------------------------------
echo Starting Docker containers...
docker compose up -d
if %errorlevel% neq 0 (
    echo ERROR: Docker up failed!
    pause
    exit /b
)

REM ------------------------------------
REM Open browser
REM ------------------------------------
echo Opening browser...
start http://127.0.0.1:8000

echo ====================================
echo Docker Django project is running!
echo ====================================

pause
endlocal
