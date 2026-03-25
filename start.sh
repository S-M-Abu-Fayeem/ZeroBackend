#!/usr/bin/env sh
set -e

python bootstrap_database.py

if [ -z "${PORT}" ]; then
	echo "ERROR: PORT is not set by the platform."
	exit 1
fi

echo "Starting gunicorn on PORT=${PORT}"
exec gunicorn \
	--bind 0.0.0.0:${PORT} \
	--workers ${GUNICORN_WORKERS:-1} \
	--worker-class gthread \
	--threads ${GUNICORN_THREADS:-8} \
	--timeout ${GUNICORN_TIMEOUT:-120} \
	app:app
