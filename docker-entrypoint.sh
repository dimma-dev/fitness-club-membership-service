#!/bin/sh
# Wait for Postgres to become available, then exec passed command
# This script uses python+psycopg2 (installed in the container) to test DB connection.
set -e

host=${POSTGRES_HOST:-postgres}
port=${POSTGRES_PORT:-5432}
user=${POSTGRES_USER:-}
password=${POSTGRES_PASSWORD:-}
dbname=${POSTGRES_DB:-}

echo "Waiting for postgres at $host:$port..."
python - <<PY
import os, time
import psycopg2
from psycopg2 import OperationalError

host = os.environ.get('POSTGRES_HOST', 'postgres')
port = int(os.environ.get('POSTGRES_PORT', '5432'))
user = os.environ.get('POSTGRES_USER', '')
password = os.environ.get('POSTGRES_PASSWORD', '')
dbname = os.environ.get('POSTGRES_DB', '')

while True:
    try:
        conn = psycopg2.connect(host=host, port=port, user=user, password=password, dbname=dbname)
        conn.close()
        print('Postgres is available')
        break
    except OperationalError as e:
        print('Postgres is unavailable, sleeping 1s...')
        time.sleep(1)
PY

exec "$@"
