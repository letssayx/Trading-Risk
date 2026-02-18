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
# Global state for simulation prices to persist across loops
sim_prices: Dict[str, float] = {}

async def simulate_market_data():
    from backend.infrastructure.db import SessionLocal
    from backend.domain.market.models import Bhavcopy

    while True:
        # Get all active symbols from connection manager
        active_symbols = set(manager.active_connections.keys())
        # Always include default majors
        default_symbols = {"NIFTY", "BANKNIFTY"}
        target_symbols = active_symbols.union(default_symbols)

        # Initialize prices for new symbols from DB
        new_symbols = target_symbols - set(sim_prices.keys())
        if new_symbols:
            db = SessionLocal()
            try:
                for sym in new_symbols:
                    # Get last close
                    last_row = db.query(Bhavcopy).filter(Bhavcopy.symbol == sym).order_by(Bhavcopy.trade_date.desc()).first()
                    if last_row:
                        sim_prices[sym] = last_row.close
                    else:
                        # Fallback if not in DB
                        sim_prices[sym] = 1000.0
            finally:
                db.close()

        for symbol in target_symbols:
            if symbol not in sim_prices: continue

            # Random walk (small drift)
            change = (random.random() - 0.5) * (sim_prices[symbol] * 0.001) # 0.1% max move
            sim_prices[symbol] += change

            tick = {
                "symbol": symbol,
                "price": round(sim_prices[symbol], 2),
                "volume": random.randint(100, 5000),
                "oi": random.randint(10000, 50000),
                "timestamp": datetime.now().isoformat()
            }
            await manager.broadcast(tick)

        await asyncio.sleep(1) # 1 second update interval

# We need to start this background task. usually in startup event.
