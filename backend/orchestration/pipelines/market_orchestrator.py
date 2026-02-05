import asyncio
import pandas as pd
from typing import Dict, Any, List
from backend.analysis.scanners.pcr import scan_pcr_mean_reversion
from backend.analysis.scanners.volatility import calculate_iv_metrics
from backend.analysis.scanners.order_flow import detect_institutional_buying
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
        except Exception:
            # Fallback for empty/malformed history
            hist_df = pd.DataFrame()
            iv_series = pd.Series()
            avg_vol = 1000

        # 2. Run all "Points" in parallel
        # Note: These functions are sync, so we wrap them or run directly if fast.
        # For asyncio.gather, they should be async or wrapped in run_in_executor.
        # Since they are pure CPU/Math, let's run them synchronously here for simplicity,
        # or simulate async.

        loop = asyncio.get_running_loop()

        pcr_task = loop.run_in_executor(None, scan_pcr_mean_reversion, snapshot, hist_df)
        vol_task = loop.run_in_executor(None, calculate_iv_metrics, snapshot.get('iv', 0), iv_series)
        flow_task = loop.run_in_executor(None, detect_institutional_buying, snapshot.get('current_tick', {}), avg_vol)

        pcr_res, vol_res, flow_res = await asyncio.gather(pcr_task, vol_task, flow_task)

        # 3. Aggregate Results (Mocking "Relative Value" which is separate logic)
        rel_val_res = {"ratio_pair": "BNF/NIFTY", "deviation": "+1.8 SD"} # Mocked

        # 4. Construct Logic/Rationale
        results = []

        # Heuristic: If we have at least one strong signal, generate a card.
        # For demo, we force a card if we have ANY data, or default mock.

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

        story = f"Detected {', '.join(triggers)}. " if triggers else "Market monitoring active. "
        story += "High conviction setup." if confidence > 80 else "Watch for confirmation."

        # 5. Risk Snapshot (Mocked evaluate_scenario output)
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
                "relative_value": rel_val_res
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
