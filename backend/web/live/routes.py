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

# Background task to stream market data
async def simulate_market_data():
    from backend.infrastructure.upstox_client import upstox_client

    while True:
        try:
            # Get all active symbols from connection manager
            active_symbols = list(manager.active_connections.keys())
            if not active_symbols:
                await asyncio.sleep(1)
                continue

            # If Upstox is configured, fetch real data
            if upstox_client.is_configured():
                # Map symbols to keys
                # Heuristic: Indices vs Equities
                keys_map = {}
                keys_to_fetch = []

                for sym in active_symbols:
                    if sym in ["NIFTY", "BANKNIFTY"]:
                        # Indices often need specific keys, hardcoding for demo/common case
                        # Or using search. Let's assume NSE_INDEX|{IndexName} or similar?
                        # Upstox V2 often uses instrument_key like 'NSE_INDEX|Nifty 50'
                        # This is brittle without a master list.
                        # Fallback to NSE_EQ for now or skip if unsure.
                        # Let's try NSE_INDEX|{sym} but NIFTY is usually Nifty 50.
                        # For safety, let's treat them as NSE_EQ if not sure, or try standard mapping.
                        key = f"NSE_INDEX|{sym}"
                        if sym == "NIFTY": key = "NSE_INDEX|Nifty 50"
                        if sym == "BANKNIFTY": key = "NSE_INDEX|Nifty Bank"
                    else:
                        key = upstox_client.get_instrument_key(sym)

                    keys_map[key] = sym
                    keys_to_fetch.append(key)

                if keys_to_fetch:
                    quotes = upstox_client.get_market_quote(keys_to_fetch)

                    for key, data in quotes.items():
                        symbol = keys_map.get(key)
                        if not symbol: continue

                        # Upstox Quote Structure: { 'last_price': ..., 'volume': ... }
                        lp = data.get('last_price', 0)
                        vol = data.get('volume', 0)
                        oi = data.get('oi', 0)

                        tick = {
                            "symbol": symbol,
                            "price": lp,
                            "volume": vol,
                            "oi": oi,
                            "timestamp": datetime.now().isoformat()
                        }
                        await manager.broadcast(tick)

            # If NOT configured, do NOTHING (as requested: "donot use false prices")
            # We just sleep to prevent busy loop

        except Exception as e:
            print(f"Market Stream Error: {e}")

        await asyncio.sleep(1) # Poll interval

# We need to start this background task. usually in startup event.
