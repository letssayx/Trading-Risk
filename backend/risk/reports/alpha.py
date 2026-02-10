from typing import Dict, Any, List
from datetime import datetime
import pandas as pd

def generate_alpha_report(
    portfolio_summary: Dict[str, float],
    risk_metrics: Dict[str, Any],
    attribution: Dict[str, Any],
    market_context: Dict[str, Any] = None
) -> str:
    """
    Generates the 4:15 PM Alpha Report.
    Summarizes daily performance, risk posture, and attribution.
    """
    report_date = datetime.now().strftime("%Y-%m-%d")

    # Portfolio Performance
    total_nav = portfolio_summary.get("total_nav", 0.0)
    daily_pnl = portfolio_summary.get("daily_pnl", 0.0)
    daily_ret = portfolio_summary.get("daily_return", 0.0) * 100

    # Risk Metrics
    var_95 = risk_metrics.get("VaR_95", 0.0)
    var_pct = (var_95 / total_nav * 100) if total_nav else 0.0
    top_risks = risk_metrics.get("top_risk_contributors", {})

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
    lines.append("")

    lines.append("2. RISK PROFILE (VaR 95%)")
    lines.append(f"   Total VaR: ${var_95:,.2f} ({var_pct:.2f}%)")
    lines.append("   Top Risk Contributors:")
    if isinstance(top_risks, dict):
        # Sort by contribution
        sorted_risks = sorted(top_risks.items(), key=lambda x: x[1], reverse=True)[:3]
        for asset, contrib in sorted_risks:
            lines.append(f"     - {asset}: {contrib:.2f}% of Risk")
    lines.append("")

    lines.append("3. FACTOR ATTRIBUTION (Return Drivers)")
    if isinstance(factor_attrib, (dict, pd.Series)):
        if isinstance(factor_attrib, pd.Series):
            factor_attrib = factor_attrib.to_dict()

        # Sort by absolute contribution
        sorted_factors = sorted(factor_attrib.items(), key=lambda x: abs(x[1]), reverse=True)
        for factor, contrib in sorted_factors:
            # Assuming contrib is already annualized or scaled appropriately
            # If not, we might need label
            lines.append(f"     - {factor}: {contrib:+.2f}%")

    lines.append(f"     - Residual/Alpha: {residual:+.2f}%")

    if market_context:
        lines.append("")
        lines.append("4. MARKET CONTEXT")
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
