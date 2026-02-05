from typing import List
from domain.ideas.idea import TradeIdea
from domain.market.snapshot import MarketSnapshot
from domain.risk.report import RiskReport
from domain.risk.standard_scenarios import (
    SCENARIO_PRICE_UP_10, SCENARIO_PRICE_DOWN_10,
    SCENARIO_VOL_EXPAND_20, SCENARIO_VOL_CONTRACT_5
)
from risk.scenarios.evaluator import evaluate_scenario

def generate_risk_report(idea: TradeIdea, market: MarketSnapshot) -> RiskReport:
    """
    Applies standard scenarios to a TradeIdea and compiles a RiskReport.
    """

    # Define standard scenarios to run
    scenarios = [
        SCENARIO_PRICE_UP_10,
        SCENARIO_PRICE_DOWN_10,
        SCENARIO_VOL_EXPAND_20,
        SCENARIO_VOL_CONTRACT_5
    ]

    scenario_results = []

    # Prepare portfolio from idea
    # Assuming the idea suggests buying/selling specific instruments.
    # TradeIdea has `instruments`. Direction applies to the strategy?
    # Usually TradeIdea needs to specify quantities or weights.
    # For now, we assume 1 contract of each for the main direction,
    # or we need logic to parse the structure.
    # Let's assume TradeIdea instruments are just a list.
    # We default to Quantity=1 for Long, -1 for Short based on `idea.direction`.
    # This is a simplification. A real TradeIdea might be "Bull Call Spread"
    # which has Long Call A and Short Call B.
    # The current `TradeIdea` domain object is simple: `instruments: List[Instrument]`, `direction: TradeDirection`.
    # It doesn't map instrument -> quantity explicitly.
    # Implementation constraint: We will treat all instruments in the list as aligned with the `idea.direction`.

    qty_multiplier = 1.0 if idea.direction.value == "LONG" else -1.0
    portfolio = [(inst, 1.0 * qty_multiplier) for inst in idea.instruments]

    for scen in scenarios:
        result = evaluate_scenario(portfolio, scen, market)
        scenario_results.append(result)

    return RiskReport(
        timestamp=market.timestamp,
        entity_id=idea.id,
        scenario_results=scenario_results,
        measures=[], # Can add VaR here later
        assumptions={"quantity_per_instrument": 1.0 * qty_multiplier}
    )
