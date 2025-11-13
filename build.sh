#!/usr/bin/env bash
set -o errexit

echo "=== Starting Django build ==="

# Установка зависимостей
poetry install --no-dev --no-interaction --no-ansi

# Активация виртуального окружения
source $(poetry env info --path)/bin/activate

# Миграции
echo "Applying migrations..."
python manage.py migrate --noinput

# Статические файлы
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "=== Build complete ==="