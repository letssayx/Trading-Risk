from backend.strategies.base_strategy import BaseStrategy
import pandas as pd
from typing import Dict, Any
from datetime import datetime

class RolloverAnalysis(BaseStrategy):
    """
    Analyzes Basis Spread (Future - Spot) and Rollover Cost (Near vs Next).
    """
    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        # Expected df columns: 'spot_price', 'future_price', 'days_to_expiry'
        # Or 'near_price', 'next_price', 'days_near', 'days_next'

        # If simple Basis Monitor
        if 'spot_price' in df.columns and 'future_price' in df.columns:
            df['basis'] = df['future_price'] - df['spot_price']
            # Annualized Basis % = (Basis / Spot) * (365 / DTE)
            # Avoid div by zero
            df['dte'] = df['days_to_expiry'].replace(0, 1)
            df['basis_annualized'] = (df['basis'] / df['spot_price']) * (365 / df['dte']) * 100

        # If Rollover Spread (Calendar)
        if 'near_price' in df.columns and 'next_price' in df.columns:
            df['roll_spread'] = df['next_price'] - df['near_price']

        return df

    def check_signals(self, df: pd.DataFrame, current_pos: Dict[str, Any]) -> str:
        latest = df.iloc[-1]
        rfr = self.config.get("rfr_benchmark", 6.0) # Risk Free Rate %

        basis_yield = latest.get('basis_annualized', 0)

        # Smart Money Integration: If FIIs are net long, reduce threshold for LONG_BASIS
        sm_bias = latest.get('smart_money_bias', 'NEUTRAL')
        threshold = self.config.get("arb_threshold", 1.0)

        if sm_bias == "BULLISH":
            threshold *= 0.5 # More aggressive entry

        # Signal Logic:
        # If Basis Yield > RFR + Threshold => Cash & Carry Opportunity (Long Spot, Short Fut)
        # If Basis Yield < RFR - Threshold => Reverse Arb (Short Spot, Long Fut)

        if basis_yield > (rfr + threshold):
            return "LONG_BASIS"
        elif basis_yield < (rfr - threshold):
            return "SHORT_BASIS"

        return "NEUTRAL"

    def youtube(self) -> None:
        pass
