#!/usr/bin/env sh
set -e

python bootstrap_database.py
echo "Starting gunicorn on PORT=${PORT:-10000}"
exec gunicorn --bind 0.0.0.0:${PORT:-10000} app:app
