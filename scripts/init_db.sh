#!/bin/bash

python manage.py makemigrations
python manage.py migrate
python manage.py create_initial_data