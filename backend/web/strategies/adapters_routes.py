from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from backend.infrastructure.db import get_db
from backend.domain.market.service import MarketDataService
from backend.strategies.adapters.turtle_adapter import TurtleAdapter
from backend.strategies.adapters.statarb_adapter import StatArbAdapter

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
async def start_turtle(
    req: TurtleStartRequest,
    db: Session = Depends(get_db)
):
    adapter = TurtleAdapter(req.symbol, req.risk_per_trade)

    # Fetch real historical data from DB
    # Note: For Turtle, we might need more history for ATR calculation, but 100 is okay for start
    # Try fetching as EQ first, then FO if implicit
    history = MarketDataService.get_daily_ohlc(db, req.symbol, days=100)

    if not history:
        # Fallback: Try with 'FO' segment if implicit (e.g. user typed NIFTY but meant NIFTY Futures?)
        # Or maybe it's just missing data.
        # Let's try explicitly as 'CM' again with relaxed constraints if needed, but get_daily_ohlc handles that.

        # Log specific error
        print(f"Start Turtle Failed: No history for {req.symbol}")
        raise HTTPException(status_code=404, detail=f"No historical data found for {req.symbol}")

    adapter.start(history)

    turtle_instances[adapter.id] = adapter
    return {"instanceId": adapter.id, "initialState": adapter.get_state()}

@router.get("/turtle/state/{instance_id}")
async def get_turtle_state(
    instance_id: str,
    db: Session = Depends(get_db)
):
    adapter = turtle_instances.get(instance_id)
    if not adapter:
        raise HTTPException(status_code=404, detail="Instance not found")

    # Poll for latest price in DB (Real Data Only)
    latest = MarketDataService.get_latest_price(db, adapter.symbol)

    if latest:
        # Update adapter with latest price and date
        # Adapter will only act if date is newer than last processed
        adapter.update(latest["price"], latest["date"])

    return adapter.get_state()

@router.post("/turtle/stop/{instance_id}")
async def stop_turtle(instance_id: str):
    if instance_id in turtle_instances:
        del turtle_instances[instance_id]
    return {"status": "stopped"}


@router.post("/statarb/start")
async def start_statarb(
    req: StatArbStartRequest,
    db: Session = Depends(get_db)
):
    adapter = StatArbAdapter(req.symbol1, req.symbol2, req.ratio, req.z_threshold)

    # Fetch real historical spread
    spread_data = MarketDataService.get_spread_series(db, req.symbol1, req.symbol2, req.ratio, days=100)

    if not spread_data:
        raise HTTPException(status_code=404, detail="Insufficient data for spread calculation")

    adapter.start(spread_data)

    statarb_instances[adapter.id] = adapter
    return {"instanceId": adapter.id, "initialState": adapter.get_state()}

@router.get("/statarb/state/{instance_id}")
async def get_statarb_state(
    instance_id: str,
    db: Session = Depends(get_db)
):
    adapter = statarb_instances.get(instance_id)
    if not adapter:
        raise HTTPException(status_code=404, detail="Instance not found")

    # Fetch latest prices
    p1 = MarketDataService.get_latest_price(db, adapter.symbol1)
    p2 = MarketDataService.get_latest_price(db, adapter.symbol2)

    if p1 and p2:
        # Check dates align? Assuming EOD data, dates should match.
        # If mismatch, we might skip or use latest available.
        # Let's use the later date to drive update.
        date_str = max(p1["date"], p2["date"])
        adapter.update(p1["price"], p2["price"], date_str)

    return adapter.get_state()

@router.post("/statarb/stop/{instance_id}")
async def stop_statarb(instance_id: str):
    if instance_id in statarb_instances:
        del statarb_instances[instance_id]
    return {"status": "stopped"}
