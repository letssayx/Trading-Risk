#!/bin/bash

# Turtle Terminal - Dev Launch Script

echo ">>> Launching Turtle Terminal Services..."

# 1. Start Infrastructure (DB/Redis)
echo ">>> Starting Docker Containers..."
docker-compose up -d

# 2. Activate Venv
source venv/bin/activate

# 3. Start Celery Worker (Background)
# Creating a dummy worker entry point if needed, or pointing to backend/main
echo ">>> Starting Celery Worker..."
celery -A backend.celery_worker worker --loglevel=info &
CELERY_PID=$!

# 4. Start FastAPI Backend
echo ">>> Starting Backend API (Port 8000)..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir backend \
    --reload-exclude "venv-wsl" \
    --reload-exclude "venv" \
    --reload-exclude ".git" \
    --reload-exclude "timescale" \
    --reload-exclude "node_modules" \
    --reload-exclude "pgdata" \
    --reload-exclude "pgadmin" \
    --reload-exclude "__pycache__" \
    --reload-exclude "*.pyc" &
BACKEND_PID=$!

echo ">>> Turtle Terminal is Live at http://localhost:8000"
echo ">>> Press CTRL+C to stop all services."

# Trap cleanup
cleanup() {
    echo ">>> Shutting down..."
    kill $CELERY_PID
    kill $BACKEND_PID
    docker-compose down
    exit
}
trap cleanup SIGINT

wait
