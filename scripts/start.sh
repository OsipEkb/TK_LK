#!/bin/bash

# Wait for database to be ready
echo "Waiting for database..."
while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
  sleep 0.1
done
echo "Database started"

# Apply database migrations
echo "Applying database migrations"
python manage.py migrate

# Collect static files
echo "Collecting static files"
python manage.py collectstatic --noinput

# Create superuser if not exists
echo "Creating superuser"
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@tehnokom.com', 'admin123')
    print("Superuser created")
else:
    print("Superuser already exists")
EOF

# Start server
echo "Starting server"
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3