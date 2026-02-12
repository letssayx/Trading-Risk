from pydantic import BaseModel
from typing import Dict, Optional, List, Any

# Strategy Schemas
class StrategyRequest(BaseModel):
    ticker: str
    signal_type: str = "TURTLE"

class SentimentRequest(BaseModel):
    fii_net: float
    pcr: float
    trin: float
    price_chg: float
    oi_chg: float

class ConvergenceRequest(BaseModel):
    turtle_signal: str
    sentiment_signal: str

class VolArbRequest(BaseModel):
    iv_near: float
    iv_far: float

class PCARequest(BaseModel):
    returns_matrix: List[List[float]]

# Widget Schemas
class WidgetRequest(BaseModel):
    tool_name: str
    params: Optional[Dict[str, Any]] = {}
