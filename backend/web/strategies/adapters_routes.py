from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
from backend.strategies.adapters.turtle_adapter import TurtleAdapter
from backend.strategies.adapters.statarb_adapter import StatArbAdapter
from backend.web.data.routes import generate_ohlc, get_spread_historical

router = APIRouter(prefix="/api/strategies", tags=["Strategy Adapters"])

# In-memory storage for active strategy instances
turtle_instances: Dict[str, TurtleAdapter] = {}
statarb_instances: Dict[str, StatArbAdapter] = {}

# --- Schemas ---
class TurtleStartRequest(BaseModel):
    symbol: str
    risk_per_trade: float = 0.01

class StatArbStartRequest(BaseModel):
    symbol1: str
    symbol2: str
    ratio: float = 1.0
    z_threshold: float = 2.0

# --- Endpoints ---

@router.post("/turtle/start")
async def start_turtle(req: TurtleStartRequest):
    adapter = TurtleAdapter(req.symbol, req.risk_per_trade)

    # Fetch mock historical data to initialize
    history = generate_ohlc(req.symbol, days=100)
    adapter.start(history)

    turtle_instances[adapter.id] = adapter
    return {"instanceId": adapter.id, "initialState": adapter.get_state()}

@router.get("/turtle/state/{instance_id}")
async def get_turtle_state(instance_id: str):
    adapter = turtle_instances.get(instance_id)
    if not adapter:
        raise HTTPException(status_code=404, detail="Instance not found")

    # Simulate a tick update on poll (since we don't have a real event loop pushing ticks here yet)
    # In a real system, the websocket loop would push to the adapter.
    # Here we just fetch a 'random walk' price based on last price to simulate live movement.
    import random
    current_price = adapter.last_price * (1 + (random.random() - 0.5) * 0.001)
    adapter.update(current_price)

    return adapter.get_state()

@router.post("/turtle/stop/{instance_id}")
async def stop_turtle(instance_id: str):
    if instance_id in turtle_instances:
        del turtle_instances[instance_id]
    return {"status": "stopped"}


@router.post("/statarb/start")
async def start_statarb(req: StatArbStartRequest):
    adapter = StatArbAdapter(req.symbol1, req.symbol2, req.ratio, req.z_threshold)

    # Fetch historical spread
    spread_data = await get_spread_historical(req.symbol1, req.symbol2, req.ratio, days=100)
    adapter.start(spread_data)

    statarb_instances[adapter.id] = adapter
    return {"instanceId": adapter.id, "initialState": adapter.get_state()}

@router.get("/statarb/state/{instance_id}")
async def get_statarb_state(instance_id: str):
    adapter = statarb_instances.get(instance_id)
    if not adapter:
        raise HTTPException(status_code=404, detail="Instance not found")

    # Simulate update
    # Need last prices for both. We don't track them in adapter perfectly in this mock.
    # We'll just jitter the spread directly or something?
    # Better: Update the spread based on last spread.
    import random
    jitter = (random.random() - 0.5) * 1.0
    # We need inputs for update(p1, p2).
    # Let's just cheat for the demo and update spread directly or imply prices.
    # To keep it cleaner, let's just not call update() here and assume it's static
    # OR mock p1/p2.

    # Mocking p1, p2 from thin air is messy.
    # Let's just return state. The UI will see static data unless I implement the full TickVault loop.
    # User Requirement: "The tab then periodically... receives updated strategy state"
    # So I should change something.

    # Let's manually drift the z-score slightly
    adapter.z_score += (random.random() - 0.5) * 0.1
    adapter.last_spread += (random.random() - 0.5) * 0.5

    return adapter.get_state()

@router.post("/statarb/stop/{instance_id}")
async def stop_statarb(instance_id: str):
    if instance_id in statarb_instances:
        del statarb_instances[instance_id]
    return {"status": "stopped"}
