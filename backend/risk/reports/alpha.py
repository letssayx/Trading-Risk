from typing import Dict, Any, List
from datetime import datetime
import pandas as pd
import numpy as np

def generate_alpha_report(
    portfolio_summary: Dict[str, float],
    risk_metrics: Dict[str, Any],
    attribution: Dict[str, Any],
    market_context: Dict[str, Any] = None
) -> str:
    """
    Generates the 4:15 PM Alpha Report.
    Summarizes daily performance, risk posture, and attribution.
    Includes Governance (LRcc), Tail Risk (EVT), and Regime (HMM).
    """
    report_date = datetime.now().strftime("%Y-%m-%d")

    # Portfolio Performance
    total_nav = portfolio_summary.get("total_nav", 0.0)
    daily_pnl = portfolio_summary.get("daily_pnl", 0.0)
    daily_ret = portfolio_summary.get("daily_return", 0.0) * 100

    # Ratios
    sharpe = portfolio_summary.get("sharpe_ratio", 0.0)
    sortino = portfolio_summary.get("sortino_ratio", 0.0)

    # Risk Metrics
    var_95 = risk_metrics.get("VaR_95", 0.0)
    var_pct = (var_95 / total_nav * 100) if total_nav else 0.0
    top_risks = risk_metrics.get("top_risk_contributors", {})

    # Governance & Tail Risk
    lrcc_decision = risk_metrics.get("LRcc_decision", "N/A")
    lrcc_val = risk_metrics.get("LRcc_value", 0.0)
    evt_var = risk_metrics.get("EVT_VaR", 0.0)
    evt_es = risk_metrics.get("EVT_ES", 0.0)
    tail_buffer = evt_es - var_95 if evt_es > var_95 else 0.0

    # Attribution
    factor_attrib = attribution.get("factor_contributions", {})
    residual = attribution.get("residual_return", 0.0) * 100

    # Construct Report
    lines = []
    lines.append(f"=== 4:15 PM ALPHA REPORT - {report_date} ===")
    lines.append("")
    lines.append("1. PERFORMANCE SUMMARY")
    lines.append(f"   NAV: ${total_nav:,.2f}")
    lines.append(f"   Daily PnL: ${daily_pnl:,.2f} ({daily_ret:+.2f}%)")
    lines.append(f"   Sharpe: {sharpe:.2f} | Sortino: {sortino:.2f}")
    lines.append("")

    lines.append("2. RISK GOVERNANCE & TAIL RISK")
    # Governance Status
    status_icon = "[PASS]" if lrcc_decision == "ACCEPTED" else "[FAIL]"
    lines.append(f"   Model Status (LRcc): {status_icon} {lrcc_decision} (Score: {lrcc_val:.2f} / Crit: 5.99)")

    # Tail Risk Table
    lines.append("   Tail Risk Assessment (EVT):")
    lines.append(f"     - Parametric VaR (95%): ${var_95:,.2f} ({var_pct:.2f}%)")
    if evt_es > 0:
        lines.append(f"     - EVT Expected Shortfall: ${evt_es:,.2f}")
        lines.append(f"     - Tail Loss Buffer: ${tail_buffer:,.2f}")
        lines.append(f"     -> In a tail event, the average expected loss is ${evt_es:,.2f}.")
    else:
        lines.append("     - EVT Expected Shortfall: Insufficient Data")

    lines.append("")
    lines.append("3. RISK CONTRIBUTORS")
    if isinstance(top_risks, dict):
        # Sort by contribution
        sorted_risks = sorted(top_risks.items(), key=lambda x: x[1], reverse=True)[:3]
        for asset, contrib in sorted_risks:
            lines.append(f"     - {asset}: {contrib:.2f}% of Risk")
    lines.append("")

    lines.append("4. FACTOR ATTRIBUTION (Return Drivers)")
    if isinstance(factor_attrib, (dict, pd.Series)):
        if isinstance(factor_attrib, pd.Series):
            factor_attrib = factor_attrib.to_dict()

        # Sort by absolute contribution
        sorted_factors = sorted(factor_attrib.items(), key=lambda x: abs(x[1]), reverse=True)
        for factor, contrib in sorted_factors:
            lines.append(f"     - {factor}: {contrib:+.2f}%")

    lines.append(f"     - Residual/Alpha: {residual:+.2f}%")

    if market_context:
        lines.append("")
        lines.append("5. MARKET CONTEXT")
        regime = market_context.get("regime", "Unknown")
        lines.append(f"   Detected Regime: {regime}")

        movers = market_context.get("top_movers", [])
        if movers:
            lines.append(f"   Top Movers: {', '.join(movers)}")
        sector = market_context.get("sector_performance", {})
        if sector:
            best_sector = max(sector.items(), key=lambda x: x[1]) if sector else ("None", 0)
            lines.append(f"   Best Sector: {best_sector[0]} ({best_sector[1]:+.2f}%)")

    lines.append("")
    lines.append("=== END REPORT ===")

    return "\n".join(lines)
