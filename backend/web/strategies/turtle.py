from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
from pydantic import BaseModel
import pandas as pd
import numpy as np

from backend.strategies.turtle import TurtleLegacyStrategy
from backend.domain.portfolio.manager import PortfolioManager
from backend.risk.manager import RiskManager

router = APIRouter(prefix="/strategies/turtle", tags=["Turtle Strategy"])

class NRequest(BaseModel):
    highs: List[float]
    lows: List[float]
    closes: List[float]
    period: int = 20

class UnitSizeRequest(BaseModel):
    total_capital: float
    n_value: float
    tick_value: float

class StopRequest(BaseModel):
    entry_price: float
    n_value: float
    side: str = "LONG"

class RiskImbalanceRequest(BaseModel):
    weights: Dict[str, float]
    cov_matrix: List[List[float]] # Nested list for matrix
    assets: List[str] # To map matrix indices
    risk_budgets: Optional[Dict[str, float]] = None
    threshold: float = 0.15

@router.post("/calculate-n")
def calculate_n(request: NRequest):
    if len(request.highs) != len(request.lows) or len(request.highs) != len(request.closes):
        raise HTTPException(status_code=400, detail="Input arrays must have same length")

    # Create dummy manager just for strategy instantiation (N calculation doesn't use it)
    pm = PortfolioManager(trades=[])
    strategy = TurtleLegacyStrategy(portfolio_manager=pm)

    highs = pd.Series(request.highs)
    lows = pd.Series(request.lows)
    closes = pd.Series(request.closes)

    n_val = strategy.calculate_N(highs, lows, closes, request.period)
    return {"n_value": n_val}

@router.post("/calculate-unit-size")
def calculate_unit_size(request: UnitSizeRequest):
    pm = PortfolioManager(trades=[], total_capital=request.total_capital)
    strategy = TurtleLegacyStrategy(portfolio_manager=pm)
    strategy.N = request.n_value

    units = strategy.calculate_unit_size(request.tick_value)
    return {"unit_size": units}

@router.post("/calculate-stop")
def calculate_stop(request: StopRequest):
    pm = PortfolioManager(trades=[])
    strategy = TurtleLegacyStrategy(portfolio_manager=pm)
    strategy.N = request.n_value

    stop = strategy.calculate_stop_price(request.entry_price, request.side)
    return {"stop_price": stop}

@router.post("/check-risk-imbalance")
def check_risk_imbalance(request: RiskImbalanceRequest):
    rm = RiskManager()

    assets = request.assets
    weights = pd.Series(request.weights)
    cov = pd.DataFrame(request.cov_matrix, index=assets, columns=assets)

    budgets = pd.Series(request.risk_budgets) if request.risk_budgets else None

    imbalances = rm.check_risk_imbalance(weights, cov, budgets, request.threshold)

    suggested_weights = rm.suggest_risk_balanced_weights(cov, budgets)

    return {
        "imbalances": imbalances,
        "suggested_weights": suggested_weights.to_dict()
    }
