#!/bin/sh
python manage.py migrate --no-input
python manage.py collectstatic --no-input

gunicorn labs.wsgi:application -w 5 --bind 0.0.0.0:8000
