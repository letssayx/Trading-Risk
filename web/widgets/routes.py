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

    elif request.viz_type == "dist_graph":
         return WidgetDataResponse(
            viz_type="dist_graph",
            data_payload={"bins": [-2, -1, 0, 1, 2], "counts": [5, 15, 60, 15, 5]},
            rationale="Returns are normally distributed with no fat tails observed."
         )

    else:
        raise HTTPException(status_code=400, detail=f"Unknown widget type: {request.viz_type}")
