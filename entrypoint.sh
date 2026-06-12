#!/bin/sh
set -eu

alembic upgrade heads
exec uvicorn app.main:app --app-dir src --host 0.0.0.0 --port 8000
