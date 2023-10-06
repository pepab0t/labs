FROM python:3.10-alpine

WORKDIR /app

RUN apk update 
RUN apk add --virtual build-deps gcc python3-dev musl-dev 
RUN apk add --no-cache mariadb-dev
RUN pip install mysqlclient
RUN apk del build-deps

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

COPY entrypoint.sh .
RUN chmod +x ./entrypoint.sh

EXPOSE 4000
