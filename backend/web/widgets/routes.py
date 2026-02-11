from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import random

router = APIRouter(prefix="/api/widgets", tags=["Widgets"])

class WidgetRequest(BaseModel):
    tool_name: str
    params: Optional[Dict[str, Any]] = {}

@router.post("/data")
def get_widget_data(req: WidgetRequest):
    """
    Returns data formatted for the widget type (Chart, Metrics, Table).
    """
    name = req.tool_name.lower()

    if "turtle" in name:
        return {
            "type": "metrics",
            "data": {
                "N (ATR)": 145.2,
                "Unit Size": 12,
                "Stop Level": 18200
            }
        }
    elif "chart" in name or "nifty" in name:
        # Mock Candle Data
        return {
            "type": "chart",
            "data": [
                {"time": "2023-01-01", "open": 100, "high": 105, "low": 98, "close": 103},
                {"time": "2023-01-02", "open": 103, "high": 106, "low": 102, "close": 104},
                {"time": "2023-01-03", "open": 104, "high": 110, "low": 104, "close": 109}
            ]
        }
    elif "risk" in name or "var" in name:
        return {
            "type": "metrics",
            "data": {
                "VaR 95%": "$12,500",
                "Expected Shortfall": "$18,000",
                "Status": "STABLE"
            }
        }
    else:
        return {
            "type": "info",
            "data": f"Data for {req.tool_name} not implemented yet."
        }
