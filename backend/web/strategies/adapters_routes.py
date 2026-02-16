from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from backend.strategies.adapters import TurtleAdapter, StatArbAdapter

router = APIRouter(prefix="/api/strategies", tags=["Strategy Adapters"])

# In-memory store for active adapters (Simulating session state)
# In prod, this would be Redis or persistent actors.
active_turtle_adapters: Dict[str, TurtleAdapter] = {}
active_statarb_adapters: Dict[str, StatArbAdapter] = {}

class TurtleUpdateRequest(BaseModel):
    symbol: str
    price: float

class StatArbUpdateRequest(BaseModel):
    sym1: str
    sym2: str
    price1: float
    price2: float

@router.post("/turtle/update")
async def update_turtle(req: TurtleUpdateRequest):
    symbol = req.symbol
    if symbol not in active_turtle_adapters:
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
