#!/bin/sh
set -e

# Migrations and static files only need to run once per deploy, from one
# place — gated to the web (gunicorn) container so three containers
# starting together (web/worker/beat) don't all race to migrate at once.
if [ "$1" = "gunicorn" ]; then
  echo "Applying database migrations..."
  python manage.py migrate --noinput
  echo "Collecting static files..."
  python manage.py collectstatic --noinput
fi

exec "$@"
