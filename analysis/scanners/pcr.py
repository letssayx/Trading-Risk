from typing import Dict, Any, Optional
import pandas as pd

def scan_pcr_mean_reversion(current_snapshot: Dict[str, Any], historical_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Scans for sentiment extremes where PCR deviates significantly from the mean.
    """
    # 1. Calculate Current PCR
    # Assumption: snapshot has 'put_oi' and 'call_oi' aggregates
    put_oi = current_snapshot.get('put_oi', 0)
    call_oi = current_snapshot.get('call_oi', 0)

    if call_oi == 0:
        return None

    current_pcr = put_oi / call_oi

    # 2. Compare to Historical Mean (e.g., 20-day rolling)
    if 'pcr_daily' not in historical_data.columns:
        return None

    pcr_history = historical_data['pcr_daily']
    pcr_mean = pcr_history.mean()
    pcr_std = pcr_history.std()

    if pcr_std == 0:
        return None

    # 3. Define Logic Triggers (Z-Score > 2.0 or < -2.0)
    z_score = (current_pcr - pcr_mean) / pcr_std

    # 4. Filter for 'Large Buy Orders' & Institutional Flow (Mocked check)
    fii_positioning = current_snapshot.get('fii_net_flow', 0)

    # Logic: Low PCR (Oversold) + FII Buying = Long Opportunity
    if z_score < -2.0 and fii_positioning > 0:
        return {
            "value": round(current_pcr, 2),
            "state": "Oversold",
            "z_score": round(z_score, 2),
            "rationale": "PCR is 2SD below mean, suggesting oversold conditions. FII accumulation detected."
        }

    # Logic: High PCR (Overbought) + FII Selling = Short Opportunity
    if z_score > 2.0 and fii_positioning < 0:
        return {
            "value": round(current_pcr, 2),
            "state": "Overbought",
            "z_score": round(z_score, 2),
            "rationale": "PCR is 2SD above mean, suggesting overbought conditions. FII distribution detected."
        }

    return None
