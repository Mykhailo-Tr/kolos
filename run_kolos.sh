#!/bin/bash

# ====================================
# Kolos Django Local Launcher
# ====================================

set -e

# ------------------------------------
# Force correct working directory
# ------------------------------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "===================================="
echo "Project directory:"
pwd
echo "===================================="

# ------------------------------------
# Check manage.py
# ------------------------------------
if [ ! -f "manage.py" ]; then
    echo "ERROR: manage.py not found in this directory!"
    echo "Please place run_kolos.sh next to manage.py"
    exit 1
fi

# ------------------------------------
# Check Python
# ------------------------------------
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found!"
    echo "Please install Python 3"
    exit 1
fi

# ------------------------------------
# Virtual environment
# ------------------------------------
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# ------------------------------------
# Upgrade pip
# ------------------------------------
echo "Upgrading pip..."
pip install --upgrade pip

# ------------------------------------
# Install dependencies
# ------------------------------------
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
else
    echo "WARNING: requirements.txt not found!"
fi

# ------------------------------------
# Django database
# ------------------------------------
echo "Running database migrations..."
python manage.py migrate --noinput

# ------------------------------------
# Static files
# ------------------------------------
echo "Collecting static files..."
python manage.py collectstatic --noinput

# ------------------------------------
# Run server
# ------------------------------------
echo "Starting Django development server..."
python manage.py runserver 127.0.0.1:8000
