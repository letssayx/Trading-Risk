from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional, List
import pandas as pd
import numpy as np

from backend.analysis.beta import calculate_beta, calculate_rolling_beta
from backend.risk.hedging import calculate_index_hedge, calculate_sentiment_hedge

router = APIRouter(prefix="/strategies/hedge", tags=["Hedge Commander"])

class BetaRequest(BaseModel):
    asset_returns: List[float]
    market_returns: List[float]
    window: int = 252

class HedgeRequest(BaseModel):
    portfolio_betas: Dict[str, float]
    portfolio_notional: Dict[str, float]
    index_price: float
    index_lot_size: int = 50 # Nifty
    market_neutral_target: float = 0.0

class SentimentHedgeRequest(BaseModel):
    base_contracts: int
    fii_net_cash: float # Crores
    pcr: float
    trin: float

@router.post("/calculate-beta")
def get_beta(request: BetaRequest):
    if len(request.asset_returns) != len(request.market_returns):
        raise HTTPException(status_code=400, detail="Return series must align")

    asset = pd.Series(request.asset_returns)
    mkt = pd.Series(request.market_returns)

    beta = calculate_beta(asset, mkt, request.window)
    return {"beta": beta}

@router.post("/calculate-index-hedge")
def get_index_hedge(request: HedgeRequest):
    result = calculate_index_hedge(
        request.portfolio_betas,
        request.portfolio_notional,
        request.index_price,
        request.index_lot_size,
        request.market_neutral_target
    )
    return result

@router.post("/calculate-sentiment-hedge")
def get_sentiment_hedge(request: SentimentHedgeRequest):
    result = calculate_sentiment_hedge(
        request.base_contracts,
        request.fii_net_cash,
        request.pcr,
        request.trin
    )
    return result
