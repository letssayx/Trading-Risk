import asyncio
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from backend.analysis.scanners.pcr import scan_pcr_mean_reversion
from backend.analysis.scanners.volatility import calculate_iv_metrics
from backend.analysis.scanners.order_flow import detect_institutional_buying
from backend.analysis.scanners.relative_value import PairsEngine
from backend.analysis.scanners.sentiment import SentimentGauge
from backend.analysis.derivatives_indicators.flow import get_oi_quadrant

# In a real app, import evaluate_scenario. Mocking for now to avoid circular deps or complex setup.

class MarketOrchestrator:
    """
    Coordinates scanner execution and aggregates results into Trade Cards.
    """

    async def generate_trade_cards(self, snapshot: Dict[str, Any], history: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs scanners in parallel and builds the unified JSON response.
        """
        # 1. Unpack history for specific scanners
        # Mocking pandas structures from dict
        try:
            hist_df = pd.DataFrame(history.get('daily_data', []))
            iv_series = hist_df['iv'] if 'iv' in hist_df.columns else pd.Series()
            avg_vol = history.get('avg_volume_20', 1000)

            # Helper for SentimentGauge
            pcr_series = pd.Series(history.get('pcr_daily', [])) if 'pcr_daily' in history else pd.Series()
        except Exception:
            # Fallback for empty/malformed history
            hist_df = pd.DataFrame()
            iv_series = pd.Series()
            pcr_series = pd.Series()
            avg_vol = 1000

        # 2. Run all "Points" in parallel
        # Note: These functions are sync, so we wrap them or run directly if fast.
        # For asyncio.gather, they should be async or wrapped in run_in_executor.

        loop = asyncio.get_running_loop()

        # Existing Functional Scanners
        pcr_task = loop.run_in_executor(None, scan_pcr_mean_reversion, snapshot, hist_df)
        vol_task = loop.run_in_executor(None, calculate_iv_metrics, snapshot.get('iv', 0), iv_series)
        flow_task = loop.run_in_executor(None, detect_institutional_buying, snapshot.get('current_tick', {}), avg_vol)

        # New Class-Based Scanners (Instantiate and Run)
        pairs_engine = PairsEngine()
        sentiment_engine = SentimentGauge()

        # Mocking a second series for Relative Value (e.g., BankNifty vs Nifty)
        # In prod, this would come from a multi-ticker data fetch.
        series_a = iv_series # Proxy
        series_b = iv_series * 1.05 + np.random.normal(0, 0.5, len(iv_series)) # Mock correlated series

        rv_task = loop.run_in_executor(None, pairs_engine.analyze_spread, series_a, pd.Series(series_b))

        # Execute
        pcr_res, vol_res, flow_res, rv_score = await asyncio.gather(pcr_task, vol_task, flow_task, rv_task)

        # Augment Sentiment with Gauge Z-Score if pcr_res is missing but we have data
        current_pcr = snapshot.get('put_oi', 0) / snapshot.get('call_oi', 1) if snapshot.get('call_oi', 0) > 0 else 0
        sentiment_z = sentiment_engine.compute_z_score(current_pcr, pcr_series)

        if not pcr_res and abs(sentiment_z) > 1.5:
             pcr_res = {
                "value": round(current_pcr, 2),
                "state": "Overbought" if sentiment_z > 0 else "Oversold",
                "z_score": round(sentiment_z, 2),
                "rationale": f"Sentiment Gauge Z-Score {round(sentiment_z, 2)} indicates extension."
            }

        # 3. Aggregate Results
        # Format RV Result
        rel_val_res = {
            "ratio_pair": "BNF/NIFTY",
            "deviation": f"{round(rv_score, 2)} SD",
            "signal": "Mean Reversion" if abs(rv_score) > 2 else "Neutral"
        }

        # 4. Construct Logic/Rationale
        results = []

        confidence = 50
        triggers = []

        if pcr_res:
            confidence += 20
            triggers.append(f"PCR {pcr_res['state']}")
        if vol_res['regime'] != "Neutral":
            confidence += 15
            triggers.append(f"IV {vol_res['regime']}")
        if flow_res:
            confidence += 25
            triggers.append("Large Order Detected")
        if abs(rv_score) > 2.0:
            confidence += 10
            triggers.append("Pair Divergence")

        story = f"Detected {', '.join(triggers)}. " if triggers else "Market monitoring active. "
        story += "High conviction setup." if confidence > 80 else "Watch for confirmation."

        # 5. OI Quadrant
        # Mocking Pct Change for demonstration (assuming tick data has prev_close or calculating it)
        price_change = 0.5 # Mock +0.5%
        oi_change = 1.2 # Mock +1.2%
        quadrant = get_oi_quadrant(price_change, oi_change)

        # 6. Risk Snapshot (Mocked evaluate_scenario output)
        risk_snapshot = {
            "worst_case": "-18,500 INR",
            "delta": 0.55,
            "theta_decay": "Aggressive",
            "var_95": "2.4%"
        }

        card = {
            "viz_type": "market_scan_trade_card",
            "trade_metadata": {
                "trade_id": f"TC-{snapshot.get('symbol', 'UNK')}",
                "symbol": snapshot.get('symbol', 'UNKNOWN'),
                "confidence_score": min(confidence, 99)
            },
            "strategy_points": {
                "sentiment_pcr": pcr_res or {"value": 0, "state": "Neutral", "z_score": 0},
                "volatility_ivr": vol_res,
                "institutional_footprint": flow_res or {"large_orders": "None"},
                "relative_value": rel_val_res,
                "market_quadrant": quadrant
            },
            "risk_snapshot": risk_snapshot,
            "jules_story": story
        }

        results.append(card)

        # Wrap in the list format expected by the widget API
        return {
            "viz_type": "market_scan_results",
            "data_payload": {
                "metadata": {"total_opportunities": len(results)},
                "results": results
            },
            "rationale": f"Scanner identified {len(results)} opportunities based on multi-point analysis."
        }
