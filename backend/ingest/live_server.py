from typing import Dict, Set, List
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
import json
import random
from datetime import datetime

class LiveServer:
    """
    Manages WebSocket connections and broadcasts simulated market data.
    """
    def __init__(self):
        # symbol -> set of websockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.prices: Dict[str, float] = {
            "NIFTY": 22500.0,
            "BANKNIFTY": 48000.0,
            "RELIANCE": 2400.0,
            "HDFCBANK": 1500.0,
            "INFY": 1600.0
        }

    async def connect(self, websocket: WebSocket):
        await websocket.accept()

    def disconnect(self, websocket: WebSocket):
        for symbol in list(self.active_connections.keys()):
            if websocket in self.active_connections[symbol]:
                self.active_connections[symbol].remove(websocket)
                if not self.active_connections[symbol]:
                    del self.active_connections[symbol]

    async def subscribe(self, websocket: WebSocket, symbols: List[str]):
        # Clear previous subs for this socket if strict? No, allow additive.
        for symbol in symbols:
            if symbol not in self.active_connections:
                self.active_connections[symbol] = set()
            self.active_connections[symbol].add(websocket)

            # Send initial snapshot
            await self.send_tick(websocket, symbol, self.prices.get(symbol, 100.0))

    async def send_tick(self, websocket: WebSocket, symbol: str, price: float):
        try:
            message = {
                "type": "tick",
                "symbol": symbol,
                "price": price,
                "volume": random.randint(100, 5000),
                "oi": random.randint(10000, 50000),
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send_text(json.dumps(message))
        except RuntimeError:
            self.disconnect(websocket)

    async def broadcast_loop(self):
        """
        Simulate random walk and broadcast to subscribers.
        """
        while True:
            await asyncio.sleep(1.0) # 1 sec tick

            for symbol, price in self.prices.items():
                # Random walk
                change = price * random.uniform(-0.001, 0.001)
                new_price = round(price + change, 2)
                self.prices[symbol] = new_price

                # Broadcast
                if symbol in self.active_connections:
                    dead_sockets = set()
                    for ws in self.active_connections[symbol]:
                        try:
                            await self.send_tick(ws, symbol, new_price)
                        except Exception:
                            dead_sockets.add(ws)

                    for ws in dead_sockets:
                        self.disconnect(ws)

live_server = LiveServer()
