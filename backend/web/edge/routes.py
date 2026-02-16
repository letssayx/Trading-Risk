from fastapi import APIRouter
from backend.domain.web.schemas import MarketEdgeResponse
import random
from datetime import datetime

router = APIRouter(prefix="/api/edge", tags=["Trading Edge"])

@router.get("", response_model=MarketEdgeResponse)
async def get_market_edge():
    """
    Returns real-time market context data for the Trading Edge panel.
    Currently returns mock data.
    """
    # Mock Logic
    sentiments = ["Bullish", "Bearish", "Neutral"]
    regimes = ["Trending", "Ranging", "Volatile"]

    return {
        "sentiment": random.choice(sentiments),
        "regime": random.choice(regimes),
        "index_pe": round(random.uniform(20.0, 25.0), 2),
        "atm_straddle": round(random.uniform(400.0, 600.0), 2),
        "atm_iv": round(random.uniform(10.0, 20.0), 2),
        "timestamp": datetime.now()
    }
