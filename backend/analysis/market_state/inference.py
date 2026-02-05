from datetime import datetime
from typing import List, Optional
from backend.domain.indicators.flow import FlowResult, FlowType
from backend.domain.market.positioning import PositioningSnapshot, ParticipantType
from backend.domain.market.state import MarketState, SentimentSignal, MarketStateEvidence
from backend.domain.indicators.indicator import Indicator, IndicatorResult

def infer_state(flow: FlowResult, positioning: Optional[PositioningSnapshot], snapshot_id: str) -> MarketState:
    """
    Combines short-term flow with institutional positioning to classify the market regime.
    """

    sentiment = SentimentSignal.NEUTRAL
    state_name = "Neutral"
    evidence_list: List[MarketStateEvidence] = []

    # 1. Analyze Flow Evidence
    flow_evidence = MarketStateEvidence(
        description=f"Flow Analysis: {flow.flow_type.value}",
        reasoning=flow.description
    )
    evidence_list.append(flow_evidence)

    # 2. Analyze Positioning Evidence (if available)
    inst_alignment = False

    if positioning:
        fii_net = positioning.net_positions.get(ParticipantType.FII, 0)
        pro_net = positioning.net_positions.get(ParticipantType.PRO, 0)

        # Determine Institutional Bias
        inst_bias = "Neutral"
        if fii_net > 0 and pro_net > 0:
            inst_bias = "Bullish"
        elif fii_net < 0 and pro_net < 0:
            inst_bias = "Bearish"

        pos_desc = f"FII Net: {fii_net:,.0f}, Pro Net: {pro_net:,.0f}. Bias: {inst_bias}"

        pos_evidence = MarketStateEvidence(
            description="Institutional Positioning",
            reasoning=pos_desc
        )
        evidence_list.append(pos_evidence)

        # Check Alignment
        if (flow.flow_type in [FlowType.LONG_BUILDUP, FlowType.SHORT_COVERING] and inst_bias == "Bullish"):
            inst_alignment = True
        elif (flow.flow_type in [FlowType.SHORT_BUILDUP, FlowType.LONG_UNWIND] and inst_bias == "Bearish"):
            inst_alignment = True

    # 3. Synthesize State
    if flow.flow_type == FlowType.LONG_BUILDUP:
        if inst_alignment:
            state_name = "Institutional Accumulation"
            sentiment = SentimentSignal.BULLISH
        else:
            state_name = "Bullish Momentum"
            sentiment = SentimentSignal.BULLISH

    elif flow.flow_type == FlowType.SHORT_COVERING:
        state_name = "Short Covering Rally"
        sentiment = SentimentSignal.BULLISH

    elif flow.flow_type == FlowType.SHORT_BUILDUP:
        if inst_alignment:
            state_name = "Institutional Distribution"
            sentiment = SentimentSignal.BEARISH
        else:
            state_name = "Bearish Pressure"
            sentiment = SentimentSignal.BEARISH

    elif flow.flow_type == FlowType.LONG_UNWIND:
        state_name = "Long Liquidation"
        sentiment = SentimentSignal.BEARISH

    return MarketState(
        name=state_name,
        timestamp=datetime.now(),
        sentiment=sentiment,
        evidence=evidence_list,
        metadata={"snapshot_id": snapshot_id}
    )
