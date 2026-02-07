import pandas as pd
from backend.core.risk.metrics import ParametricVaR

class PortfolioManager:
    """
    Ingests trades and links to RiskEngine.
    """
    def __init__(self):
        self.holdings = pd.DataFrame()
        self.risk_engine = ParametricVaR()

    def ingest_csv(self, csv_content: bytes):
        self.holdings = pd.read_csv(pd.io.common.BytesIO(csv_content))
        return len(self.holdings)

    def calculate_health(self) -> dict:
        if self.holdings.empty: return {"status": "Empty"}

        # Mock calculation: Total Value
        total_val = self.holdings['value'].sum() if 'value' in self.holdings.columns else 0

        # Mock Returns for VaR
        import numpy as np
        mock_returns = np.random.normal(0, 0.01, 100) # 1% Vol

        var_99 = self.risk_engine.calculate(total_val, 0.01, 0.99)

        return {
            "total_value": total_val,
            "var_99": var_99,
            "status": "Healthy" if var_99 < (total_val * 0.05) else "Risk Alert"
        }
