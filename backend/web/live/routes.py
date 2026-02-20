from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Set
import asyncio
import json
from datetime import datetime

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
        # In a real app, we'd broadcast to specific symbol subscribers.
        # Here, for simplicity, we iterate over symbols in the message if present, or all.
        symbol = message.get("symbol")
        if symbol and symbol in self.active_connections:
            # Create a copy of the set for safe iteration
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

# Simulation removed.
# This module now only serves as a passive WebSocket relay if needed.
