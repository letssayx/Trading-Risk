from domain.market.snapshot import InstrumentSnapshot
from domain.indicators.flow import FlowResult, FlowType

def compute_flow(current: InstrumentSnapshot, previous: InstrumentSnapshot) -> FlowResult:
    """
    Determines the FlowType based on Price and Open Interest changes.

    Rules:
    - Price Up, OI Up -> Long Buildup
    - Price Up, OI Down -> Short Covering
    - Price Down, OI Up -> Short Buildup
    - Price Down, OI Down -> Long Unwind
    """

    # Calculate percentage changes
    if previous.price == 0:
        price_change_pct = 0.0
    else:
        price_change_pct = (current.price - previous.price) / previous.price

    if previous.open_interest is None or current.open_interest is None or previous.open_interest == 0:
        oi_change_pct = 0.0
    else:
        oi_change_pct = (current.open_interest - previous.open_interest) / previous.open_interest

    # Determine FlowType
    # Using a small threshold for neutrality to handle noise/flat markets
    THRESHOLD = 0.0001 # 0.01%

    price_up = price_change_pct > THRESHOLD
    price_down = price_change_pct < -THRESHOLD
    oi_up = oi_change_pct > THRESHOLD
    oi_down = oi_change_pct < -THRESHOLD

    if price_up and oi_up:
        flow = FlowType.LONG_BUILDUP
        desc = "Price rose with increasing Open Interest (Long Buildup)."
    elif price_up and oi_down:
        flow = FlowType.SHORT_COVERING
        desc = "Price rose with decreasing Open Interest (Short Covering)."
    elif price_down and oi_up:
        flow = FlowType.SHORT_BUILDUP
        desc = "Price fell with increasing Open Interest (Short Buildup)."
    elif price_down and oi_down:
        flow = FlowType.LONG_UNWIND
        desc = "Price fell with decreasing Open Interest (Long Unwind)."
    else:
        flow = FlowType.NEUTRAL
        desc = "No significant directional flow detected."

    return FlowResult(
        flow_type=flow,
        price_change_pct=price_change_pct,
        oi_change_pct=oi_change_pct,
        description=desc
    )
