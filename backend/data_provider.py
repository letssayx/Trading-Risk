import pandas as pd
from typing import Dict, Any

try:
    from nsepython import nse_optionchain_scrapper
    NSEPYTHON_AVAILABLE = True
except ImportError:
    NSEPYTHON_AVAILABLE = False

def get_nifty_option_chain(symbol: str = "NIFTY") -> Dict[str, Any]:
    """
    Fetches the live Option Chain from NSE for analysis.
    Uses nsepython if available, otherwise returns mock structure for offline/safe mode.
    """
    if NSEPYTHON_AVAILABLE:
        try:
            payload = nse_optionchain_scrapper(symbol)
            if payload:
                # Extracting core data for Turtle's Scanners
                records = payload.get('records', {}).get('data', [])
                df = pd.json_normalize(records)

                return {
                    "timestamp": payload.get('records', {}).get('timestamp', "Unknown"),
                    "underlying": payload.get('records', {}).get('underlyingValue', 0),
                    "data": df
                }
        except Exception as e:
            print(f"⚠️ NSE Data Fetch Error: {e}")
            pass # Fallback to mock

    # Mock Data for Development/Sandbox
    print(f"⚠️ Using Mock Data for {symbol} (NSEPython not connected/installed)")

    mock_data = [
        {"strikePrice": 19500, "CE.openInterest": 200000, "PE.openInterest": 150000, "CE.lastPrice": 150, "PE.lastPrice": 80},
        {"strikePrice": 19600, "CE.openInterest": 250000, "PE.openInterest": 100000, "CE.lastPrice": 100, "PE.lastPrice": 120}
    ]

    return {
        "timestamp": "2026-02-06 15:30:00",
        "underlying": 19550.0,
        "data": pd.DataFrame(mock_data)
    }
