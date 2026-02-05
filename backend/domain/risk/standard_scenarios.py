from backend.domain.risk.scenario import Scenario

def price_shock_scenario(pct_change: float) -> Scenario:
    direction = "Up" if pct_change > 0 else "Down"
    return Scenario(
        name=f"Price Shock {direction} {abs(pct_change)*100:.1f}%",
        description=f"Simulates a {pct_change*100:.1f}% change in the underlying price.",
        parameters={"spot_move": pct_change}
    )

def vol_shock_scenario(vol_change_points: float) -> Scenario:
    direction = "Expansion" if vol_change_points > 0 else "Contraction"
    return Scenario(
        name=f"Vol {direction} {abs(vol_change_points):.1f}pts",
        description=f"Simulates a {vol_change_points:.1f} percentage point change in implied volatility.",
        parameters={"vol_shock": vol_change_points}
    )

# Standard Definitions
SCENARIO_PRICE_UP_10 = price_shock_scenario(0.10)
SCENARIO_PRICE_DOWN_10 = price_shock_scenario(-0.10)
SCENARIO_PRICE_UP_20 = price_shock_scenario(0.20)
SCENARIO_PRICE_DOWN_20 = price_shock_scenario(-0.20)

SCENARIO_VOL_EXPAND_10 = vol_shock_scenario(0.10) # +10% vol
SCENARIO_VOL_EXPAND_20 = vol_shock_scenario(0.20) # +20% vol
SCENARIO_VOL_CONTRACT_5 = vol_shock_scenario(-0.05) # -5% vol
