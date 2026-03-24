#!/usr/bin/env sh
set -e

python bootstrap_database.py
exec gunicorn --bind 0.0.0.0:${PORT:-10000} app:app
