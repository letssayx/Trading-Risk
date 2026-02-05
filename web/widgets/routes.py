from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from web.auth.routes import get_current_user
from domain.common.user import User

router = APIRouter(prefix="/api/widgets", tags=["Widgets"])

class WidgetDataRequest(BaseModel):
    viz_type: str # e.g., "vol_surface", "dist_graph"
    parameters: Dict[str, Any] # e.g., {"symbol": "NIFTY", "expiry": "28-Dec"}

class WidgetDataResponse(BaseModel):
    viz_type: str
    data_payload: Any # The matrix/array
    highlights: Optional[Dict[str, Any]] = None # {"target": [x, y]}
    rationale: str

@router.post("/data", response_model=WidgetDataResponse)
async def get_widget_data(request: WidgetDataRequest, current_user: User = Depends(get_current_user)):
    """
    Returns standardized data for diverse widget types.
    """
    if request.viz_type == "vol_surface":
        # Mock Vol Surface Data
        # In prod: Query DB for IV across strikes
        return WidgetDataResponse(
            viz_type="vol_surface",
            data_payload=[
                {"strike": 19000, "expiry": "Near", "iv": 14.5},
                {"strike": 19500, "expiry": "Near", "iv": 12.0}, # ATM low
                {"strike": 20000, "expiry": "Near", "iv": 13.5}  # Smile
            ],
            highlights={"target": [19500, "Near"], "label": "Skew Stress"},
            rationale="Volatility smile is flattening, indicating reduced tail risk demand."
        )

    elif request.viz_type == "dist_graph" or request.viz_type == "statistical_distribution":
         return WidgetDataResponse(
            viz_type="statistical_distribution",
            data_payload={
                "labels": [-3.0, -2.0, -1.0, 0, 1.0, 2.0, 3.0],
                "values": [0.004, 0.054, 0.242, 0.399, 0.242, 0.054, 0.004],
                "analysis_markers": {"mean": 0.05, "std_dev": 1.2, "var_95": -2.1, "current_position": 1.5}
            },
            rationale="Returns follow a normal distribution. Current position (+1.5 SD) suggests extended momentum."
         )

    elif request.viz_type == "market_scan_results":
        return WidgetDataResponse(
            viz_type="market_scan_results",
            data_payload={
                "metadata": {"total_opportunities": 12},
                "results": [
                    {
                        "trade_id": "TC-9921",
                        "symbol": "NIFTY-FEB-26",
                        "strategy_tag": "Short Covering Play",
                        "rationale": "High-conviction squeeze identified. FIIs are net long.",
                        "risk_reward": "1:2.5",
                        "worst_case": "-12,400 INR"
                    }
                ]
            },
            rationale="Scanner identified 12 opportunities. Top pick is a Nifty Short Covering play."
        )

    else:
        raise HTTPException(status_code=400, detail=f"Unknown widget type: {request.viz_type}")
