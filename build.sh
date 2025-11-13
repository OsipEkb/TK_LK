#!/usr/bin/env bash
# build.sh

set -o errexit

echo "=== Starting build process ==="

# Установка Poetry если не установлен
if ! command -v poetry &> /dev/null; then
    echo "Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="/opt/render/.local/bin:$PATH"
fi

echo "Poetry version:"
poetry --version

echo "Installing dependencies..."
poetry install --no-dev --no-interaction --no-ansi

echo "Activating virtual environment..."
source $(poetry env info --path)/bin/activate

echo "Making migrations..."
python manage.py makemigrations --noinput

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "=== Build completed successfully ==="