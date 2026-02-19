from pydantic import BaseModel, Field
from typing import Dict, Optional, List, Any

# ==========================================
# STRATEGY DOMAIN SCHEMAS
# ==========================================

class StrategyRequest(BaseModel):
    """
    Request schema for invoking a specific trading strategy.
    """
    ticker: str = Field(
        ...,
        description="The ticker symbol of the asset to analyze.",
        example="NIFTY"
    )
    signal_type: str = Field(
        "TURTLE",
        description="The type of strategy logic to apply (e.g., TURTLE, MOMENTUM).",
        example="TURTLE"
    )

class SentimentRequest(BaseModel):
    """
    Request schema for market sentiment analysis based on flow data.
    """
    fii_net: float = Field(
        ...,
        description="Net Foreign Institutional Investor (FII) flow in Crores.",
        example=500.0
    )
    pcr: float = Field(
        ...,
        description="Put-Call Ratio (Volume or OI based).",
        example=0.95
    )
    trin: float = Field(
        ...,
        description="TRIN (Arms Index) value.",
        example=1.1
    )
    price_chg: float = Field(
        ...,
        description="Percentage change in price (e.g., 0.015 for 1.5%).",
        example=0.015
    )
    oi_chg: float = Field(
        ...,
        description="Percentage change in Open Interest.",
        example=0.05
    )

class ConvergenceRequest(BaseModel):
    """
    Request schema for checking signal convergence between models.
    """
    turtle_signal: str = Field(
        ...,
        description="Signal output from the Turtle strategy.",
        example="BUY"
    )
    sentiment_signal: str = Field(
        ...,
        description="Signal output from the Sentiment model.",
        example="BUY"
    )


# ==========================================
# RISK DOMAIN SCHEMAS
# ==========================================

class VolArbRequest(BaseModel):
    """
    Request schema for Volatility Arbitrage analysis.
    """
    iv_near: float = Field(
        ...,
        description="Implied Volatility of the near-term expiry.",
        example=0.25
    )
    iv_far: float = Field(
        ...,
        description="Implied Volatility of the far-term expiry.",
        example=0.30
    )

class PCARequest(BaseModel):
    """
    Request schema for PCA-based Factor Analysis.
    """
    returns_matrix: List[List[float]] = Field(
        ...,
        description="2D Matrix of asset returns (rows=samples, cols=assets).",
        example=[[0.01, -0.02], [0.005, 0.01]]
    )


# ==========================================
# UI / WORKBENCH DOMAIN SCHEMAS
# ==========================================

class WidgetRequest(BaseModel):
    """
    Request schema for spawning UI widgets in the Sovereign Workbench.
    """
    tool_name: str = Field(
        ...,
        description="The unique name of the sovereign tool to initialize.",
        example="Turtle Strategy"
    )
    params: Optional[Dict[str, Any]] = Field(
        default={},
        description="Configuration parameters for the tool initialization.",
        example={"lookback": 20}
    )
