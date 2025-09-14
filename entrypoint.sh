#!/bin/sh

set -e

echo "Waiting for Postgres..."
while ! pg_isready -h db -p 5432 -U "$POSTGRES_USER"; do
  sleep 1
done

echo "Postgres is ready, running migrations..."

python manage.py migrate

exec gunicorn core.wsgi:application --bind 0.0.0.0:8000



