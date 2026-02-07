#!/bin/bash

# Load Environment
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
fi

echo "🚀 Starting Turtle Terminal Dev Environment..."

# 1. Start Infrastructure (Docker)
echo "   [1/3] Starting Database & Cache..."
docker-compose up -d
if [ $? -ne 0 ]; then
    echo "⚠️ Docker Compose failed. Ensure Docker is running."
fi

# 2. Start Celery Worker
echo "   [2/3] Starting Simulation Worker..."
# Running in background
celery -A backend.celery_worker.celery_app worker --loglevel=info > celery.log 2>&1 &
CELERY_PID=$!
echo "         Worker PID: $CELERY_PID"

# Mock Initial Ingestion Trigger (Optional)
# echo "   [Info] Run 'python backend/data/nse_ingestion.py' to seed institutional data if needed."

# 3. Start Backend (with Hot Reload)
echo "   [3/3] Starting Backend API (Live Sync Active)..."
echo "         Open http://localhost:8000/dashboard"

# Reload includes backend/plugins to detect new strategy files
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir backend

# Cleanup on exit
kill $CELERY_PID
echo "🛑 Shutting down..."
