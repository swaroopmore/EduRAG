#!/bin/sh
# Container entrypoint: apply DB migrations, then start the API.
# Railway injects $PORT; locally it defaults to 8000.
set -e

if [ "${RUN_MIGRATIONS_ON_START:-true}" = "true" ]; then
  echo "Running database migrations..."
  alembic upgrade head
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers --forwarded-allow-ips="*"
