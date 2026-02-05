import uuid
from datetime import datetime
from typing import List
from domain.market.snapshot import MarketSnapshot
from domain.market.state import MarketState, SentimentSignal
from domain.ideas.idea import TradeIdea, TradeDirection, TradeRationale, IdeaConstraint
from domain.instruments.option import OptionType
from ideas.generation.utils import find_atm_option
from risk.reports.generator import generate_risk_report

def generate_trade_ideas(market_state: MarketState, market_snapshot: MarketSnapshot) -> List[TradeIdea]:
    """
    Generates structured trade ideas based on the inferred market state and attaches risk reports.
    """
    ideas = []

    # 1. Determine Direction and Strategy
    direction = TradeDirection.NEUTRAL
    target_option_type = None
    strategy_name = ""

    if market_state.sentiment == SentimentSignal.BULLISH:
        direction = TradeDirection.LONG
        target_option_type = OptionType.CALL
        strategy_name = "Long ATM Call"

    elif market_state.sentiment == SentimentSignal.BEARISH:
        direction = TradeDirection.SHORT # Strategy is Short, but for Options we might Buy Put
        # Actually, "Short" direction usually means "Short the market".
        # Buying a Put is a "Short" delta strategy.
        target_option_type = OptionType.PUT
        strategy_name = "Long ATM Put"

    if target_option_type is None:
        return ideas # Neutral/Uncertain, no trade

    # 2. Identify Target Instrument (Simple: ATM Option on NIFTY)
    # Assumption: We are trading NIFTY for this demo context
    target_symbol = "NIFTY"

    # Try to find valid option
    target_snap = find_atm_option(market_snapshot, target_symbol, target_option_type)

    if not target_snap:
        # Fallback: Try identifying from available instruments if NIFTY not found
        # Or just return empty if no suitable instrument
        return ideas

    instrument = target_snap.instrument

    # 3. Construct Trade Rationale
    # Link back to State Evidence
    evidence_summaries = [ev.description for ev in market_state.evidence]
    rationale_text = f"Market is in {market_state.name}. {'; '.join(evidence_summaries)}."

    rationale = TradeRationale(
        summary=f"{strategy_name} on {target_symbol}",
        reasoning_steps=[
            f"Market State: {market_state.name}",
            f"Sentiment: {market_state.sentiment.value}",
            f"Selected Instrument: {instrument.symbol} (Strike: {instrument.strike})"
        ],
        evidence=market_state.evidence # In correct type, this expects IndicatorResult list?
        # MarketStateEvidence has 'supporting_indicators' which are IndicatorResult.
        # But TradeRationale.evidence expects List[IndicatorResult].
        # We should flatten the list.
    )

    all_evidence = []
    for ev in market_state.evidence:
        all_evidence.extend(ev.supporting_indicators)

    # Re-create rationale with correct type
    rationale = TradeRationale(
        summary=f"{strategy_name} on {target_symbol}",
        reasoning_steps=[
            f"Market State: {market_state.name}",
            f"Sentiment: {market_state.sentiment.value}",
            f"Selected Instrument: {instrument.symbol} (Strike: {instrument.strike})"
        ],
        evidence=all_evidence
    )

    # 4. Create Trade Idea
    # Note: user_id is normally passed in, but this function is pure logic.
    # The orchestrator should override the user_id or we assume a system user for generation.
    # For now, we default to "SYSTEM_AUTO" and let the orchestrator update it if needed.
    idea = TradeIdea(
        id=str(uuid.uuid4()),
        user_id="SYSTEM_AUTO",
        timestamp=datetime.now(),
        instruments=[instrument],
        direction=direction,
        rationale=rationale,
        constraints=IdeaConstraint(min_liquidity=50000, max_risk=2000, horizon="Intraday"),
        status="PROPOSED"
    )

    # 5. Attach Risk Report
    risk_report = generate_risk_report(idea, market_snapshot)

    # TradeIdea is frozen, so we need to use `dataclasses.replace` or create with it.
    # But we created it above. Wait, 'risk_summary' is a field.
    # We should create it with risk_summary or use replace.
    # Since it's frozen, we can't set attribute.
    # Let's re-instantiate or assume we can pass it in constructor.

    idea_with_risk = TradeIdea(
        id=idea.id,
        user_id=idea.user_id,
        timestamp=idea.timestamp,
        instruments=idea.instruments,
        direction=idea.direction,
        rationale=idea.rationale,
        constraints=idea.constraints,
        risk_summary=risk_report,
        status="VALIDATED"
    )

    ideas.append(idea_with_risk)

    return ideas
