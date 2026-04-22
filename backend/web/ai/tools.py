import logging
import yfinance as yf
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from typing import Dict, Any

from backend.ingest.nse_models import BhavcopyEQ, BhavcopyFO

logger = logging.getLogger(__name__)

def search_db_symbol(db: Session, query: str) -> str:
    """
    Searches SymbolMaster, SecurityMaster, or distinct values in Bhavcopy for a matching NSE symbol using Python difflib fuzzy matching for very high accuracy on spelling errors.
    """
    import difflib

    try:
        from backend.ingest.nse_models import SymbolMaster, SecurityMaster

        clean_query = query.strip().upper()

        # Pull all possible symbols and names into memory for difflib scoring
        sm_records = db.query(SymbolMaster.symbol, SymbolMaster.company_name).all()
        sec_records = db.query(SecurityMaster.ticker_symb, SecurityMaster.instrument_name).all()

        # Build mapping dict: "SYMBOL" or "COMPANY NAME" -> "SYMBOL (COMPANY NAME)"
        search_corpus = {}

        for sym, comp in sm_records:
            sym_str = str(sym).upper() if sym else ""
            comp_str = str(comp).upper() if comp else ""
            val = f"{sym_str} ({comp_str})"
            if sym_str: search_corpus[sym_str] = val
            if comp_str: search_corpus[comp_str] = val

        for sym, comp in sec_records:
            sym_str = str(sym).upper() if sym else ""
            comp_str = str(comp).upper() if comp else ""
            val = f"{sym_str} ({comp_str})"
            if sym_str and sym_str not in search_corpus: search_corpus[sym_str] = val
            if comp_str and comp_str not in search_corpus: search_corpus[comp_str] = val

        # Find closest matches
        words_to_match = list(search_corpus.keys())
        matches = difflib.get_close_matches(clean_query, words_to_match, n=5, cutoff=0.4)

        if matches:
            unique_hits = list(dict.fromkeys([search_corpus[m] for m in matches]))
            return f"Found potential symbols based on closest spelling: {', '.join(unique_hits)}"

        return f"No symbols found matching '{clean_query}'. Could be a severe spelling error or untracked instrument."
    except Exception as e:
        logger.error(f"Error querying historical DB for symbol {query}: {e}")
        return f"Error searching database: {e}"

def fetch_detailed_db_data(db: Session, ticker: str, days: int = 30) -> str:
    """
    Fetches detailed recent historical data from the local database for a given ticker.
    Useful to provide Qwen with deeper context on volatility, P/E, and corporate actions.
    """
    try:
        from backend.ingest.nse_models import (
            BhavcopyEQ, FOVolatility, PERatio, CorporateAction,
            BulkDeal, BlockDeal, FIIDerivativesStat, MWPLClientPosition, ParticipantOI, SymbolMaster
        )
        import json

        ticker = ticker.upper().strip()
        result = {
            "ticker": ticker,
            "symbol_master_details": {},
            "equity_history": [],
            "volatility_history": [],
            "pe_history": [],
            "recent_corporate_actions": [],
            "bulk_block_deals": [],
            "fii_derivatives_stats": [],
            "mwpl_participant_oi": []
        }

        # Inject Symbol Master context
        sm_result = db.query(SymbolMaster).filter(SymbolMaster.symbol == ticker).first()
        if sm_result:
            result["symbol_master_details"] = {
                "company_name": sm_result.company_name,
                "broad_index": sm_result.broad_index,
                "sector_index": sm_result.sector_index,
                "derivative_liquidity_tier": sm_result.derivative_liquidity_tier,
                "typical_hedge_index": sm_result.typical_hedge_index
            }

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

        # Bulk & Block Deals
        bulk_query = select(BulkDeal).filter(BulkDeal.symbol == ticker).order_by(desc(BulkDeal.date)).limit(5)
        bulk_results = db.execute(bulk_query).scalars().all()
        for r in bulk_results:
            result["bulk_block_deals"].append({
                "date": str(r.date),
                "type": "BULK",
                "buy_sell": r.buy_sell,
                "quantity": r.quantity_traded,
                "price": r.trade_price,
                "client": r.client_name
            })

        block_query = select(BlockDeal).filter(BlockDeal.symbol == ticker).order_by(desc(BlockDeal.date)).limit(5)
        block_results = db.execute(block_query).scalars().all()
        for r in block_results:
            result["bulk_block_deals"].append({
                "date": str(r.date),
                "type": "BLOCK",
                "buy_sell": r.buy_sell,
                "quantity": r.quantity_traded,
                "price": r.trade_price,
                "client": r.client_name
            })

        # FII Derivatives Stats (Market wide usually, not ticker specific, but added for context)
        fii_query = select(FIIDerivativesStat).order_by(desc(FIIDerivativesStat.date)).limit(5)
        fii_results = db.execute(fii_query).scalars().all()
        for r in fii_results:
            result["fii_derivatives_stats"].append({
                "date": str(r.date),
                "instrument": r.instrument_type,
                "buy_amt_cr": r.buy_amt_crores,
                "sell_amt_cr": r.sell_amt_crores,
                "oi_contracts": r.oi_contracts
            })

        # MWPL Client Position
        mwpl_query = select(MWPLClientPosition).filter(MWPLClientPosition.underlying_stock == ticker).order_by(desc(MWPLClientPosition.date)).limit(5)
        mwpl_results = db.execute(mwpl_query).scalars().all()
        for r in mwpl_results:
            result["mwpl_participant_oi"].append({
                "date": str(r.date),
                "type": "MWPL",
                "position_pct": r.position_pct
            })

        # Participant OI (Market wide context)
        poi_query = select(ParticipantOI).filter(ParticipantOI.client_type == 'FII').order_by(desc(ParticipantOI.trade_date)).limit(1)
        poi_results = db.execute(poi_query).scalars().all()
        for r in poi_results:
            result["mwpl_participant_oi"].append({
                "date": str(r.trade_date),
                "type": "Participant_OI_FII",
                "future_index_long": r.future_index_long,
                "future_index_short": r.future_index_short
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
        if ticker.upper() in ["NIFTY", "NIFTY 50", "NIFTY50", "NSEI", "^NSEI"]:
            yf_ticker = "^NSEI"
        elif ticker.upper() in ["BANKNIFTY", "BANK NIFTY", "NIFTY BANK", "NSEBANK", "^NSEBANK"]:
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
        "options": {},
        "vix": {},
        "mto_delivery": {},
        "yfinance_fallback": False,
        "historical_context": ""
    }

    if ticker == "NONE":
        return matrix

    try:
        from backend.ingest.nse_models import MTODelivery

        from backend.ingest.nse_models import SymbolMaster

        # Determine likely instrument type for futures/options
        # Look it up in SymbolMaster to check if it's an index, otherwise fallback to hardcoded list
        is_index = False
        sm_rec = db.query(SymbolMaster).filter(SymbolMaster.symbol == ticker).first()
        if sm_rec and sm_rec.typical_hedge_index:
            # If a symbol is its own typical hedge index, it's highly likely an index
            if sm_rec.symbol == sm_rec.typical_hedge_index:
                is_index = True

        if not is_index:
            is_index = ticker in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "NIFTYNXT50"]

        fut_inst = 'FUTIDX' if is_index else 'FUTSTK'
        opt_inst = 'OPTIDX' if is_index else 'OPTSTK'

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

        # 2. Fetch latest Futures data
        fo_query = select(BhavcopyFO).filter(
            BhavcopyFO.ticker_symb == ticker,
            BhavcopyFO.instrument_type == fut_inst
        ).order_by(desc(BhavcopyFO.trade_date)).limit(1)
        fo_result = db.execute(fo_query).scalar_one_or_none()

        if fo_result:
            matrix["futures"] = {
                "instrument_type": fo_result.instrument_type,
                "trade_date": str(fo_result.trade_date),
                "close_price": fo_result.close_price,
                "open_interest": fo_result.open_interest,
                "change_in_oi": fo_result.change_in_oi,
                "implied_move_pct": round(abs((fo_result.close_price - eq_result.close_price) / eq_result.close_price) * 100, 2) if eq_result and eq_result.close_price else None
            }

        # 3. Fetch latest Options data (closest expiry, highest OI or just ATM)
        # We will grab a summary of recent options
        opt_query = select(BhavcopyFO).filter(
            BhavcopyFO.ticker_symb == ticker,
            BhavcopyFO.instrument_type == opt_inst
        ).order_by(desc(BhavcopyFO.trade_date), desc(BhavcopyFO.open_interest)).limit(2)
        opt_results = db.execute(opt_query).scalars().all()

        if opt_results:
            matrix["options"]["summary"] = []
            for r in opt_results:
                matrix["options"]["summary"].append({
                    "instrument_type": r.instrument_type,
                    "trade_date": str(r.trade_date),
                    "strike_price": r.strike_price,
                    "option_type": r.option_type,
                    "close_price": r.close_price,
                    "open_interest": r.open_interest
                })

        # 4. Fetch VIX Data (Global context)
        vix_query = select(BhavcopyEQ).filter(BhavcopyEQ.symbol == 'India VIX').order_by(desc(BhavcopyEQ.trade_date)).limit(1)
        vix_result = db.execute(vix_query).scalar_one_or_none()
        if vix_result:
            matrix["vix"] = {
                "trade_date": str(vix_result.trade_date),
                "close_price": vix_result.close_price,
                "prev_close": vix_result.prev_close
            }

        # 5. Fetch MTO Delivery specifically
        mto_query = select(MTODelivery).filter(MTODelivery.security_name == ticker).order_by(desc(MTODelivery.trade_date)).limit(1)
        mto_result = db.execute(mto_query).scalar_one_or_none()
        if mto_result:
             matrix["mto_delivery"] = {
                 "trade_date": str(mto_result.trade_date),
                 "deliverable_qty": mto_result.deliverable_qty,
                 "deliverable_pct": mto_result.deliverable_pct
             }

    except Exception as e:
        logger.warning(f"DB lookup failed for {ticker}: {e}")

    # Fallback / Enrich with YFinance if DB data is missing or incomplete
    if not matrix["equity"] or not matrix.get("equity", {}).get("close_price"):
        try:
            # Format ticker for YFinance
            yf_ticker = f"{ticker.upper()}.NS"
            if ticker.upper() in ["NIFTY", "NIFTY 50", "NIFTY50", "NSEI", "^NSEI"]:
                yf_ticker = "^NSEI"
            elif ticker.upper() in ["BANKNIFTY", "BANK NIFTY", "NIFTY BANK", "NSEBANK", "^NSEBANK"]:
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
