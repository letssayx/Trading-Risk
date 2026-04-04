from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, text
from datetime import datetime, timedelta
import pandas as pd
import json

from backend.infrastructure.db import get_db
from backend.ingest.nse_models import DailyDerivativesAnalysis, BhavcopyFO, BhavcopyEQ

router = APIRouter()

@router.get("/api/data/analysis/oi")
def get_aggregated_oi_analysis(db: Session = Depends(get_db)):
    """
    Computes OI vs Price Quadrant Analysis for all F&O symbols on the latest trading day.
    """
    try:
        # 1. Get the latest two trading dates
        from backend.ingest.nse_models import BhavcopyEQ
        dates_query = db.query(BhavcopyEQ.trade_date)\
                  .filter(BhavcopyEQ.series == 'EQ')\
                  .distinct()\
                  .order_by(BhavcopyEQ.trade_date.desc())\
                  .limit(2).all()

        if len(dates_query) < 2:
            return {"data": []}

        curr_date, prev_date = dates_query[0][0], dates_query[1][0]

        if not curr_date or not prev_date:
            return {"data": []}

        # 2. Get data for both dates (Filter out expired contracts to ensure accurate FUT 1 selection)
        query = db.query(
            BhavcopyFO.ticker_symb,
            BhavcopyFO.trade_date,
            BhavcopyFO.close_price,
            BhavcopyFO.open_interest
        ).filter(
            BhavcopyFO.trade_date.in_([curr_date, prev_date]),
            BhavcopyFO.expiry_date >= BhavcopyFO.trade_date,
            BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK', 'FUTIVX', 'FUTIRC'])
        ).order_by(BhavcopyFO.trade_date.asc(), BhavcopyFO.expiry_date.asc()).all()

        # 3. Aggregate OI and get price per symbol per date
        sym_data = {}
        for r in query:
            sym = r.ticker_symb
            dt = r.trade_date
            if sym not in sym_data:
                sym_data[sym] = {curr_date: {"price": None, "oi": 0}, prev_date: {"price": None, "oi": 0}}

            # Strictly use Near Month Futures (FUT 1) close price for analysis
            # Due to `expiry_date >= trade_date` and `order_by(expiry_date.asc())`,
            # the first record is guaranteed to be active FUT 1.
            if sym_data[sym][dt]["price"] is None:
                sym_data[sym][dt]["price"] = float(r.close_price) if r.close_price else 0.0

            # Sum OI across all expiries (FUT 1 + FUT 2 + FUT 3...)
            sym_data[sym][dt]["oi"] += (int(r.open_interest) if r.open_interest else 0)

        # 4. Get historical data for the last 10 days for MWPL-style collapsible rows
        from backend.ingest.nse_models import SymbolMaster
        symbols_list = list(sym_data.keys())

        # Get sector info
        sector_query = db.query(SymbolMaster.symbol, SymbolMaster.sector_index).filter(SymbolMaster.symbol.in_(symbols_list)).all()
        sector_map = {r.symbol: r.sector_index for r in sector_query}

        # Get last 500 dates for extended advanced filters
        from backend.ingest.nse_models import BhavcopyEQ
        all_hist_dates_query = db.query(BhavcopyEQ.trade_date)\
                  .filter(BhavcopyEQ.series == 'EQ')\
                  .distinct()\
                  .order_by(BhavcopyEQ.trade_date.desc())\
                  .limit(500).all()

        all_hist_dates = [d[0] for d in all_hist_dates_query]

        # We need the last 10 days for the table, and the dates exactly 30, 60, 90, 252, 500 days ago for advanced filters
        target_indices = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 29, 59, 89, 251, 499]
        target_dates = []
        for idx in target_indices:
            if idx < len(all_hist_dates):
                target_dates.append(all_hist_dates[idx])

        # Query history for these specific target dates
        hist_query = db.query(
            BhavcopyFO.ticker_symb,
            BhavcopyFO.trade_date,
            BhavcopyFO.close_price,
            BhavcopyFO.open_interest
        ).filter(
            BhavcopyFO.trade_date.in_(target_dates),
            BhavcopyFO.expiry_date >= BhavcopyFO.trade_date,
            BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK', 'FUTIVX', 'FUTIRC'])
        ).order_by(BhavcopyFO.trade_date.asc(), BhavcopyFO.expiry_date.asc()).all()

        hist_data = {}
        for r in hist_query:
            sym = r.ticker_symb
            dt = r.trade_date
            if sym not in hist_data:
                hist_data[sym] = {}
            if dt not in hist_data[sym]:
                hist_data[sym][dt] = {"price": float(r.close_price) if r.close_price else 0.0, "oi": 0}
            hist_data[sym][dt]["oi"] += (int(r.open_interest) if r.open_interest else 0)

        # Fetch options summary data to append to the analysis table
        opt_query = db.query(
            BhavcopyFO.ticker_symb,
            BhavcopyFO.option_type,
            db.func.sum(BhavcopyFO.open_interest).label('total_opt_oi')
        ).filter(
            BhavcopyFO.trade_date == curr_date,
            BhavcopyFO.instrument_type.in_(['OPTIDX', 'OPTSTK', 'STO', 'IDO'])
        ).group_by(BhavcopyFO.ticker_symb, BhavcopyFO.option_type).all()

        opt_data = {}
        for r in opt_query:
            sym = r.ticker_symb
            if sym not in opt_data:
                opt_data[sym] = {'ce_oi': 0, 'pe_oi': 0}
            if r.option_type == 'CE':
                opt_data[sym]['ce_oi'] = int(r.total_opt_oi) if r.total_opt_oi else 0
            elif r.option_type == 'PE':
                opt_data[sym]['pe_oi'] = int(r.total_opt_oi) if r.total_opt_oi else 0

        # Fetch applicable annualized vol (proxy for ATM IV context)
        from backend.ingest.nse_models import FOVolatility
        vol_query = db.query(FOVolatility.symbol, FOVolatility.applicable_annualised_vol).filter(
            FOVolatility.trade_date == curr_date
        ).all()
        vol_data = {r.symbol: float(r.applicable_annualised_vol) * 100 if r.applicable_annualised_vol else None for r in vol_query}

        # 5. Calculate metrics
        results = []
        for sym, dates_dict in sym_data.items():
            prev = dates_dict.get(prev_date, {"price": 0, "oi": 0})
            curr = dates_dict.get(curr_date, {"price": 0, "oi": 0})

            if prev.get("price") is None or prev.get("price") == 0 or prev.get("oi") == 0 or curr.get("price") is None or curr.get("price") == 0 or curr.get("oi") == 0:
                continue

            price_chg = ((curr["price"] - prev["price"]) / prev["price"]) * 100
            oi_chg = ((curr["oi"] - prev["oi"]) / prev["oi"]) * 100

            interp = "Neutral"
            if price_chg > 0 and oi_chg > 0:
                interp = "Long Build Up"
            elif price_chg > 0 and oi_chg < 0:
                interp = "Short Covering"
            elif price_chg < 0 and oi_chg > 0:
                interp = "Short Build Up"
            elif price_chg < 0 and oi_chg < 0:
                interp = "Long Unwinding"

            # Build history array
            hist_arr = []
            if sym in hist_data:
                sorted_hist_dates = sorted(hist_data[sym].keys(), reverse=True)
                for i in range(len(sorted_hist_dates)):
                    dt = sorted_hist_dates[i]
                    curr_h = hist_data[sym][dt]

                    prev_h = None
                    if i + 1 < len(sorted_hist_dates):
                        prev_h = hist_data[sym][sorted_hist_dates[i+1]]

                    h_price_chg = 0
                    h_oi_chg = 0
                    if prev_h and prev_h["price"] > 0 and prev_h["oi"] > 0:
                        h_price_chg = ((curr_h["price"] - prev_h["price"]) / prev_h["price"]) * 100
                        h_oi_chg = ((curr_h["oi"] - prev_h["oi"]) / prev_h["oi"]) * 100

                    # Only append to 10-day history array if it's within the top 10 recent dates
                    if dt in target_dates[:10]:
                        hist_arr.append({
                            "date": str(dt),
                            "price": curr_h["price"],
                            "oi": curr_h["oi"],
                            "price_chg_pct": round(h_price_chg, 2),
                            "oi_chg_pct": round(h_oi_chg, 2)
                        })

            # Calculate multi-timeframe derived metrics (30d, 60d, 90d, 252d, 500d)
            adv_metrics = {
                "oi_chg_30d": 0, "price_chg_30d": 0,
                "oi_chg_60d": 0, "price_chg_60d": 0,
                "oi_chg_90d": 0, "price_chg_90d": 0,
                "oi_chg_252d": 0, "price_chg_252d": 0,
                "oi_chg_500d": 0, "price_chg_500d": 0
            }

            if sym in hist_data and curr_date in hist_data[sym]:
                c_data = hist_data[sym][curr_date]

                timeframes = [(30, 29), (60, 59), (90, 89), (252, 251), (500, 499)]
                for label, idx in timeframes:
                    if idx < len(all_hist_dates):
                        past_dt = all_hist_dates[idx]
                        if past_dt in hist_data[sym]:
                            p_data = hist_data[sym][past_dt]
                            if p_data["price"] > 0:
                                adv_metrics[f"price_chg_{label}d"] = ((c_data["price"] - p_data["price"]) / p_data["price"]) * 100
                            if p_data["oi"] > 0:
                                adv_metrics[f"oi_chg_{label}d"] = ((c_data["oi"] - p_data["oi"]) / p_data["oi"]) * 100

            pcr = 0.0
            total_oi = curr["oi"]
            if sym in opt_data:
                pe = opt_data[sym]['pe_oi']
                ce = opt_data[sym]['ce_oi']
                if ce > 0:
                    pcr = pe / ce
                # Note: true delta weighted OI is intensive for all symbols,
                # so we stick to futures OI + raw options OI for this top-level summary table if needed,
                # or just use futures OI as "OI" and opt_oi + fut_oi as "Total OI"
                total_oi += (pe + ce)

            atm_iv = vol_data.get(sym, None)

            results.append({
                "symbol": sym,
                "sector": sector_map.get(sym, "Unknown"),
                "price": curr["price"],
                "price_chg_pct": round(price_chg, 2),
                "oi": curr["oi"],
                "total_oi": total_oi,
                "oi_chg_pct": round(oi_chg, 2),
                "pcr": round(pcr, 4),
                "atm_iv": round(atm_iv, 2) if atm_iv else None,
                "interpretation": interp,
                "curr_price": curr["price"],
                "curr_oi": curr["oi"],
                "history": hist_arr[:10],
                **{k: round(v, 2) for k, v in adv_metrics.items()}
            })

        return {"date": str(curr_date), "data": results}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))

@router.get("/api/data/analysis/oi/{symbol}")
def get_oi_analysis(symbol: str, db: Session = Depends(get_db)):
    """
    Computes OI vs Price Quadrant Analysis.
    """
    try:
        symbol = symbol.upper()

        # Get active futures for this symbol for the last 60 days
        # We need trade_date, close_price, open_interest
        # Use only Near Month to avoid aggregating all expiries, or sum them. Sum is better for "Total OI".
        # We will use BhavcopyFO for futures.

        query = db.query(
            BhavcopyFO.trade_date,
            BhavcopyFO.close_price,
            BhavcopyFO.open_interest
        ).filter(
            BhavcopyFO.ticker_symb == symbol,
            BhavcopyFO.expiry_date >= BhavcopyFO.trade_date,
            BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK', 'FUTIVX', 'FUTIRC'])
        ).order_by(BhavcopyFO.trade_date.asc(), BhavcopyFO.expiry_date.asc()).all()

        if not query:
            return {"symbol": symbol, "history": []}

        # Aggregate OI and get price (strictly using Near Month Futures / FUT 1 price)
        dates = {}
        for r in query:
            dt = r.trade_date
            if dt not in dates:
                # First encountered row per trade_date is guaranteed to be active FUT 1
                dates[dt] = {"price": float(r.close_price) if r.close_price else 0.0, "oi": 0}
            # Sum OI across all expiries (FUT 1 + FUT 2 + FUT 3...)
            dates[dt]["oi"] += (int(r.open_interest) if r.open_interest else 0)

        sorted_dates = sorted(dates.keys())

        history = []
        for i in range(1, len(sorted_dates)):
            prev = dates[sorted_dates[i-1]]
            curr = dates[sorted_dates[i]]

            p_chg = ((curr["price"] - prev["price"]) / prev["price"] * 100) if prev["price"] > 0 else 0
            oi_chg = ((curr["oi"] - prev["oi"]) / prev["oi"] * 100) if prev["oi"] > 0 else 0

            interpretation = "Indecision"
            if p_chg > 0 and oi_chg > 0: interpretation = "Long Build Up"
            elif p_chg < 0 and oi_chg > 0: interpretation = "Short Build Up"
            elif p_chg > 0 and oi_chg < 0: interpretation = "Short Covering"
            elif p_chg < 0 and oi_chg < 0: interpretation = "Long Unwinding"

            history.append({
                "time": sorted_dates[i].strftime('%Y-%m-%d'),
                "price_chg_pct": p_chg,
                "oi_chg_pct": oi_chg,
                "interpretation": interpretation
            })

        # Return only last 30 days to avoid clutter
        return {"symbol": symbol, "history": history[-30:]}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))

@router.get("/api/data/analysis/rollover")
def get_aggregated_rollover_analysis(db: Session = Depends(get_db)):
    """
    Computes Rollover Analysis metrics for all F&O symbols on the latest trading day.
    """
    try:
        # Get latest date
        from backend.ingest.nse_models import BhavcopyEQ
        latest_date_query = db.query(BhavcopyEQ.trade_date)\
                  .filter(BhavcopyEQ.series == 'EQ')\
                  .distinct()\
                  .order_by(BhavcopyEQ.trade_date.desc())\
                  .first()

        if not latest_date_query:
            return {"data": []}

        latest_date = latest_date_query[0]

        # Get all futures for the latest date
        futs = db.query(
            BhavcopyFO.ticker_symb,
            BhavcopyFO.expiry_date,
            BhavcopyFO.close_price,
            BhavcopyFO.open_interest
        ).filter(
            BhavcopyFO.trade_date == latest_date,
            BhavcopyFO.expiry_date >= latest_date,
            BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK', 'FUTIVX', 'FUTIRC'])
        ).order_by(BhavcopyFO.ticker_symb.asc(), BhavcopyFO.expiry_date.asc()).all()

        # Group by symbol
        sym_futs = {}
        for f in futs:
            sym = f.ticker_symb
            if sym not in sym_futs:
                sym_futs[sym] = []
            sym_futs[sym].append(f)

        results = []
        for sym, s_futs in sym_futs.items():
            if len(s_futs) < 2:
                continue

            total_oi = sum([(int(f.open_interest) if f.open_interest else 0) for f in s_futs])

            near = s_futs[0]
            next_month = s_futs[1]

            near_oi = int(near.open_interest) if near.open_interest else 0

            rollover_pct = 0
            if total_oi > 0:
                rollover_pct = ((total_oi - near_oi) / total_oi) * 100

            near_price = float(near.close_price) if near.close_price else 0
            next_price = float(next_month.close_price) if next_month.close_price else 0

            spread = next_price - near_price
            spread_pct = (spread / near_price) * 100 if near_price > 0 else 0

            results.append({
                "symbol": sym,
                "rollover_pct": round(rollover_pct, 2),
                "rollover_cost": round(spread, 2),
                "rollover_cost_pct": round(spread_pct, 2),
                "near_oi": near_oi,
                "total_oi": total_oi,
                "near_price": near_price,
                "next_price": next_price
            })

        return {"date": str(latest_date), "data": results}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))

@router.get("/api/data/analysis/rollover/{symbol}")
def get_rollover_analysis(symbol: str, db: Session = Depends(get_db)):
    """
    Computes Rollover Analysis metrics.
    """
    try:
        symbol = symbol.upper()

        # Get latest date
        latest_date_query = db.query(BhavcopyFO.trade_date).filter(
            BhavcopyFO.ticker_symb == symbol,
            BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK', 'FUTIVX', 'FUTIRC'])
        ).order_by(BhavcopyFO.trade_date.desc()).first()

        if not latest_date_query:
            return {"error": "No data found"}

        latest_date = latest_date_query[0]

        # Get all futures for the latest date
        futs = db.query(
            BhavcopyFO.expiry_date,
            BhavcopyFO.close_price,
            BhavcopyFO.open_interest
        ).filter(
            BhavcopyFO.trade_date == latest_date,
            BhavcopyFO.ticker_symb == symbol,
            BhavcopyFO.expiry_date >= latest_date,
            BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK', 'FUTIVX', 'FUTIRC'])
        ).order_by(BhavcopyFO.expiry_date.asc()).all()

        if not futs or len(futs) < 2:
            return {"error": "Insufficient futures data to calculate rollover"}

        total_oi = sum([(int(f.open_interest) if f.open_interest else 0) for f in futs])

        near = futs[0]
        next_month = futs[1]

        near_oi = int(near.open_interest) if near.open_interest else 0
        next_oi = int(next_month.open_interest) if next_month.open_interest else 0

        # Calculate rollover
        # True rollover typically is (Next OI + Far OI) / Total OI * 100
        non_near_oi = total_oi - near_oi
        rollover_pct = (non_near_oi / total_oi * 100) if total_oi > 0 else 0.0

        near_price = float(near.close_price) if near.close_price else 0.0
        next_price = float(next_month.close_price) if next_month.close_price else 0.0

        rollover_cost = next_price - near_price
        rollover_cost_pct = (rollover_cost / near_price * 100) if near_price > 0 else 0.0

        return {
            "symbol": symbol,
            "trade_date": latest_date.strftime('%Y-%m-%d'),
            "rollover_pct": round(rollover_pct, 2),
            "rollover_cost": round(rollover_cost, 2),
            "rollover_cost_pct": round(rollover_cost_pct, 2),
            "near_month": {
                "expiry": near.expiry_date.strftime('%Y-%m-%d') if near.expiry_date else "-",
                "price": round(near_price, 2),
                "oi": near_oi
            },
            "next_month": {
                "expiry": next_month.expiry_date.strftime('%Y-%m-%d') if next_month.expiry_date else "-",
                "price": round(next_price, 2),
                "oi": next_oi
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))

@router.get("/api/data/derivatives/mwpl_historical")
def get_mwpl_historical(db: Session = Depends(get_db)):
    """
    Fetches the last 14 trading days of mwpl_array data directly from MWPLClientPosition.
    Also retrieves the EQ close and calculate the Fut1 close.
    """
    from backend.ingest.nse_models import BhavcopyEQ, BhavcopyFO, MWPLClientPosition

    # Find the last 14 unique trading dates in MWPLClientPosition
    dates_query = db.query(MWPLClientPosition.date).distinct().order_by(MWPLClientPosition.date.desc()).limit(14).all()
    if not dates_query:
        return {"data": {}}

    dates = [d[0] for d in dates_query]

    # Query MWPL data for these dates
    mwpl_records = db.query(
        MWPLClientPosition.date,
        MWPLClientPosition.underlying_stock,
        MWPLClientPosition.client_position_num,
        MWPLClientPosition.position_pct
    ).filter(
        MWPLClientPosition.date.in_(dates)
    ).all()

    # Query BhavcopyEQ for these dates
    eq_records = db.query(
        BhavcopyEQ.trade_date,
        BhavcopyEQ.symbol,
        BhavcopyEQ.close_price
    ).filter(
        BhavcopyEQ.trade_date.in_(dates),
        BhavcopyEQ.series.in_(['EQ', 'BE', 'SM', 'BZ'])
    ).all()

    eq_map = {}
    for r in eq_records:
        eq_map[(r.trade_date, r.symbol)] = float(r.close_price) if r.close_price else 0.0

    # Query BhavcopyFO for futures close prices
    fo_records = db.query(
        BhavcopyFO.trade_date,
        BhavcopyFO.ticker_symb,
        BhavcopyFO.close_price,
        BhavcopyFO.expiry_date
    ).filter(
        BhavcopyFO.trade_date.in_(dates),
        BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK', 'FUTIVX', 'FUTIRC'])
    ).all()

    # Group futures by date and symbol, find the nearest expiry for "fut1_close"
    fo_map = {}
    for r in fo_records:
        key = (r.trade_date, r.ticker_symb)
        if key not in fo_map:
            fo_map[key] = []
        fo_map[key].append({"expiry": r.expiry_date, "close": float(r.close_price) if r.close_price else 0.0})

    for key, futs in fo_map.items():
        futs.sort(key=lambda x: x["expiry"])
        fo_map[key] = futs[0]["close"] if futs else 0.0

    result = {}

    # Group MWPL records by date and symbol
    grouped_mwpl = {}
    for r in mwpl_records:
        key = (r.date, r.underlying_stock)
        if key not in grouped_mwpl:
            grouped_mwpl[key] = []
        grouped_mwpl[key].append({"client": r.client_position_num, "pct": float(r.position_pct) if r.position_pct else 0.0})

    for (trade_date, symbol), clients in grouped_mwpl.items():
        if symbol not in result:
            result[symbol] = []

        parsed_arr = []
        mwpl_val = 0.0

        # Sort clients by pct
        clients.sort(key=lambda x: x["pct"], reverse=True)

        for idx, client in enumerate(clients):
            val = client["pct"]
            parsed_arr.append({f"Client {idx+1}": val})
            if val > mwpl_val:
                mwpl_val = val

        if parsed_arr:
            result[symbol].append({
                "date": str(trade_date),
                "eq_close": eq_map.get((trade_date, symbol), 0.0),
                "fut1_close": fo_map.get((trade_date, symbol), 0.0),
                "mwpl": mwpl_val,
                "mwpl_array": parsed_arr
            })

    # Sort dates descending for each symbol
    for sym in result:
        result[sym].sort(key=lambda x: x["date"], reverse=True)

    return {"data": result}

@router.get("/api/data/derivatives/marketwatch")
def get_marketwatch(date: str = None, custom_symbols: str = None, db: Session = Depends(get_db)):
    """
    Fetches Market Watch data for all F&O symbols.
    Returns current EQ price, Corporate Action (Ex-date), and the next 3 unexpired future contracts
    (Fut1, Fut2, Fut3) with their Price, Volume, OI, ATP, DTE, etc.
    """
    from backend.ingest.nse_models import BhavcopyEQ
    from backend.domain.market.models import Bhavcopy
    import datetime

    # Safely query to prevent 500 crashes
    try:
        if date:
            target_date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
            latest_fo_date = target_date
        else:
            # Find the latest date where there is actual futures data (prevents returning empty table if only EQ is loaded so far)
            latest_fo_date_row = db.query(BhavcopyEQ.trade_date)\
                                   .filter(BhavcopyEQ.series == 'EQ')\
                                   .order_by(desc(BhavcopyEQ.trade_date))\
                                   .first()
            if not latest_fo_date_row:
                return {"data": {}}
            latest_fo_date = latest_fo_date_row[0]
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"data": {}}

    # Try to find the closest EQ date at or before the FO date to ensure we have data
    closest_eq_date_row = db.query(BhavcopyEQ.trade_date)\
                            .filter(BhavcopyEQ.trade_date <= latest_fo_date)\
                            .order_by(desc(BhavcopyEQ.trade_date))\
                            .first()
    eq_date_to_use = closest_eq_date_row[0] if closest_eq_date_row else latest_fo_date

    # 1. Fetch all EQ data for the matched EQ date
    eq_records = db.query(
        BhavcopyEQ.symbol,
        BhavcopyEQ.close_price,
        BhavcopyEQ.prev_close,
        BhavcopyEQ.total_traded_qty,
        BhavcopyEQ.avg_price
    ).filter(
        BhavcopyEQ.trade_date == eq_date_to_use,
        BhavcopyEQ.series == 'EQ'
    ).all()

    eq_map = {}
    for r in eq_records:
        cp = float(r.close_price) if r.close_price else 0.0
        pcp = float(r.prev_close) if r.prev_close else 0.0
        pct_change = ((cp - pcp) / pcp * 100) if pcp > 0 else 0.0

        eq_map[r.symbol] = {
            "price": cp,
            "prev_close": pcp,
            "pct_change": pct_change,
            "vol": int(r.total_traded_qty) if r.total_traded_qty else 0,
            "atp": float(r.avg_price) if r.avg_price else 0.0
        }

    # Also add indices from HistoricalIndexData (match to the EQ date)
    # Note: HistoricalIndexData doesn't have prev_close. So let's fetch the previous day's close for % change.
    from backend.ingest.nse_models import HistoricalIndexData
    idx_records = db.query(
        HistoricalIndexData.index_name,
        HistoricalIndexData.close_price,
        HistoricalIndexData.total_traded_qty
    ).filter(
        HistoricalIndexData.trade_date == eq_date_to_use
    ).all()

    prev_idx_date = db.query(HistoricalIndexData.trade_date)\
                        .filter(HistoricalIndexData.trade_date < eq_date_to_use)\
                        .order_by(desc(HistoricalIndexData.trade_date))\
                        .first()

    prev_idx_map = {}
    if prev_idx_date:
        prev_idx_records = db.query(HistoricalIndexData.index_name, HistoricalIndexData.close_price)\
                             .filter(HistoricalIndexData.trade_date == prev_idx_date[0]).all()
        for pr in prev_idx_records:
            sym = pr.index_name.replace('NIFTY 50', 'NIFTY').replace('NIFTY BANK', 'BANKNIFTY').replace('NIFTY FIN SERVICE', 'FINNIFTY').replace('NIFTY MID SELECT', 'MIDCPNIFTY')
            prev_idx_map[sym] = float(pr.close_price) if pr.close_price else 0.0

    for r in idx_records:
        sym = r.index_name.replace('NIFTY 50', 'NIFTY').replace('NIFTY BANK', 'BANKNIFTY').replace('NIFTY FIN SERVICE', 'FINNIFTY').replace('NIFTY MID SELECT', 'MIDCPNIFTY')
        cp = float(r.close_price) if r.close_price else 0.0
        pcp = prev_idx_map.get(sym, 0.0)
        pct_change = ((cp - pcp) / pcp * 100) if pcp > 0 else 0.0

        eq_map[sym] = {
            "price": cp,
            "prev_close": pcp,
            "pct_change": pct_change,
            "vol": int(r.total_traded_qty) if r.total_traded_qty else 0,
            "atp": 0.0
        }

    # 2. Fetch active Futures data
    fut_records = db.query(
        BhavcopyFO.ticker_symb,
        BhavcopyFO.expiry_date,
        BhavcopyFO.close_price,
        BhavcopyFO.total_trading_vol,
        BhavcopyFO.open_interest,
        BhavcopyFO.change_in_oi
    ).filter(
        BhavcopyFO.trade_date == latest_fo_date,
        BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK', 'FUTIVX', 'FUTIRC'])
    ).all()

    # Organize futures by symbol and sort by expiry
    fut_map = {}
    for r in fut_records:
        sym = r.ticker_symb
        if sym not in fut_map:
            fut_map[sym] = []

        dte = (r.expiry_date - latest_fo_date).days if r.expiry_date else 0
        fut_map[sym].append({
            "expiry": str(r.expiry_date),
            "price": float(r.close_price) if r.close_price else 0.0,
            "vol": int(r.total_trading_vol) if r.total_trading_vol else 0,
            "oi": int(r.open_interest) if r.open_interest else 0,
            "chg_oi": int(r.change_in_oi) if r.change_in_oi else 0,
            "dte": dte
        })

    for sym in fut_map:
        fut_map[sym].sort(key=lambda x: x["expiry"])

    # 3. Fetch Corporate Actions (Dividends with upcoming ex-dates)
    # Just look for active dividends within next month
    ca_map = {}
    try:
        from backend.ingest.nse_models import CorporateAction
        import datetime
        next_month = latest_fo_date + datetime.timedelta(days=30)
        ca_records = db.query(
            CorporateAction.symbol,
            CorporateAction.ex_date,
            CorporateAction.purpose
        ).filter(
            CorporateAction.ex_date >= latest_fo_date,
            CorporateAction.ex_date <= next_month,
            CorporateAction.parsed_dividend_amount != None
        ).all()
        for r in ca_records:
            ca_map[r.symbol] = f"{r.ex_date.strftime('%d-%b')} Div"
    except Exception:
        pass

    result = {}
    # 1. Add all F&O symbols
    for sym, futures in fut_map.items():
        if len(futures) == 0:
            continue

        eq_data = eq_map.get(sym, {"price": 0.0, "prev_close": 0.0, "pct_change": 0.0, "vol": 0, "atp": 0.0})

        # Prepare F1, F2, F3
        futs = futures[:3]

        # Calculate BPS and Yield
        for i in range(len(futs)):
            futs[i]["bps"] = 0.0
            futs[i]["yield"] = 0.0

            base_price = eq_data["price"]
            days = futs[i]["dte"]

            if base_price > 0:
                futs[i]["bps"] = ((futs[i]["price"] - base_price) / base_price) * 10000

            if days > 0:
                futs[i]["yield"] = (futs[i]["bps"] / 10000) * (365 / days) * 100

        result[sym] = {
            "eq": {
                "price": eq_data["price"],
                "prev_close": eq_data.get("prev_close", 0.0),
                "pct_change": eq_data.get("pct_change", 0.0),
                "vol": eq_data["vol"],
                "atp": eq_data["atp"],
                "ca": ca_map.get(sym, "")
            },
            "futures": futs
        }

    # 2. Support injecting custom non-F&O cash symbols if requested via query param
    if custom_symbols:
        custom_list = [s.strip().upper() for s in custom_symbols.split(',') if s.strip()]
        for csym in custom_list:
            if csym not in result:
                # We need to query BhavcopyEQ for this specific custom symbol on the eq_date_to_use
                # because the initial eq_map might only contain F&O matching EQ records depending on ingestion
                custom_eq_record = db.query(
                    BhavcopyEQ.close_price,
                    BhavcopyEQ.prev_close,
                    BhavcopyEQ.total_traded_qty,
                    BhavcopyEQ.avg_price
                ).filter(
                    BhavcopyEQ.trade_date == eq_date_to_use,
                    BhavcopyEQ.symbol == csym,
                    BhavcopyEQ.series.in_(['EQ', 'BE']) # Also allow BE for custom
                ).first()

                if custom_eq_record:
                    cp = float(custom_eq_record.close_price) if custom_eq_record.close_price else 0.0
                    pcp = float(custom_eq_record.prev_close) if custom_eq_record.prev_close else 0.0
                    pct_change = ((cp - pcp) / pcp * 100) if pcp > 0 else 0.0

                    result[csym] = {
                        "eq": {
                            "price": cp,
                            "prev_close": pcp,
                            "pct_change": pct_change,
                            "vol": int(custom_eq_record.total_traded_qty) if custom_eq_record.total_traded_qty else 0,
                            "atp": float(custom_eq_record.avg_price) if custom_eq_record.avg_price else 0.0,
                            "ca": ca_map.get(csym, "")
                        },
                        "futures": []  # No futures since it's a cash custom addition
                    }

    return {"data": result, "date": latest_fo_date.strftime('%Y-%m-%d')}
