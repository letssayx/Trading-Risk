from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from web.auth.routes import get_current_user
from domain.common.user import User

router = APIRouter(prefix="/api/risk", tags=["Risk Analysis"])

class ScenarioView(BaseModel):
    name: str
    pnl_impact: float
    severity: str # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    description: str

class GreekView(BaseModel):
    delta: float
    gamma: float
    vega: float
    theta: float

class RiskAnalysisResponse(BaseModel):
    idea_id: str
    scenarios: List[ScenarioView]
    greeks: GreekView
    contra_indicators: List[str] # The "Why NOT" section

@router.get("/analysis/{idea_id}", response_model=RiskAnalysisResponse)
async def get_risk_analysis(idea_id: str, current_user: User = Depends(get_current_user)):
    """
    Returns structured risk data for the UI, including Scenarios and Greeks.
    """
    # In a real app, retrieve TradeIdea from DB by ID.
    # For now, we return mock data that aligns with our standard scenarios.

    scenarios = [
        ScenarioView(
            name="Price Shock Up 10%",
            pnl_impact=238875.0,
            severity="LOW", # Profit is "LOW" risk
            description="Simulates a 10% sharp rise in underlying."
        ),
        ScenarioView(
            name="Price Shock Down 10%",
            pnl_impact=-150000.0,
            severity="CRITICAL",
            description="Simulates a 10% sharp fall in underlying."
        ),
        ScenarioView(
            name="Vol Expansion +20%",
            pnl_impact=12000.0,
            severity="MEDIUM",
            description="Simulates a massive spike in implied volatility."
        )
    ]

    greeks = GreekView(delta=0.5, gamma=0.002, vega=12.0, theta=-50.0)

    # "Why NOT" - Reasons to be cautious
    contra = [
        "Liquidity is below historical average for this strike.",
        "Event Risk: Earnings announcement in 2 days.",
        "High Gamma risk exposure if price stalls."
    ]

    return RiskAnalysisResponse(
        idea_id=idea_id,
        scenarios=scenarios,
        greeks=greeks,
        contra_indicators=contra
    )
