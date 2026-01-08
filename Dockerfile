# ----------------------------
# Dockerfile для Kolos Project
# ----------------------------

# Базовий образ Python
FROM python:3.12-slim

# Встановлюємо SQLite та необхідні утиліти
RUN apt-get update && apt-get install -y \
    build-essential \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# Робоча директорія
WORKDIR /app

# Копіюємо requirements і встановлюємо залежності
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо весь проект у контейнер
COPY . .

# Відкриваємо порт Django
EXPOSE 8000

# Запуск міграцій і старт сервера
CMD python manage.py migrate --noinput && \
    python manage.py collectstatic --noinput && \
    python manage.py runserver 0.0.0.0:8000
