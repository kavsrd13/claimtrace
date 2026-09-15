#!/bin/bash
# ──────────────────────────────────────────────────────────────────────────────
# azure/startup.sh
# Azure App Service startup script for ClaimTrace (Python 3.11).
#
# Set as the startup command in App Service:
#   bash azure/startup.sh
# ──────────────────────────────────────────────────────────────────────────────

set -e

echo "=== ClaimTrace Azure App Service Startup ==="
echo "Python: $(python --version)"

# Navigate to backend directory
cd /home/site/wwwroot/backend

# Install dependencies if not already installed (App Service SCM deploy installs these)
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv
fi

source .venv/bin/activate

pip install -r requirements.txt --quiet

# Detect port (Azure App Service injects $PORT)
PORT="${PORT:-8000}"

echo "Starting Uvicorn on port $PORT..."
exec uvicorn main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --workers 2 \
    --log-level info \
    --access-log
