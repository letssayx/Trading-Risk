from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
from typing import List
import logging

# Set up logger that broadcasts to WebSocket
class WebSocketLogHandler(logging.Handler):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager

    def emit(self, record):
        try:
            msg = self.format(record)
            # Create a fire-and-forget task to broadcast
            asyncio.create_task(self.manager.broadcast(msg))
        except Exception:
            self.handleError(record)

router = APIRouter()

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

# Attach handler to root logger or specific loggers
ws_handler = WebSocketLogHandler(manager)
ws_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
ws_handler.setFormatter(formatter)

# Add to specific loggers we care about
logging.getLogger("backend.ingest").addHandler(ws_handler)
logging.getLogger("backend.strategies").addHandler(ws_handler)
logging.getLogger("sqlalchemy.engine").addHandler(ws_handler) # For DB queries if enabled

@router.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Removed mock log_generator to rely on real logs
