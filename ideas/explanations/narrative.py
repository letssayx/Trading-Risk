from domain.ideas.idea import TradeIdea
from domain.risk.report import RiskReport

def compose_narrative(idea: TradeIdea) -> str:
    """
    Deterministically assembles a narrative explaining the trade idea,
    integrating rationale, evidence, and risk analysis.
    """

    # 1. Header and Thesis
    lines = []
    lines.append(f"**Trade Idea:** {idea.rationale.summary}")
    lines.append(f"**Direction:** {idea.direction.value}")
    lines.append("")

    # 2. The "Why" (Rationale & Evidence)
    lines.append("### Thesis")
    for step in idea.rationale.reasoning_steps:
        lines.append(f"- {step}")

    if idea.rationale.evidence:
        lines.append("")
        lines.append("**Key Evidence:**")
        # Extract descriptions from evidence (IndicatorResults or similar)
        # Ideally, IndicatorResult has a way to describe itself or its value.
        # For now, we assume simple string conversion or value printing.
        for ev in idea.rationale.evidence:
             # Try to get a description if it's a MarketStateEvidence or just Value
             desc = f"{ev.indicator.name}: {ev.value}"
             if hasattr(ev.value, 'description'):
                 desc = f"{ev.indicator.name}: {ev.value.description}"
             lines.append(f"- {desc}")

    # 3. Risk Assessment
    if idea.risk_summary:
        lines.append("")
        lines.append("### Risk Assessment")

        # Highlight worst case from scenarios
        worst_scenario = min(idea.risk_summary.scenario_results, key=lambda x: x.pnl_impact)
        lines.append(f"**Worst Case Scenario:** {worst_scenario.scenario.name}")
        lines.append(f"- Est. PnL Impact: {worst_scenario.pnl_impact:,.2f}")

        # List all scenarios briefly
        lines.append("")
        lines.append("**Stress Test Results:**")
        for res in idea.risk_summary.scenario_results:
            lines.append(f"- {res.scenario.name}: {res.pnl_impact:,.0f}")

    # 4. Explicit Guardrails
    lines.append("")
    lines.append("### Guardrails")
    lines.append("- This is a generated idea based on current market state.")
    lines.append("- Verify liquidity before execution.")
    if idea.constraints:
        lines.append(f"- Horizon: {idea.constraints.horizon}")

    return "\n".join(lines)
