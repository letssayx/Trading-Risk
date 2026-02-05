from datetime import date
from typing import List, Optional, Dict
from domain.market.snapshot import MarketSnapshot, InstrumentSnapshot
from domain.instruments.option import OptionContract, OptionType

def find_atm_option(
    market: MarketSnapshot,
    underlying_symbol: str,
    option_type: OptionType,
    expiry_date: Optional[date] = None
) -> Optional[InstrumentSnapshot]:
    """
    Finds the At-The-Money (ATM) option for a given underlying in the market snapshot.
    """
    # 1. Find Underlying Spot Price
    # Try to find a snapshot for the underlying itself or use metadata
    # This is a simplification. In a real system, we'd look up the underlying asset's snapshot.
    # We'll scan instruments to find the underlying price from metadata of options or a future.

    spot_price = None

    # Strategy A: Check if underlying is in instruments
    # Strategy B: Check metadata of any option for 'underlying_price'

    candidates: List[InstrumentSnapshot] = []

    for inst_id, snap in market.instruments.items():
        inst = snap.instrument

        # Check if this is the underlying
        if hasattr(inst, 'symbol') and inst.symbol == underlying_symbol: # Simple match
             spot_price = snap.price

        # Check metadata
        if spot_price is None and snap.metadata.get('underlying_price'):
            spot_price = snap.metadata['underlying_price']

        # Collect candidates
        if isinstance(inst, OptionContract):
            if inst.underlying.symbol == underlying_symbol and inst.option_type == option_type:
                # If expiry is specified, match it
                if expiry_date and inst.expiry != expiry_date:
                    continue
                candidates.append(snap)

    if spot_price is None or not candidates:
        return None

    # 2. Sort by distance to spot price
    # ATM means strike closest to spot
    candidates.sort(key=lambda x: abs(x.instrument.strike - spot_price))

    return candidates[0] if candidates else None
