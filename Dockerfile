# Dockerfile
FROM python:3.13-slim

WORKDIR /app

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Делаем скрипт запуска исполняемым
RUN chmod +x /app/entrypoint.sh 2>/dev/null || true

# Запуск
CMD ["python", "-m", "src.main"]