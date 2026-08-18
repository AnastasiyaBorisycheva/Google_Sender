#!/bin/sh

# Ждем и накатываем миграции Alembic на PostgreSQL
echo "Применяем миграции Alembic..."
alembic upgrade head

# Запускаем приложение
echo "Запускаем Telegram бота..."
exec "$@"