from typing import List, Dict, Any
from backend.domain.risk.scenario import Scenario
from backend.risk.scenarios.evaluator import evaluate_scenario
from backend.domain.market.snapshot import MarketSnapshot

class ScenarioGenerator:
    """
    Generates institutional stress scenarios.
    """

    @staticmethod
    def black_swan_scenario() -> Scenario:
        return Scenario(
            name="Black Swan",
            description="Spot -20%, Vol +50%",
            parameters={"spot_move": -0.20, "vol_shock": 0.50}
        )

    @staticmethod
    def rate_shock_scenario() -> Scenario:
        return Scenario(
            name="Rate Shock",
            description="Interest Rate +100bps",
            parameters={"rate_shock": 0.01}
        )

    def run_stress_test(self, portfolio: List[Any], market_map: Dict[str, MarketSnapshot]) -> Dict[str, float]:
        """
        Runs standard institutional shocks on a portfolio.
        """
        scenarios = [self.black_swan_scenario(), self.rate_shock_scenario()]
        results = {}

        # Simplified execution logic (reusing evaluator)
        # Note: In real app, we need to adapt portfolio structure to what evaluate_scenario expects
        # For now, mocking the aggregate result logic similar to RiskManager

        for scen in scenarios:
            # Placeholder: In a real implementation, we'd map the portfolio to the evaluator inputs
            results[scen.name] = 0.0 # Implementation detail: reuse evaluate_scenario

        return results
