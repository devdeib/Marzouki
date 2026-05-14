#!/usr/bin/env bash
# Build / release script for the Marzouki Django app.
#
# Run from the project root (the directory that contains `manage.py`):
#   ./TheProject/build.sh
#
# Or from anywhere; the script self-locates the project root.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "[build] Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "[build] Collecting static files..."
python manage.py collectstatic --no-input

echo "[build] Applying database migrations..."
python manage.py migrate --no-input

echo "[build] Done."
