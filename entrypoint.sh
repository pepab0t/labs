#!/bin/sh
python manage.py makemigrations main
python manage.py migrate

python manage.py runserver 0.0.0.0:4000
