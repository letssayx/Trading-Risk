from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from backend.strategies.adapters import TurtleAdapter, StatArbAdapter
import uuid

router = APIRouter(prefix="/api/strategies", tags=["Strategy Adapters"])

# In-memory store for active adapters (Simulating session state)
# In prod, this would be Redis or persistent actors.
active_turtle_adapters: Dict[str, TurtleAdapter] = {}
active_statarb_adapters: Dict[str, StatArbAdapter] = {}

class TurtleStartRequest(BaseModel):
    symbol: str
    windowSize: int = 20
    riskPerTrade: float = 0.01

class StatArbStartRequest(BaseModel):
    symbol1: str
    symbol2: str
    ratio: float = 1.0
    zThreshold: float = 2.0

class TurtleUpdateRequest(BaseModel):
    symbol: str
    price: float

class StatArbUpdateRequest(BaseModel):
    sym1: str
    sym2: str
    price1: float
    price2: float

# --- Management Endpoints ---

@router.post("/turtle/start")
async def start_turtle(req: TurtleStartRequest):
    instance_id = str(uuid.uuid4())
    # For MVP, we key by symbol to keep it simple for the tab to find
    # In full version, key by instance_id to allow multiple strats on same symbol
    active_turtle_adapters[req.symbol] = TurtleAdapter(req.symbol, lookback=req.windowSize)
    return {"instanceId": instance_id, "status": "started", "symbol": req.symbol}

@router.post("/statarb/start")
async def start_statarb(req: StatArbStartRequest):
    instance_id = str(uuid.uuid4())
    key = f"{req.symbol1}-{req.symbol2}"
    active_statarb_adapters[key] = StatArbAdapter(req.symbol1, req.symbol2) # Add params to adapter later
    return {"instanceId": instance_id, "status": "started", "pair": key}

# --- State/Update Endpoints ---

@router.post("/turtle/update")
async def update_turtle(req: TurtleUpdateRequest):
    symbol = req.symbol
    if symbol not in active_turtle_adapters:
        # Auto-start if not exists (Lazy init for MVP)
        active_turtle_adapters[symbol] = TurtleAdapter(symbol)

    adapter = active_turtle_adapters[symbol]
    result = adapter.update(req.price)
    return result

@router.post("/statarb/update")
async def update_statarb(req: StatArbUpdateRequest):
    key = f"{req.sym1}-{req.sym2}"
    if key not in active_statarb_adapters:
        active_statarb_adapters[key] = StatArbAdapter(req.sym1, req.sym2)

    adapter = active_statarb_adapters[key]
    result = adapter.update(req.price1, req.price2)
    return result

@router.get("/turtle/state/{symbol}")
async def get_turtle_state(symbol: str):
    if symbol not in active_turtle_adapters:
        raise HTTPException(status_code=404, detail="Strategy not active")
    # Return last known state or adapter internal state
    # Adapter currently returns state on update. We might need a getter.
    # For MVP, update is the primary way to interact.
    return {"status": "active"}
