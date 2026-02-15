#!/bin/bash

# Turtle Terminal - Dev Launch Script

echo ">>> Launching Turtle Terminal Services..."

# 1. Start Infrastructure (DB/Redis)
echo ">>> Starting Docker Containers..."
if command -v docker-compose &> /dev/null; then
    docker-compose up -d
else
    echo "⚠️ docker-compose not found, skipping container start (assuming local or mock env)"
fi

# 2. Activate Venv (if exists)
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "⚠️ venv directory not found. Assuming global python environment."
fi

# 3. Start Celery Worker (Background)
echo ">>> Starting Celery Worker..."
# Check if celery is installed
if command -v celery &> /dev/null; then
    celery -A backend.celery_worker worker --loglevel=info &
    CELERY_PID=$!
else
    echo "⚠️ Celery not found. Skipping worker."
    CELERY_PID=""
fi

# 4. Start FastAPI Backend
echo ">>> Starting Backend API (Port 8000)..."
if command -v uvicorn &> /dev/null; then
    uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
else
    echo "❌ uvicorn not found. Please install requirements."
    if [ -n "$CELERY_PID" ]; then kill $CELERY_PID; fi
    exit 1
fi

echo ">>> Turtle Terminal is Live at http://localhost:8000"
echo ">>> Press CTRL+C to stop all services."

# Trap cleanup
cleanup() {
    echo ">>> Shutting down..."
    if [ -n "$CELERY_PID" ]; then kill $CELERY_PID; fi
    if [ -n "$BACKEND_PID" ]; then kill $BACKEND_PID; fi
    if command -v docker-compose &> /dev/null; then
        docker-compose down
    fi
    exit
}
trap cleanup SIGINT

wait
