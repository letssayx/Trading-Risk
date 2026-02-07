from typing import Dict, Any
import pandas as pd

class BaseStrategy:
    """
    Coordinator pattern: Injects Indicator objects.
    """
    def __init__(self, indicators: Dict[str, Any]):
        self.indicators = indicators

    def run(self, data: pd.DataFrame) -> str:
        raise NotImplementedError
