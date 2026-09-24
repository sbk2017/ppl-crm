#!/bin/sh
set -e

DATA_DIR=${DATA_DIR:-/app/data}
mkdir -p "$DATA_DIR" "$DATA_DIR/uploads" "$DATA_DIR/exports" "$DATA_DIR/backups"

echo ">> Applying migrations..."
python manage.py migrate --noinput

echo ">> Collecting static files..."
python manage.py collectstatic --noinput

echo ">> Ensuring admin account..."
python manage.py create_admin || true

echo ">> Starting Gunicorn..."
exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -