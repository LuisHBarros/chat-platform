#!/bin/sh
set -e

echo "Running database migrations..."
uv run --frozen --no-dev alembic upgrade head

echo "Starting auth service..."
exec uv run --frozen --no-dev uvicorn app.main:app --host 0.0.0.0 --port 8000
