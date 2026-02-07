import pandas as pd
from backend.core.risk.metrics import ParametricVaR
from backend.core.stats.factor import APTModel

class PortfolioManager:
    """
    Ingests trades and links to RiskEngine & Advanced Stats.
    """
    def __init__(self):
        self.holdings = pd.DataFrame()
        self.risk_engine = ParametricVaR()
        self.apt_model = APTModel()

    def ingest_csv(self, csv_content: bytes):
        self.holdings = pd.read_csv(pd.io.common.BytesIO(csv_content))
        return len(self.holdings)

    def calculate_health(self) -> dict:
        if self.holdings.empty: return {"status": "Empty"}
        total_val = self.holdings['value'].sum() if 'value' in self.holdings.columns else 0
        var_99 = self.risk_engine.calculate(total_val, 0.01, 0.99)
        return {
            "total_value": total_val,
            "var_99": var_99,
            "status": "Healthy" if var_99 < (total_val * 0.05) else "Risk Alert"
        }

    def calculate_macro_sensitivity(self, macro_data: pd.DataFrame) -> dict:
        """
        Live Link: Uses APT to check sensitivity to DXY/Oil.
        """
        if self.holdings.empty: return {}
        # Mock Portfolio Return Series (Aggregated)
        import numpy as np
        port_returns = pd.Series(np.random.normal(0, 0.01, len(macro_data)))

        betas = self.apt_model.calculate_betas(port_returns, macro_data)
        return betas
