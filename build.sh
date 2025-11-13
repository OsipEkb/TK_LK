#!/usr/bin/env bash
set -o errexit

echo "=== Starting build ==="

# Установка зависимостей
poetry install --no-interaction --no-ansi

# Миграции (если есть база данных)
python manage.py migrate --noinput || echo "Migrations skipped"

# Статические файлы
python manage.py collectstatic --noinput --clear

echo "=== Build complete ==="