#!/usr/bin/env bash
set -euo pipefail

# Migrations and static files only need to run once per deploy, from one
# place — gated to the web (gunicorn) container so three containers
# starting together (web/worker/beat) don't all race to migrate at once.
# Print some diagnostics to help debug failures in CI/Render logs.
if [ "${1:-}" = "gunicorn" ]; then
  echo "PATH=$PATH"
  echo "which python: $(command -v python || true)"
  echo "which gunicorn: $(command -v gunicorn || true)"

  echo "Applying database migrations..."
  python manage.py migrate --noinput || { echo "migrate failed"; exit 1; }

  echo "Collecting static files..."
  python manage.py collectstatic --noinput || { echo "collectstatic failed"; exit 1; }
fi

exec "$@"
