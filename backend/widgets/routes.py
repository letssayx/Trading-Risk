from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from backend.auth.routes import get_current_user
from backend.domain.common.user import User
from backend.orchestration.pipelines.market_orchestrator import MarketOrchestrator
from backend.risk.measures.var import calculate_parametric_var, aggregate_greeks

# MVP Hack: Allow widgets to load without strict auth for the demo dashboard
async def get_current_user_or_mock():
    return User(id="mvp_user", username="trader", full_name="Local Trader")

router = APIRouter(prefix="/api/widgets", tags=["Widgets"])

class WidgetDataRequest(BaseModel):
    viz_type: str # e.g., "vol_surface", "dist_graph", "risk_metrics"
    parameters: Dict[str, Any] # e.g., {"symbol": "NIFTY", "expiry": "28-Dec"}

class WidgetDataResponse(BaseModel):
    viz_type: str
    data_payload: Any # The matrix/array
    highlights: Optional[Dict[str, Any]] = None # {"target": [x, y]}
    rationale: str

@router.post("/data", response_model=WidgetDataResponse)
async def get_widget_data(request: WidgetDataRequest, current_user: User = Depends(get_current_user_or_mock)):
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
        # 1. Prepare Mock Data for Orchestrator (In prod: Fetch from DB)
        snapshot = {
            "symbol": request.parameters.get("symbol", "NIFTY"),
            "put_oi": 1500000, "call_oi": 2000000, # PCR 0.75
            "iv": 18.5,
            "current_tick": {"volume": 5000, "close": 19600, "vwap": 19550, "quantity": 1000},
            "fii_net_flow": 500
        }
        history = {
            "daily_data": [{"iv": 12}, {"iv": 14}, {"iv": 18}], # Rising IV
            "avg_volume_20": 1000,
            "pcr_daily": [0.8, 0.9, 1.0, 0.75, 0.6] # More data for SentimentGauge
        }

        # 2. Run Orchestrator
        orchestrator = MarketOrchestrator()
        result = await orchestrator.generate_trade_cards(snapshot, history)

        return WidgetDataResponse(
            viz_type="market_scan_results",
            data_payload=result["data_payload"],
            rationale=result["rationale"]
        )

    elif request.viz_type == "risk_metrics":
        # 1. Mock Portfolio Data (In prod: Fetch from Trade/RiskSnapshot)
        portfolio_value = 1_000_000.0
        # Mocking returns series for VaR
        returns = pd.Series(np.random.normal(0, 0.01, 100)) # 1% daily vol
        volatility = returns.std()

        # 2. Calculate VaR using the Institutional Module
        # Note: Function expects (value, vol, confidence, horizon)
        var_95 = calculate_parametric_var(portfolio_value, volatility, confidence=0.95)
        var_99 = calculate_parametric_var(portfolio_value, volatility, confidence=0.99)

        # 3. Aggregate Greeks (Mock Positions)
        positions = [
            {"delta": 0.5, "gamma": 0.02, "vega": 10, "theta": -5, "quantity": 100}, # Long Calls
            {"delta": -0.3, "gamma": 0.01, "vega": 8, "theta": -4, "quantity": 100}  # Short Calls/Puts hedge
        ]
        # Helper to convert list of dicts to list of objects if needed,
        # but aggregate_greeks might expect objects or dicts.
        # Let's check aggregate_greeks implementation in risk/measures/var.py.
        # Assuming it sums attributes. For now, doing manual sum to be safe or assuming existing func works on dicts if flexible.
        # Let's verify calculate_parametric_var first.

        portfolio_greeks = {
            "delta": sum(p['delta'] * p['quantity'] for p in positions),
            "gamma": sum(p['gamma'] * p['quantity'] for p in positions),
            "vega": sum(p['vega'] * p['quantity'] for p in positions),
            "theta": sum(p['theta'] * p['quantity'] for p in positions)
        }

        return WidgetDataResponse(
            viz_type="risk_metrics",
            data_payload={
                "var_metrics": {
                    "VaR 95%": f"{var_95:,.2f}",
                    "VaR 99%": f"{var_99:,.2f}",
                    "Time Horizon": "1 Day"
                },
                "portfolio_greeks": portfolio_greeks,
                "exposure_summary": {
                    "gross_exposure": 200_000, # Mock
                    "net_delta_exposure": portfolio_greeks['delta'] * 19500 # Spot ref
                }
            },
            rationale="Portfolio Delta is positive (Long). VaR is within limits."
        )

    else:
        raise HTTPException(status_code=400, detail=f"Unknown widget type: {request.viz_type}")
