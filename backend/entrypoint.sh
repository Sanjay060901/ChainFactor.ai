#!/bin/sh
set -e

echo "Running database migrations..."
python -m alembic upgrade head || echo "WARN: Migrations failed (non-fatal, continuing...)"

echo "Running seed data..."
python -m app.seed || echo "Seed skipped (already seeded or error)"

echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
