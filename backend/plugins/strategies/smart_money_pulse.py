from backend.strategies.base_strategy import BaseStrategy
import pandas as pd
import numpy as np
from typing import Dict, Any

class SmartMoneyPulse(BaseStrategy):
    """
    Analyzes Institutional vs Retail Positioning with Participant Fingerprinting.
    """
    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        # Expected df columns:
        # 'fii_long', 'fii_short', 'client_long', 'client_short', 'pro_long', 'pro_short'
        # 'price_change_pct', 'pro_oi_change_pct' (derived from previous rows if time series)

        # 1. Global Flow (FII)
        if 'fii_long' in df.columns:
            df['fii_ratio'] = df['fii_long'] / df['fii_short'].replace(0, 1)

        # 2. Retail Contrarian (Client)
        if 'client_long' in df.columns:
            df['client_ratio'] = df['client_long'] / df['client_short'].replace(0, 1)

        # 3. Local Smart Money (PRO)
        if 'pro_long' in df.columns:
            df['pro_net'] = df['pro_long'] - df['pro_short']
            # Rolling change for SuperHNI detection
            df['pro_oi_change_pct'] = df['pro_net'].pct_change()

        # 4. SuperHNI Detector (Accumulation: OI Up > 10%, Price Stable < 1%)
        if 'price_change_pct' in df.columns and 'pro_oi_change_pct' in df.columns:
            # Mask for stable price
            stable_price = df['price_change_pct'].abs() < 1.0
            # Mask for aggressive accumulation
            aggressive_oi = df['pro_oi_change_pct'] > 0.10

            # Use fillna(False) to handle NaNs from pct_change or initial rows
            df['super_hni_accumulation'] = np.where(stable_price & aggressive_oi, True, False)

        # Ensure the column exists even if conditions not met (e.g. missing columns)
        if 'super_hni_accumulation' not in df.columns:
             df['super_hni_accumulation'] = False

        return df

    def check_signals(self, df: pd.DataFrame, current_pos: Dict[str, Any]) -> str:
        latest = df.iloc[-1]

        # Scores
        fii_score = "BULLISH" if latest.get('fii_ratio', 1.0) > 1.5 else "BEARISH" if latest.get('fii_ratio', 1.0) < 0.6 else "NEUTRAL"
        client_score = "BEARISH" if latest.get('client_ratio', 1.0) > 1.5 else "BULLISH" if latest.get('client_ratio', 1.0) < 0.8 else "NEUTRAL" # Contrarian

        # SuperHNI Flag
        super_hni = latest.get('super_hni_accumulation', False)

        # Logic
        if super_hni:
            return "ULTRA_HIGH_CONVICTION" # Local Smart Money Accumulating

        if fii_score == "BULLISH" and client_score == "BULLISH": # Client Bearish -> Score Bullish
            return "STRONG_BUY_SIGNAL"

        return "NEUTRAL"

    def get_participant_scores(self, df: pd.DataFrame) -> Dict[str, str]:
        """Helper to expose sub-gauges to UI."""
        latest = df.iloc[-1]
        return {
            "global_flow": latest.get('fii_ratio', 1.0),
            "local_desk": latest.get('pro_net', 0),
            "retail_sentiment": latest.get('client_ratio', 1.0),
            "super_hni_alert": bool(latest.get('super_hni_accumulation', False))
        }

    def youtube(self) -> None:
        pass
