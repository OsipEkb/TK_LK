

set -o errexit

# Install dependencies using Poetry
poetry install --no-dev --no-interaction --no-ansi

# Collect static files
poetry run python manage.py collectstatic --noinput

# Run migrations
poetry run python manage.py migrate