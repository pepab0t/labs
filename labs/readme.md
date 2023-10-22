# Labs

Reservation system for lab exercises.

## First steps
### Install dependencies
>__Note:__ This guide is for Mac/Linux, if you are using Windows, find the equivalent command. 

Create virtual enviroment:

```bash
python3 -m venv venv
```
Activate enviroment: 
```bash
source ./venv/bin/activate
```
Install requirements:
```bash
pip install -r requirements.txt
```

### Make migrations
Make migrations using Django framework:
```bash
python3 manage.py makemigrations main
python3 manage.py migrate
```
These steps will create database.

### Create super user
Now let's create __super user__.\
Several functionality of the app is for staff only. We will use superuser account for them.

> __WARNING__: all email addresses used in this application must have domain `@fs.cvut.cz`

To create superuser account execute:
```bash
python3 manage.py createsuperuser
```

> Example of creadentials:
> - Email: admin@fs.cvut.cz
> - Password: admin

### Run server
In this state, we can run application with 
```bash
python3 manage.py runserver
```

> __Note:__ If you want to change some settings, such as `SECRET_KEY`, modify the file `labs/settings.py`.