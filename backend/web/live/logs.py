from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json
from datetime import datetime

router = APIRouter()
clients = []

@router.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients.remove(websocket)

async def log_generator():
    """
    Deprecated: Random log generator.
    Now passive.
    """
    pass

async def broadcast_log(msg: str, level: str = "INFO"):
    """
    Helper to broadcast real system logs to frontend.
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    payload = json.dumps({"time": timestamp, "level": level, "message": msg})
    for client in clients:
        try:
            await client.send_text(payload)
        except:
            pass
