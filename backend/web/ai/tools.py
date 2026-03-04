import logging
import yfinance as yf
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from backend.ingest.nse_models import BhavcopyEQ, BhavcopyFO

logger = logging.getLogger(__name__)

def fetch_bhavcopy_data(db: Session, ticker: str) -> Dict[str, Any]:
    """
    Fetches the most recent End of Day data for a given ticker from the local database.
    If missing, falls back to Yahoo Finance to provide real-world historical context.
    Used by Qwen to ensure zero hallucinations for the Data Matrix.
    """
    # Build the matrix dictionary
    matrix = {
        "ticker": ticker,
        "equity": {},
        "futures": {},
        "yfinance_fallback": False,
        "historical_context": ""
    }

    if ticker == "NONE":
        return matrix

    try:
        # 1. Fetch latest Equity data
        eq_query = select(BhavcopyEQ).filter(BhavcopyEQ.symbol == ticker).order_by(desc(BhavcopyEQ.trade_date)).limit(1)
        eq_result = db.execute(eq_query).scalar_one_or_none()

        if eq_result:
            matrix["equity"] = {
                "trade_date": str(eq_result.trade_date),
                "close_price": eq_result.close_price,
                "prev_close": eq_result.prev_close,
                "total_traded_qty": eq_result.total_traded_qty,
                "deliverable_pct": eq_result.deliverable_pct
            }

        # 2. Fetch latest F&O data (specifically Futures for OI changes)
        fo_query = select(BhavcopyFO).filter(
            BhavcopyFO.ticker_symb == ticker,
            BhavcopyFO.instrument_type == 'FUTSTK'
        ).order_by(desc(BhavcopyFO.trade_date)).limit(1)
        fo_result = db.execute(fo_query).scalar_one_or_none()

        if fo_result:
            matrix["futures"] = {
                "trade_date": str(fo_result.trade_date),
                "close_price": fo_result.close_price,
                "open_interest": fo_result.open_interest,
                "change_in_oi": fo_result.change_in_oi,
                "implied_move_pct": round(abs((fo_result.close_price - eq_result.close_price) / eq_result.close_price) * 100, 2) if eq_result and eq_result.close_price else None
            }
    except Exception as e:
        logger.warning(f"DB lookup failed for {ticker}: {e}")

    # Fallback / Enrich with YFinance if DB data is missing or incomplete
    if not matrix["equity"] or not matrix.get("equity", {}).get("close_price"):
        try:
            # Format ticker for YFinance
            yf_ticker = f"{ticker.upper()}.NS"
            if ticker.upper() in ["NIFTY", "NIFTY 50", "NIFTY50"]:
                yf_ticker = "^NSEI"
            elif ticker.upper() in ["BANKNIFTY", "BANK NIFTY", "NIFTY BANK"]:
                yf_ticker = "^NSEBANK"
            elif ticker.upper() in ["FINNIFTY", "NIFTY FIN SERVICE"]:
                yf_ticker = "NIFTY_FIN_SERVICE.NS"

            stock = yf.Ticker(yf_ticker)

            # Get latest close price
            hist = stock.history(period="1mo")
            if not hist.empty:
                latest_close = float(hist['Close'].iloc[-1])
                latest_vol = int(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns else 0
                prev_close = float(hist['Close'].iloc[-2]) if len(hist) > 1 else latest_close

                high_1m = float(hist['High'].max())
                low_1m = float(hist['Low'].min())

                matrix["equity"] = {
                    "trade_date": str(hist.index[-1].date()),
                    "close_price": round(latest_close, 2),
                    "prev_close": round(prev_close, 2),
                    "total_traded_qty": latest_vol,
                    "deliverable_pct": 0.0
                }

                matrix["yfinance_fallback"] = True
                matrix["historical_context"] = f"YFinance 1-Month Context: High: {round(high_1m, 2)}, Low: {round(low_1m, 2)}"
        except Exception as e:
            logger.warning(f"YFinance fallback failed for {ticker}: {e}")

    return matrix
