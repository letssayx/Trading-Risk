from typing import Any
from pydantic import BaseModel
from typing import Dict, Optional

class InstrumentSchema(BaseModel):
    turtle_id: str
    symbol: str
    exchange: str
    exchange_mapping: Dict[str, str] = {} # e.g. {"NSE": "NIFTY-I", "CBOT": "..."}
    details: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
