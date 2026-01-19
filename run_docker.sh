#!/bin/bash

echo "===================================="
echo "Kolos Django Docker Launcher (Unix)"
echo "===================================="

# Move to script directory
cd "$(dirname "$0")" || exit 1

echo "Project directory:"
pwd
echo "===================================="

# ------------------------------------
# Check docker
# ------------------------------------
if ! command -v docker &> /dev/null
then
    echo "ERROR: Docker not found!"
    exit 1
fi

# ------------------------------------
# Check docker-compose.yml
# ------------------------------------
if [ ! -f docker-compose.yml ]; then
    echo "ERROR: docker-compose.yml not found!"
    exit 1
fi

# ------------------------------------
# Build containers
# ------------------------------------
echo "Building Docker containers..."
docker compose build
if [ $? -ne 0 ]; then
    echo "ERROR: Docker build failed!"
    exit 1
fi

# ------------------------------------
# Start containers
# ------------------------------------
echo "Starting Docker containers..."
docker compose up -d
if [ $? -ne 0 ]; then
    echo "ERROR: Docker up failed!"
    exit 1
fi

# ------------------------------------
# Open browser
# ------------------------------------
echo "Opening browser..."
if command -v xdg-open &> /dev/null; then
    xdg-open http://127.0.0.1:8000
elif command -v open &> /dev/null; then
    open http://127.0.0.1:8000
fi

echo "===================================="
echo "Docker Django project is running!"
echo "===================================="
