from dataclasses import dataclass
from datetime import date
from enum import Enum
from .instrument import Instrument
from .asset import UnderlyingAsset

class OptionType(Enum):
    CALL = "CALL"
    PUT = "PUT"

class OptionStyle(Enum):
    EUROPEAN = "EUROPEAN"
    AMERICAN = "AMERICAN"

@dataclass(frozen=True, kw_only=True)
class OptionContract(Instrument):
    """Option contract definition."""
    expiry: date
    strike: float
    option_type: OptionType
    style: OptionStyle
    underlying: UnderlyingAsset
