from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.ingest.live_server import live_server
import asyncio
import json

router = APIRouter(prefix="/ws", tags=["Live Data"])

@router.websocket("/live")
async def websocket_endpoint(websocket: WebSocket):
    await live_server.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if "subscribe" in message:
                symbols = message["subscribe"]
                await live_server.subscribe(websocket, symbols)

    except WebSocketDisconnect:
        live_server.disconnect(websocket)
    except Exception as e:
        print(f"WS Error: {e}")
        live_server.disconnect(websocket)

# Background task starter
async def start_broadcast():
    await live_server.broadcast_loop()
