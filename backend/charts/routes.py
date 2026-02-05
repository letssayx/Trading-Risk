from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter(prefix="/api", tags=["Charting"])

class ChartConfig(BaseModel):
    widget_config: Dict[str, Any]

@router.get("/chart-config/{symbol}", response_model=ChartConfig)
async def get_chart_config(symbol: str):
    """
    Returns configuration for the TradingView widget for the given symbol.
    In a real app, this might map internal symbols to TradingView symbols.
    """
    # Mapping logic (Mock)
    tv_symbol = symbol
    if symbol == "NIFTY":
        tv_symbol = "NSE:NIFTY"

    config = {
        "symbol": tv_symbol,
        "interval": "D",
        "timezone": "Asia/Kolkata",
        "theme": "dark",
        "style": "1",
        "locale": "in",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": False,
        "allow_symbol_change": True,
        "container_id": "tradingview_widget"
    }

    return ChartConfig(widget_config=config)
