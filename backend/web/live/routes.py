from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Set
import asyncio
import json
import random
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
        # Handle disconnect properly - tricky without tracking which symbols this socket subscribed to
        # For this simple demo, we let the broadcast loop handle stale connections
        pass

# Background task to simulate market data
async def simulate_market_data():
    symbols = ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "INFY", "HDFC", "SBIN"]
    prices = {s: 1000.0 + random.random() * 1000 for s in symbols}

    while True:
        for symbol in symbols:
            # Stop Random walk for now - keep price stable or gentle noise
            # change = (random.random() - 0.5) * 0.1
            # prices[symbol] += change

            # Just emit the current price (maybe slight jitter to show it's alive)
            prices[symbol] += (random.random() - 0.5) * 0.05

            tick = {
                "symbol": symbol,
                "price": round(prices[symbol], 2),
                "volume": random.randint(100, 5000),
                "oi": random.randint(10000, 50000),
                "timestamp": datetime.now().isoformat()
            }
            # We need to broadcast this.
            # Since manager.broadcast is async, we can await it.
            await manager.broadcast(tick)

        await asyncio.sleep(1) # 1 second update interval

# We need to start this background task. usually in startup event.
