FROM python:3.11-slim

WORKDIR /app

# Установка Poetry
RUN pip install poetry

# Копируем конфигурацию Poetry
COPY pyproject.toml poetry.lock* ./

# Устанавливаем зависимости
RUN poetry config virtualenvs.create false && poetry install --no-dev

# Копируем проект
COPY . .

# Собираем статику
RUN python manage.py collectstatic --noinput

# Запускаем приложение
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:$PORT"]