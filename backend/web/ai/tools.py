import logging
import yfinance as yf
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from backend.ingest.nse_models import BhavcopyEQ, BhavcopyFO

logger = logging.getLogger(__name__)

def search_db_symbol(db: Session, query: str) -> str:
    """
    Searches the SecurityMaster or distinct values in Bhavcopy for a matching NSE symbol.
    """
    try:
        from backend.ingest.nse_models import SecurityMaster, BhavcopyEQ
        from sqlalchemy import func

        query = query.upper().strip()

        # Check SecurityMaster
        sm_query = select(SecurityMaster.ticker_symb).filter(
            func.upper(SecurityMaster.ticker_symb).like(f"%{query}%")
        ).limit(5)

        results = db.execute(sm_query).scalars().all()
        if results:
            return f"Found potential symbols in DB: {', '.join(results)}"

        # Check distinct Bhavcopy symbols
        bc_query = select(BhavcopyEQ.symbol).filter(
            func.upper(BhavcopyEQ.symbol).like(f"%{query}%")
        ).distinct().limit(5)

        bc_results = db.execute(bc_query).scalars().all()
        if bc_results:
            return f"Found potential symbols in historical DB: {', '.join(bc_results)}"

        return f"No symbols found in local DB matching '{query}'"
    except Exception as e:
        logger.error(f"Error querying historical DB for symbol {query}: {e}")
        return f"Error searching database: {e}"

def fetch_detailed_db_data(db: Session, ticker: str, days: int = 30) -> str:
    """
    Fetches detailed recent historical data from the local database for a given ticker.
    Useful to provide Qwen with deeper context on volatility, P/E, and corporate actions.
    """
    try:
        from backend.ingest.nse_models import BhavcopyEQ, FOVolatility, PERatio, CorporateAction
        import json

        ticker = ticker.upper().strip()
        result = {"ticker": ticker, "equity_history": [], "volatility_history": [], "pe_history": [], "recent_corporate_actions": []}

        # Equity History
        eq_query = select(BhavcopyEQ).filter(BhavcopyEQ.symbol == ticker).order_by(desc(BhavcopyEQ.trade_date)).limit(days)
        eq_results = db.execute(eq_query).scalars().all()
        for r in eq_results:
            result["equity_history"].append({
                "date": str(r.trade_date),
                "close": r.close_price,
                "volume": r.total_traded_qty,
                "deliverable_pct": r.deliverable_pct
            })

        # Volatility History
        vol_query = select(FOVolatility).filter(FOVolatility.symbol == ticker).order_by(desc(FOVolatility.trade_date)).limit(days)
        vol_results = db.execute(vol_query).scalars().all()
        for r in vol_results:
            result["volatility_history"].append({
                "date": str(r.trade_date),
                "annualised_vol": r.underlying_annualised_vol,
                "applicable_margin": r.applicable_annualised_vol
            })

        # PE History
        pe_query = select(PERatio).filter(PERatio.symbol == ticker).order_by(desc(PERatio.date)).limit(days)
        pe_results = db.execute(pe_query).scalars().all()
        for r in pe_results:
            result["pe_history"].append({
                "date": str(r.date),
                "pe": r.symbol_pe
            })

        # Corporate Actions
        ca_query = select(CorporateAction).filter(CorporateAction.symbol == ticker).order_by(desc(CorporateAction.date)).limit(5)
        ca_results = db.execute(ca_query).scalars().all()
        for r in ca_results:
            result["recent_corporate_actions"].append({
                "date": str(r.date),
                "purpose": r.purpose,
                "ex_date": str(r.ex_date) if r.ex_date else None
            })

        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error fetching detailed DB data for {ticker}: {e}")
        return f"Error fetching detailed DB data: {e}"

def fetch_yfinance_historical(ticker: str, days: int = 30) -> str:
    """
    Fetches historical price data and potential news/outcomes from Yahoo Finance.
    """
    import json
    try:
        yf_ticker = f"{ticker.upper()}.NS"
        if ticker.upper() in ["NIFTY", "NIFTY 50", "NIFTY50"]:
            yf_ticker = "^NSEI"
        elif ticker.upper() in ["BANKNIFTY", "BANK NIFTY", "NIFTY BANK"]:
            yf_ticker = "^NSEBANK"
        elif ticker.upper() in ["FINNIFTY", "NIFTY FIN SERVICE"]:
            yf_ticker = "NIFTY_FIN_SERVICE.NS"

        stock = yf.Ticker(yf_ticker)
        # Assuming 1mo is ~30 days
        hist = stock.history(period="1mo" if days <= 30 else "3mo")

        if hist.empty:
            return f"No historical data found on YFinance for {yf_ticker}"

        history_data = []
        for date, row in hist.iterrows():
            history_data.append({
                "date": str(date.date()),
                "open": round(float(row['Open']), 2),
                "high": round(float(row['High']), 2),
                "low": round(float(row['Low']), 2),
                "close": round(float(row['Close']), 2),
                "volume": int(row['Volume'])
            })

        result = {
            "ticker": ticker,
            "yfinance_ticker": yf_ticker,
            "history": history_data[-days:]  # Return only requested days
        }

        # Try to get recent news if available
        try:
            news = stock.news
            if news:
                result["recent_news"] = [{"title": n.get("title", ""), "publisher": n.get("publisher", ""), "link": n.get("link", "")} for n in news[:5]]
        except Exception:
            pass

        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error fetching YFinance historical data for {ticker}: {e}"

def search_yfinance_symbol(query: str) -> str:
    """
    Searches Yahoo Finance for a matching ticker symbol.
    """
    import requests
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            quotes = data.get('quotes', [])
            if quotes:
                results = [f"{q.get('symbol')} ({q.get('shortname', '')})" for q in quotes[:5]]
                return f"Found potential symbols on YFinance: {', '.join(results)}"
        return f"No symbols found on YFinance matching '{query}'"
    except Exception as e:
        return f"Error searching YFinance: {e}"

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
