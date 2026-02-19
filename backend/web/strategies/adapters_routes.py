from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Optional
from backend.strategies.adapters.turtle_adapter import TurtleAdapter
from backend.strategies.adapters.statarb_adapter import StatArbAdapter
from backend.web.data.routes import generate_ohlc, fetch_historical_data, get_spread_historical
from backend.infrastructure.db import get_db

router = APIRouter(prefix="/api/strategies", tags=["Strategy Adapters"])

# In-memory storage for active strategy instances
turtle_instances: Dict[str, TurtleAdapter] = {}
statarb_instances: Dict[str, StatArbAdapter] = {}

# --- Schemas ---
class TurtleStartRequest(BaseModel):
    symbol: str
    segment: str = "CM" # "CM" or "FO"
    expiry_pos: int = 1 # 1=Near, 2=Next, 3=Far
    risk_per_trade: float = 0.01

class StatArbStartRequest(BaseModel):
    symbol1: str
    symbol2: str
    ratio: float = 1.0
    z_threshold: float = 2.0

# --- Endpoints ---

@router.post("/turtle/start")
async def start_turtle(req: TurtleStartRequest, db: Session = Depends(get_db)):
    adapter = TurtleAdapter(req.symbol, req.risk_per_trade)
    adapter.set_config(req.segment, req.expiry_pos)

    # Fetch historical data to initialize
    history = fetch_historical_data(req.symbol, req.segment, 100, db, expiry_pos=req.expiry_pos)
    if not history:
        history = []

    adapter.start(history)

    turtle_instances[adapter.id] = adapter
    return {"instanceId": adapter.id, "initialState": adapter.get_state()}

@router.get("/turtle/state/{instance_id}")
async def get_turtle_state(instance_id: str):
    adapter = turtle_instances.get(instance_id)
    if not adapter:
        raise HTTPException(status_code=404, detail="Instance not found")

    # Only return state. Updates happen via WebSocket or external Tick events.
    return adapter.get_state()

@router.post("/turtle/pause/{instance_id}")
async def pause_turtle(instance_id: str):
    adapter = turtle_instances.get(instance_id)
    if adapter:
        adapter.is_active = False
        return {"status": "paused"}
    raise HTTPException(status_code=404, detail="Instance not found")

@router.post("/turtle/resume/{instance_id}")
async def resume_turtle(instance_id: str):
    adapter = turtle_instances.get(instance_id)
    if adapter:
        adapter.is_active = True
        return {"status": "resumed"}
    raise HTTPException(status_code=404, detail="Instance not found")

@router.post("/turtle/remove/{instance_id}")
async def remove_turtle(instance_id: str):
    if instance_id in turtle_instances:
        del turtle_instances[instance_id]
        return {"status": "removed"}
    raise HTTPException(status_code=404, detail="Instance not found")


@router.post("/statarb/start")
async def start_statarb(req: StatArbStartRequest, db: Session = Depends(get_db)):
    adapter = StatArbAdapter(req.symbol1, req.symbol2, req.ratio, req.z_threshold)

    # Fetch historical spread
    spread_data = await get_spread_historical(req.symbol1, req.symbol2, req.ratio, days=100, db=db)
    adapter.start(spread_data)

    statarb_instances[adapter.id] = adapter
    return {"instanceId": adapter.id, "initialState": adapter.get_state()}

@router.get("/statarb/state/{instance_id}")
async def get_statarb_state(instance_id: str):
    adapter = statarb_instances.get(instance_id)
    if not adapter:
        raise HTTPException(status_code=404, detail="Instance not found")

    return adapter.get_state()

@router.post("/statarb/stop/{instance_id}")
async def stop_statarb(instance_id: str):
    if instance_id in statarb_instances:
        del statarb_instances[instance_id]
    return {"status": "stopped"}
