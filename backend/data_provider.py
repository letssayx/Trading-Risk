import pandas as pd
from typing import Dict, Any

try:
    from nsepython import nse_optionchain_scrapper
    NSEPYTHON_AVAILABLE = True
except ImportError:
    NSEPYTHON_AVAILABLE = False

try:
    import upstox_client
    from upstox_client.rest import ApiException
    from backend.config import Config
    UPSTOX_AVAILABLE = True
except ImportError:
    UPSTOX_AVAILABLE = False

def get_nifty_option_chain(symbol: str = "NIFTY", expiry_date: str = "2026-03-26") -> Dict[str, Any]:
    """
    Fetches the live Option Chain from Upstox (Preferred) or NSEPython (Fallback).
    """
    # 1. Try Upstox API
    if UPSTOX_AVAILABLE and Config.MARKET_DATA_KEY and len(Config.MARKET_DATA_KEY) > 20: # Heuristic for real key
        try:
            configuration = upstox_client.Configuration()
            configuration.access_token = Config.MARKET_DATA_KEY # Assumes Access Token is stored here after Auth flow

            api_instance = upstox_client.OptionsApi(upstox_client.ApiClient(configuration))
            # Format symbol for Upstox: NSE_INDEX|Nifty 50
            upstox_symbol = "NSE_INDEX|Nifty 50" if symbol == "NIFTY" else symbol

            api_response = api_instance.get_put_call_option_chain(upstox_symbol, expiry_date)

            # Map Upstox response to standard DF
            if api_response and api_response.data:
                # Logic to convert api_response.data to DataFrame structure expected by scanners
                # Mocking this mapping for now as it depends on exact Upstox response schema
                return {
                    "timestamp": "Live",
                    "underlying": 0, # Need to fetch LTP separately usually
                    "data": pd.DataFrame(api_response.data)
                }
        except Exception as e:
             print(f"⚠️ Upstox Fetch Error: {e}")

    # 2. Fallback to NSEPython
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
