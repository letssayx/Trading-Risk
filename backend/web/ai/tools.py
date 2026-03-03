from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from backend.ingest.nse_models import BhavcopyEQ, BhavcopyFO

def fetch_bhavcopy_data(db: Session, ticker: str) -> Dict[str, Any]:
    """
    Fetches the most recent End of Day data for a given ticker from the local database.
    Used by Qwen to ensure zero hallucinations for the Data Matrix.
    """
    # 1. Fetch latest Equity data
    eq_query = select(BhavcopyEQ).filter(BhavcopyEQ.symbol == ticker).order_by(desc(BhavcopyEQ.trade_date)).limit(1)
    eq_result = db.execute(eq_query).scalar_one_or_none()

    # 2. Fetch latest F&O data (specifically Futures for OI changes)
    fo_query = select(BhavcopyFO).filter(
        BhavcopyFO.ticker_symb == ticker,
        BhavcopyFO.instrument_type == 'FUTSTK'
    ).order_by(desc(BhavcopyFO.trade_date)).limit(1)
    fo_result = db.execute(fo_query).scalar_one_or_none()

    # Build the matrix dictionary
    matrix = {
        "ticker": ticker,
        "equity": {},
        "futures": {}
    }

    if eq_result:
        matrix["equity"] = {
            "trade_date": str(eq_result.trade_date),
            "close_price": eq_result.close_price,
            "prev_close": eq_result.prev_close,
            "total_traded_qty": eq_result.total_traded_qty,
            "deliverable_pct": eq_result.deliverable_pct
        }

    if fo_result:
        matrix["futures"] = {
            "trade_date": str(fo_result.trade_date),
            "close_price": fo_result.close_price,
            "open_interest": fo_result.open_interest,
            "change_in_oi": fo_result.change_in_oi,
            "implied_move_pct": round(abs((fo_result.close_price - eq_result.close_price) / eq_result.close_price) * 100, 2) if eq_result and eq_result.close_price else None
        }

    return matrix
