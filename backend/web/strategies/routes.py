from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from backend.dependencies import get_db
from backend.strategies.models import Strategy
from backend.registry.manager import PluginManager
import pandas as pd
import numpy as np

router = APIRouter(prefix="/strategies", tags=["Strategies"])
plugin_manager = PluginManager()

@router.post("/backtest/preview")
async def backtest_preview(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Runs a Mini-Backtest on the last 30 days of data for a strategy configuration.
    """
    strat_id = payload.get("strategy_id")
    config = payload.get("config", {})

    # 1. Load Strategy (Mock logic for now, or use PluginManager to instantiate with new config)
    # Ideally: instance = plugin_manager.load_class_with_config(...)

    # 2. Fetch Data (Mock 30 days)
    # In prod: db.query(MarketData).filter(...).limit(30)
    # Mocking results based on config to show dynamic behavior

    # If config is "aggressive", higher win rate but lower profit factor?
    # Simple deterministic mock for UI verification:
    threshold = float(config.get("spread_threshold", 5.0))
    win_rate = min(90, 50 + (threshold * 2)) # Higher threshold = higher win rate?
    profit_factor = max(1.0, 3.0 - (threshold * 0.1))

    return {
        "status": "Success",
        "win_rate": round(win_rate, 2),
        "profit_factor": round(profit_factor, 2),
        "period": "Last 30 Days"
    }
