import pandas as pd
from typing import List, Dict, Any

class PriceOiAnalyzer:
    """
    Analyzes Price vs Open Interest to determine market sentiment.
    """

    @staticmethod
    def analyze_symbol(symbol: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyzes a list of daily data points (must include 'close' and 'open_interest').
        Returns the latest interpretation and the time series for plotting.
        """
        if not data or len(data) < 2:
            return {"error": "Insufficient data"}

        df = pd.DataFrame(data)

        # Calculate Changes
        df['price_chg'] = df['close'].diff()
        df['price_chg_pct'] = df['close'].pct_change() * 100
        df['oi_chg'] = df['open_interest'].diff()
        df['oi_chg_pct'] = df['open_interest'].pct_change() * 100

        # Drop NaN rows (first row after diff)
        df.dropna(inplace=True)

        # Determine Interpretation
        def interpret(row):
            p_chg = row['price_chg']
            oi_chg = row['oi_chg']

            if pd.isna(p_chg) or pd.isna(oi_chg):
                return "N/A"

            if p_chg > 0 and oi_chg > 0:
                return "Long Build Up"
            elif p_chg > 0 and oi_chg < 0:
                return "Short Covering"
            elif p_chg < 0 and oi_chg > 0:
                return "Short Build Up"
            elif p_chg < 0 and oi_chg < 0:
                return "Long Unwinding"
            return "Neutral"

        df['interpretation'] = df.apply(interpret, axis=1)

        # Prepare Result
        latest = df.iloc[-1]

        return {
            "symbol": symbol,
            "latest": {
                "date": latest['time'] if 'time' in latest else str(latest.name),
                "price": latest['close'],
                "oi": int(latest['open_interest']),
                "price_chg_pct": round(latest['price_chg_pct'], 2),
                "oi_chg_pct": round(latest['oi_chg_pct'], 2),
                "interpretation": latest['interpretation']
            },
            "history": df[['time', 'close', 'open_interest', 'price_chg_pct', 'oi_chg_pct', 'interpretation']].tail(20).to_dict(orient='records')
        }
