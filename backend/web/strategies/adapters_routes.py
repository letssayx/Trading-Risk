from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict
from sqlalchemy.orm import Session
from backend.infrastructure.db import get_db
from backend.domain.market.models import Bhavcopy
from backend.strategies.registry import StrategyRegistry
from backend.strategies.adapters.turtle_adapter import TurtleAdapter
from backend.strategies.adapters.statarb_adapter import StatArbAdapter
# Removed generate_ohlc import

router = APIRouter(prefix="/api/strategies", tags=["Strategy Adapters"])

@router.get("/list")
async def list_strategies():
    """
    Returns available OOTB and User strategies.
    """
    return StrategyRegistry.get_strategies()

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

# --- Helper ---
def fetch_history_from_db(db: Session, symbol: str, limit: int = 100):
    """
    Fetch last N days history for strategy initialization
    """
    results = db.query(Bhavcopy).filter(
        Bhavcopy.symbol == symbol.upper()
    ).order_by(Bhavcopy.trade_date.desc()).limit(limit).all()

    # Reverse to be chronological
    results.reverse()

    data = []
    for row in results:
        # Skip if any price data is missing
        if row.close is None or row.high is None or row.low is None:
            continue

        data.append({
            "time": row.trade_date.strftime("%Y-%m-%d"),
            "open": row.open or row.close, # Fallback open
            "high": row.high,
            "low": row.low,
            "close": row.close,
            "volume": row.total_traded_qty or 0
        })
    return data

# --- Endpoints ---

@router.post("/turtle/start")
async def start_turtle(req: TurtleStartRequest, db: Session = Depends(get_db)):
    adapter = TurtleAdapter(req.symbol, req.risk_per_trade)

    # Fetch real historical data
    history = fetch_history_from_db(db, req.symbol, limit=100)

    if not history:
        # If no data, we can't really start properly, but let's allow it with empty state
        # or raise error? User might be testing with empty DB.
        # Let's initialize empty.
        pass

    adapter.start(history)

    turtle_instances[adapter.id] = adapter
    return {"instanceId": adapter.id, "initialState": adapter.get_state()}

@router.get("/turtle/state/{instance_id}")
async def get_turtle_state(instance_id: str):
    adapter = turtle_instances.get(instance_id)
    if not adapter:
        raise HTTPException(status_code=404, detail="Instance not found")

    # No random updates.
    # The state remains what it was after start() or last real update.
    # In a real system, a background worker would call adapter.update(tick)
    return adapter.get_state()

@router.post("/turtle/stop/{instance_id}")
async def stop_turtle(instance_id: str):
    if instance_id in turtle_instances:
        del turtle_instances[instance_id]
    return {"status": "stopped"}


@router.post("/statarb/start")
async def start_statarb(req: StatArbStartRequest, db: Session = Depends(get_db)):
    adapter = StatArbAdapter(req.symbol1, req.symbol2, req.ratio, req.z_threshold)

    # Fetch historical data for both
    h1 = fetch_history_from_db(db, req.symbol1, limit=100)
    h2 = fetch_history_from_db(db, req.symbol2, limit=100)

    # Align and Calculate Spread (Naive alignment for MVP)
    # We should use pandas merge on time, but assume aligned for now if imported from same source
    # Or strict intersection.
    spread_data = []
    min_len = min(len(h1), len(h2))
    for i in range(min_len):
        # Taking from end (latest)
        d1 = h1[-(min_len-i)]
        d2 = h2[-(min_len-i)]
        if d1['time'] == d2['time']:
            val = d1['close'] - (req.ratio * d2['close'])
            spread_data.append({
                "time": d1['time'],
                "value": val
            })

    adapter.start(spread_data)

    statarb_instances[adapter.id] = adapter
    return {"instanceId": adapter.id, "initialState": adapter.get_state()}

@router.get("/statarb/state/{instance_id}")
async def get_statarb_state(instance_id: str):
    adapter = statarb_instances.get(instance_id)
    if not adapter:
        raise HTTPException(status_code=404, detail="Instance not found")

    # No random updates.
    return adapter.get_state()

@router.post("/statarb/stop/{instance_id}")
async def stop_statarb(instance_id: str):
    if instance_id in statarb_instances:
        del statarb_instances[instance_id]
    return {"status": "stopped"}
