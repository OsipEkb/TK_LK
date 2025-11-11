FROM python:3.11-slim

WORKDIR /app

# Копируем requirements.txt первым для кэширования
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Собираем статику
RUN python manage.py collectstatic --noinput

# Запускаем приложение
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:$PORT"]