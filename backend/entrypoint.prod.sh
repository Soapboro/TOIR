#!/bin/bash
set -e

# ── Ждём PostgreSQL ────────────────────────────────────────────────────────────
echo "[entrypoint] Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
until python -c "
import psycopg2, sys
try:
    psycopg2.connect(
        host='${DB_HOST}', port='${DB_PORT}',
        dbname='${DB_NAME}', user='${DB_USER}', password='${DB_PASSWORD}'
    )
except Exception as e:
    sys.exit(1)
" 2>/dev/null; do
    echo "[entrypoint]   PostgreSQL unavailable — retrying in 2s"
    sleep 2
done
echo "[entrypoint] PostgreSQL is ready."

# ── Миграции ──────────────────────────────────────────────────────────────────
echo "[entrypoint] Applying migrations..."
python manage.py migrate --noinput

# ── Статика ───────────────────────────────────────────────────────────────────
echo "[entrypoint] Collecting static files..."
python manage.py collectstatic --noinput --clear

# ── Gunicorn ──────────────────────────────────────────────────────────────────
WORKERS=${GUNICORN_WORKERS:-4}
THREADS=${GUNICORN_THREADS:-2}
TIMEOUT=${GUNICORN_TIMEOUT:-120}

echo "[entrypoint] Starting Gunicorn (workers=${WORKERS}, threads=${THREADS})..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${WORKERS}" \
    --threads "${THREADS}" \
    --worker-class gthread \
    --timeout "${TIMEOUT}" \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    --forwarded-allow-ips '*'
