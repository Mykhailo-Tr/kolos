@echo off
setlocal

REM ====================================
REM Kolos Django Local Launcher
REM ====================================

REM Force correct working directory (directory of this BAT file)
cd /d "%~dp0"

echo ====================================
echo Project directory:
echo %cd%
echo ====================================

REM ------------------------------------
REM Check manage.py
REM ------------------------------------
if not exist manage.py (
    echo ERROR: manage.py not found in this directory!
    echo Please place run_kolos.bat next to manage.py
    pause
    exit /b
)

REM ------------------------------------
REM Check Python
REM ------------------------------------
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b
)

REM ------------------------------------
REM Virtual environment
REM ------------------------------------
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate

REM ------------------------------------
REM Upgrade pip
REM ------------------------------------
echo Upgrading pip...
python -m pip install --upgrade pip

REM ------------------------------------
REM Install dependencies
REM ------------------------------------
if exist requirements.txt (
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    echo WARNING: requirements.txt not found!
)

REM ------------------------------------
REM Django database
REM ------------------------------------
echo Running database migrations...
python manage.py migrate --noinput

REM ------------------------------------
REM Static files
REM ------------------------------------
echo Collecting static files...
python manage.py collectstatic --noinput

REM ------------------------------------
REM Run server
REM ------------------------------------
echo Starting Django development server...
start http://127.0.0.1:8000
python manage.py runserver 127.0.0.1:8000

pause
endlocal
