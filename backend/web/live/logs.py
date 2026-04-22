from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
from typing import List, Dict, Any
import logging
from datetime import datetime

# Import the persistence task
# We import inside handler or ensure module loading to avoid circular deps
from backend.ingest.audit_tasks import persist_log_batch

router = APIRouter()

# Buffer for logs to batch-insert
LOG_BUFFER: List[Dict[str, Any]] = []
BUFFER_SIZE = 100
FLUSH_INTERVAL = 5 # seconds

class WebSocketLogHandler(logging.Handler):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager

    def emit(self, record):
        try:
            msg = self.format(record)

            # 1. Broadcast to UI (Only if inside an async loop)
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    loop.create_task(self.manager.broadcast(msg))
            except RuntimeError:
                # No running loop (e.g., synchronous Celery worker)
                pass

            # 2. Queue for DB Persistence
            # Parse simple message or keep raw
            log_entry = {
                "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                "level": record.levelname,
                "source": record.name,
                "event_type": "System_Log",
                "message": record.getMessage(),
                "meta_data": {"filename": record.filename, "line": record.lineno}
            }

            # If running in sync context (no loop), we might need to flush manually or accept that
            # the async log_flusher won't run.
            # Ideally, we should check if we are in the main async app or a worker.
            # For now, we append to buffer. In Celery, this buffer might grow if no one flushes it.
            # A robust solution for Celery would be to push directly to DB or Redis if no loop.
            LOG_BUFFER.append(log_entry)

            # Fallback flush for sync contexts if buffer gets too big
            if len(LOG_BUFFER) >= BUFFER_SIZE:
                try:
                    # Check loop again
                    try:
                        asyncio.get_running_loop()
                    except RuntimeError:
                        # No loop, flush synchronously
                        batch = LOG_BUFFER[:]
                        LOG_BUFFER.clear()
                        persist_log_batch.delay(batch)
                except:
                    pass

        except Exception:
            self.handleError(record)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

# Background Log Flusher
async def log_flusher():
    """Periodically flushes log buffer to DB"""
    while True:
        await asyncio.sleep(FLUSH_INTERVAL)
        if LOG_BUFFER:
            # Create batch copy
            batch = LOG_BUFFER[:]
            LOG_BUFFER.clear()
            # Send to Celery
            try:
                persist_log_batch.delay(batch)
            except Exception as e:
                print(f"Log flush failed: {e}")

# Attach handler
ws_handler = WebSocketLogHandler(manager)
ws_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ws_handler.setFormatter(formatter)

# Attach to loggers
logging.getLogger("backend").addHandler(ws_handler)
# We specifically avoid attaching the websocket handler to sqlalchemy.engine here
# to prevent the UI websocket (and by extension the root uvicorn logger) from puking SQL.
# logging.getLogger("sqlalchemy.engine").addHandler(ws_handler)
logging.getLogger("celery").addHandler(ws_handler)

@router.on_event("startup")
async def start_flusher():
    asyncio.create_task(log_flusher())

@router.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
