from typing import List, Dict, Any
from backend.domain.market.snapshot import MarketSnapshot
from backend.risk.scenarios.evaluator import evaluate_scenario
from backend.domain.risk.scenario import Scenario
from backend.risk.measures.var import calculate_parametric_var, aggregate_greeks
from backend.risk.scenarios.generator import ScenarioGenerator

class RiskManager:
    """
    Manages portfolio-level risk and incremental EOD stress testing.
    Updated for Institutional requirements (VaR, Greeks Aggregation).
    """

    def evaluate_portfolio_risk(self, portfolio: List[Dict[str, Any]], market_map: Dict[str, MarketSnapshot]) -> Dict[str, Any]:
        """
        Runs stress tests on a list of positions (Portfolio).
        portfolio: List of {"symbol": str, "quantity": float, "greeks": {...}}
        """
        # 1. Greeks Aggregation
        net_greeks = aggregate_greeks(portfolio)

        # 2. VaR Calculation (Mock Volatility)
        # In prod: fetch historical vol from market_data
        portfolio_value = sum([p['quantity'] * 100 for p in portfolio]) # Mock value
        var_99 = calculate_parametric_var(portfolio_value, vol=0.015, confidence=0.99)

        # 3. Stress Scenarios
        scen_gen = ScenarioGenerator()
        # Mocking the stress test run logic as loop over portfolio is needed
        # Reusing basic scenarios from previous implementation for backward compatibility
        scenarios = [
            Scenario(name="Gap Down 10%", description="Spot -10%", parameters={"spot_move": -0.10}),
            Scenario(name="Vol Spike 20%", description="Vol +20pts", parameters={"vol_shock": 0.20}),
            scen_gen.black_swan_scenario()
        ]

        results = {}
        for scen in scenarios:
            scenario_pnl = 0.0
            for position in portfolio:
                symbol = position.get('symbol')
                qty = position.get('quantity', 0)
                snapshot = market_map.get(symbol)

                if snapshot:
                    instrument = snapshot.instrument
                    res = evaluate_scenario([(instrument, qty)], scen, MarketSnapshot(id="temp", timestamp=snapshot.timestamp, instruments={symbol: snapshot}))
                    scenario_pnl += res.pnl_impact
            results[scen.name] = round(scenario_pnl, 2)

        return {
            "net_greeks": net_greeks,
            "portfolio_var_99": var_99,
            "scenario_results": results
        }
