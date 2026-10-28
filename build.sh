#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input

python manage.py migrate

# Negocio "Demo" con datos inventados. Solo lo crea si no existe.
python manage.py crear_negocio_demo