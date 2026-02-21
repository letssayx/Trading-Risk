from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
from typing import List

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

@router.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep alive or wait for client messages?
            # Usually logs are push-only.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Mock log producer
async def log_generator():
    """Simulates backend activity logs."""
    import random
    logs = [
        "Computing Z-Score for AAPL...",
        "Market Data Heartbeat: 45ms latency",
        "Risk Engine: VaR 95% = $12,450",
        "Strategy: Turtle Breakout detected on NIFTY",
        "Registry: New tool loaded.",
        "System: Optimal."
    ]
    while True:
        await asyncio.sleep(2)
        msg = random.choice(logs)
        await manager.broadcast(msg)
