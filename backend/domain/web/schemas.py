from pydantic import BaseModel, Field
from typing import Dict, Optional, List, Any
from datetime import datetime
import uuid

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

class StrategyResponse(BaseModel):
    id: str
    name: str
    type: str
    parameters: Dict[str, Any]
    filters: List[str]
    active: bool
    score: Optional[float]
    created_at: datetime
    updated_at: datetime

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

class VaRRequest(BaseModel):
    portfolio_id: str
    confidence: float = Field(0.95, ge=0, le=1)
    horizon: int = Field(1, ge=1)

class VaRResponse(BaseModel):
    portfolio_id: str
    confidence: float
    horizon: int
    var_value: float
    var_percent: float
    method: str
    timestamp: datetime

# ==========================================
# PORTFOLIO / TRADE DOMAIN SCHEMAS
# ==========================================

class TradeRequest(BaseModel):
    symbol: str
    side: str = Field(..., pattern="^(BUY|SELL)$")
    quantity: int = Field(..., gt=0)
    price: float = Field(..., gt=0)
    strategy_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class TradeResponse(BaseModel):
    id: str
    symbol: str
    side: str
    quantity: int
    entry_price: float
    exit_price: Optional[float]
    pnl: Optional[float]
    strategy_id: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

class PortfolioRequest(BaseModel):
    name: str
    description: Optional[str]
    initial_capital: float = Field(..., gt=0)
    currency: str = "INR"

class PortfolioResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    initial_capital: float
    current_nav: float
    currency: str
    created_at: datetime
    updated_at: datetime

# ==========================================
# SPREAD DOMAIN SCHEMAS
# ==========================================

class LegConfig(BaseModel):
    symbol: str
    operator: str = Field(..., pattern="^[+\\-×÷]$")
    multiplier: float = Field(..., gt=0)
    side: str = Field(..., pattern="^(Buy|Sell)$")
    lots: int = Field(..., gt=0)

class SpreadRequest(BaseModel):
    name: str
    legs: List[LegConfig]
    tags: List[str] = []

class SpreadResponse(BaseModel):
    id: str
    name: str
    legs: List[LegConfig]
    formula: str
    current_price: Optional[float]
    tags: List[str]
    created_at: datetime
    updated_at: datetime

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

# ==========================================
# MARKET EDGE SCHEMAS
# ==========================================

class MarketEdgeResponse(BaseModel):
    """
    Response schema for Trading Edge Panel data.
    """
    sentiment: str = Field(..., example="Bullish")
    regime: str = Field(..., example="Trending")
    index_pe: float = Field(..., example=22.5)
    atm_straddle: float = Field(..., example=450.0)
    atm_iv: float = Field(..., example=12.5)
    timestamp: datetime = Field(default_factory=datetime.now)

# ==========================================
# GENERIC RESPONSE SCHEMAS
# ==========================================

class MessageResponse(BaseModel):
    message: str
    status: str = "success"
    timestamp: datetime = Field(default_factory=datetime.now)

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str]
    status: str = "error"
    timestamp: datetime = Field(default_factory=datetime.now)
