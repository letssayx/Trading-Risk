from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json
import random

router = APIRouter(tags=["Live Updates"])

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
            await connection.send_text(message)

manager = ConnectionManager()

@router.websocket("/ws/live-updates")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Simulate Real-Time Push (PnL, Greeks)
            # In prod, this would subscribe to a Redis channel or internal event bus
            data = {
                "type": "pnl_update",
                "payload": {
                    "total_pnl": round(random.uniform(-5000, 5000), 2),
                    "delta": round(random.uniform(-50, 50), 2),
                    "timestamp": "now"
                }
            }
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(2) # 2s interval
    except WebSocketDisconnect:
        manager.disconnect(websocket)
