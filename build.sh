#!/usr/bin/env bash
set -o errexit

echo "=== Starting Django build ==="

# Установка зависимостей
poetry install --no-interaction --no-ansi

# Миграции
python manage.py makemigrations --noinput || echo "No new migrations needed"
python manage.py migrate --noinput

# Статические файлы
python manage.py collectstatic --noinput --clear

echo "=== Build complete ==="