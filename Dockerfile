# Використовуємо офіційний Python образ
FROM python:3.11-slim

# Встановлюємо залежності
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо весь проєкт
COPY . .

# Відкриваємо порт Django
EXPOSE 8000

# Команда запуску
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
