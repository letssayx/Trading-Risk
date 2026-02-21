from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Set
import asyncio
import json
from datetime import datetime

# Import TickVault to read real ticks if available
from backend.ingest.tick_vault import TickVault

router = APIRouter()

# Simple in-memory manager for active connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {} # symbol -> list of websockets

    async def connect(self, websocket: WebSocket):
        await websocket.accept()

    def disconnect(self, websocket: WebSocket, symbol: str):
        if symbol in self.active_connections:
            self.active_connections[symbol].discard(websocket)
            if not self.active_connections[symbol]:
                del self.active_connections[symbol]

    async def subscribe(self, websocket: WebSocket, symbols: List[str]):
        for symbol in symbols:
            if symbol not in self.active_connections:
                self.active_connections[symbol] = set()
            self.active_connections[symbol].add(websocket)

    async def broadcast(self, message: dict):
        symbol = message.get("symbol")
        if symbol and symbol in self.active_connections:
            for connection in list(self.active_connections[symbol]):
                try:
                    await connection.send_json(message)
                except:
                    self.disconnect(connection, symbol)

manager = ConnectionManager()

@router.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            if "subscribe" in message:
                await manager.subscribe(websocket, message["subscribe"])
    except WebSocketDisconnect:
        pass

# No random walk simulation.
# In a real environment, this function would poll Redis or receive ZMQ messages
# from the feed handler and broadcast them.
async def simulate_market_data():
    # Placeholder: If we had a real feed, we would loop here.
    # For now, stay silent rather than emitting fake random numbers.
    while True:
        await asyncio.sleep(60)
