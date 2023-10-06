FROM python:3.10-alpine

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt
COPY . .
RUN python3 manage.py makemigrations main
RUN python3 manage.py migrate

EXPOSE 4000

CMD ["python3", "manage.py", "runserver", "0.0.0.0:4000"]