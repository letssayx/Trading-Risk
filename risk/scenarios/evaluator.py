from typing import List, Dict, Tuple
from domain.instruments.instrument import Instrument
from domain.instruments.option import OptionContract
from domain.market.snapshot import MarketSnapshot, InstrumentSnapshot
from domain.risk.scenario import Scenario, ScenarioResult

def evaluate_scenario(
    instruments: List[Tuple[Instrument, float]], # List of (Instrument, Quantity)
    scenario: Scenario,
    market: MarketSnapshot
) -> ScenarioResult:
    """
    Estimates the PnL impact of a scenario on a portfolio using Delta/Gamma/Vega approximations.
    """
    total_pnl = 0.0
    details = {}

    spot_shock_pct = scenario.parameters.get("spot_move", 0.0)
    vol_shock_points = scenario.parameters.get("vol_shock", 0.0)

    for instrument, quantity in instruments:
        snapshot = market.get_instrument_snapshot(instrument.id)
        if not snapshot:
            details[instrument.symbol] = "Missing Snapshot"
            continue

        pnl = 0.0
        greeks = snapshot.greeks
        current_price = snapshot.price

        # 1. Delta PnL: Delta * Change in Spot Price
        # Note: Delta is usually per 1 unit of underlying.
        # For options, we assume delta is 0-1 (or 0-100). Standard is 0-1.
        # Change in Spot = Spot * spot_shock_pct
        # But we don't have Spot price in InstrumentSnapshot if it's an option,
        # we have the Option Price.
        # We need the Underlying Price.
        # For simplicity in this approximation, we assume:
        # PnL ~= Delta * (UnderlyingPrice * shock)
        # Wait, if we don't have Underlying Price easily, we can't scale the % shock.
        # Ideally, MarketSnapshot should allow looking up the underlying.

        # Assumption: For this version, we will assume the scenario parameter 'spot_move'
        # applies to the instrument price directly if it's linear (Future),
        # or we try to infer underlying price.

        # Better approach: The scenario defines "spot_move" (%).
        # If it's a Future, PnL = Price * spot_move * quantity * contract_size (if Delta=1)
        # If it's an Option, PnL = Delta * (UnderlyingPrice * spot_move) + ...

        # Let's assume we can get Underlying Price from the snapshot or we estimate it.
        # If we lack Underlying Price, we can't accurately compute Delta PnL from % move.
        # Let's assume we treat 'spot_move' as 'instrument_move' for linear,
        # but for options we need the underlying.

        # Workaround: Use the 'price' of the instrument as a proxy for underlying price
        # ONLY IF we can't find the underlying.
        # But for options, price != underlying.

        # Let's verify if we can assume the underlying is in the market snapshot.
        underlying = instrument.underlying if hasattr(instrument, 'underlying') else None
        underlying_price = 0.0

        if underlying:
             # Try to find underlying snapshot.
             # Only possible if underlying ID is known or standard.
             # For now, let's assume `snapshot.metadata['underlying_price']` exists
             # or we skip Delta calcs if missing.
             underlying_price = snapshot.metadata.get('underlying_price', 0.0)

        delta = greeks.get('delta', 0.0)
        gamma = greeks.get('gamma', 0.0)
        vega = greeks.get('vega', 0.0)

        if underlying_price > 0:
            spot_change = underlying_price * spot_shock_pct

            # Delta PnL
            delta_pnl = delta * spot_change

            # Gamma PnL: 0.5 * Gamma * (SpotChange^2)
            gamma_pnl = 0.5 * gamma * (spot_change ** 2)

            # Vega PnL: Vega * VolChange (points)
            # Vega is usually change per 1% vol change (0.01) or 1 point?
            # Standard convention: Vega is change per 1 percentage point (e.g. 1.0 change in IV).
            # If vol_shock_points is 0.10 (10%), that is 10 points? Or 10% relative?
            # Standard scenarios defined: 0.10 means 10% (0.10).
            # If IV goes 20% -> 30%, that is +0.10 or +10 points?
            # Let's assume input is raw float (e.g., 0.10) and Vega is per 1 unit (100%).
            # Usually Vega is PnL per 1% change in vol.
            # So if vol increases by 10% (0.10), that is 10 units of Vega.
            # Let's assume vol_shock_points is e.g. 0.05 for 5%.
            # So we multiply by 100 to get "points".
            vega_pnl = vega * (vol_shock_points * 100)

            pnl = (delta_pnl + gamma_pnl + vega_pnl) * quantity * instrument.contract_size

        else:
            # Fallback for linear instruments (Futures) without explicit Delta/Underlying
            # If it's a future, Delta is approx 1.
            # PnL = Price * pct_change * quantity * contract_size
            if hasattr(instrument, 'expiry'): # Simple check for derivative
                 pnl = current_price * spot_shock_pct * quantity * instrument.contract_size
            else:
                 pnl = 0.0 # Can't evaluate

        total_pnl += pnl
        details[instrument.symbol] = {
            "pnl": pnl,
            "delta_pnl": delta_pnl * quantity * instrument.contract_size if underlying_price > 0 else 0,
            "gamma_pnl": gamma_pnl * quantity * instrument.contract_size if underlying_price > 0 else 0,
            "vega_pnl": vega_pnl * quantity * instrument.contract_size if underlying_price > 0 else 0
        }

    return ScenarioResult(
        scenario=scenario,
        pnl_impact=total_pnl,
        details=details
    )
