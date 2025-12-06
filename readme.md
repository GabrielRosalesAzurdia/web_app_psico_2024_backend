# Daniel Padnos Wellness Center

## Start Proyect

Run the following commands

> pip install -r requirements.txt
> python manage.py makemigrations
> python manage.py migrate
> python manage.py runserver

it should work !

> python manage.py makemigrations
> python manage.py migrate
> python -m gunicorn web_app_psico_2024_backend.asgi:application -k uvicorn.workers.UvicornWorker
