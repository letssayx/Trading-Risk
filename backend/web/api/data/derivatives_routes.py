from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, text
from datetime import datetime, timedelta
import pandas as pd
import json

from backend.infrastructure.db import get_db
from backend.ingest.nse_models import DailyDerivativesAnalysis, BhavcopyFO, BhavcopyEQ

router = APIRouter()


@router.post("/api/data/analysis/oi/sync")
def sync_aggregated_oi_analysis(db: Session = Depends(get_db)):
    """
    Checks if a computation is needed (i.e., if BhavcopyFO has newer data than OiAnalysisMetrics)
    and if so, triggers the computation.
    """
    try:
        from backend.ingest.nse_models import BhavcopyFO, OiAnalysisMetrics
        from sqlalchemy import func

        latest_raw_date = db.query(func.max(BhavcopyFO.trade_date)).filter(
            BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK', 'FUTIVX', 'FUTIRC'])
        ).scalar()

        latest_metric_date = db.query(func.max(OiAnalysisMetrics.trade_date)).scalar()

        if latest_raw_date and latest_metric_date and latest_raw_date <= latest_metric_date:
            return {"status": "success", "message": "Data is already up to date.", "computed": False, "latest_date": str(latest_raw_date)}

        # If we reach here, we need to compute
        return compute_aggregated_oi_analysis(db, latest_metric_date=str(latest_metric_date) if latest_metric_date else None)
    except Exception as e:
        import traceback
        return {"status": "error", "message": str(e), "traceback": traceback.format_exc()}


@router.post("/api/data/analysis/oi/compute")
def compute_aggregated_oi_analysis(db: Session = Depends(get_db), latest_metric_date: str = None):
    """
    Computes OI vs Price Quadrant Analysis for all F&O symbols over 32 days and caches it.
    """
    try:
        from backend.ingest.nse_models import BhavcopyFO, HistoricalATMIV
        from sqlalchemy.dialects.postgresql import insert
        from backend.ingest.nse_models import OiAnalysisMetrics
        import datetime
        from sqlalchemy import desc

        latest_metric_date_obj = datetime.datetime.strptime(latest_metric_date, "%Y-%m-%d").date() if latest_metric_date else None

        # First, find all dates in BhavcopyFO
        all_dates_query = db.query(BhavcopyFO.trade_date)\
                  .filter(BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK', 'FUTIVX', 'FUTIRC', 'OPTIDX', 'OPTSTK', 'STO', 'IDO', 'CE', 'PE']))\
                  .distinct()\
                  .order_by(BhavcopyFO.trade_date.desc()).all()

        all_dates = [d[0] for d in all_dates_query]

        if not all_dates:
            return {"status": "error", "message": "No data found in BhavcopyFO."}

        dates_to_compute = []
        if latest_metric_date_obj:
            dates_to_compute = [d for d in all_dates if d > latest_metric_date_obj]
        else:
            dates_to_compute = all_dates[:32] # Initial backfill

        if not dates_to_compute:
            return {"status": "success", "message": "No new dates to compute."}

        # Need enough historical dates to compute 30-day changes for the oldest date to compute
        # The oldest date to compute is dates_to_compute[-1]
        oldest_idx = all_dates.index(dates_to_compute[-1])
        # We need the current dates + 30 days of history beyond the oldest
        max_idx = min(oldest_idx + 31, len(all_dates))
        valid_dates = all_dates[:max_idx]

        if len(valid_dates) < 2:
            return {"status": "error", "message": f"Not enough data in BhavcopyFO. Found {len(valid_dates)} dates."}


        query = db.query(
            BhavcopyFO.ticker_symb,
            BhavcopyFO.trade_date,
            BhavcopyFO.close_price,
            BhavcopyFO.open_interest,
            BhavcopyFO.instrument_type,
            BhavcopyFO.option_type
        ).filter(
            BhavcopyFO.trade_date.in_(valid_dates),
            BhavcopyFO.expiry_date >= BhavcopyFO.trade_date,
            BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK', 'FUTIVX', 'FUTIRC', 'OPTIDX', 'OPTSTK', 'STO', 'IDO', 'CE', 'PE'])
        ).order_by(BhavcopyFO.trade_date.asc(), BhavcopyFO.expiry_date.asc()).all()

        sym_data = {}
        for r in query:
            sym = r.ticker_symb
            dt = r.trade_date
            if sym not in sym_data:
                sym_data[sym] = {d: {"price": None, "fut_oi": 0, "call_oi": 0, "put_oi": 0} for d in valid_dates}

            if r.instrument_type in ['FUTIDX', 'FUTSTK', 'FUTIVX', 'FUTIRC', 'STF', 'IDF'] or (r.instrument_type and r.instrument_type.startswith('FUT')):
                sym_data[sym][dt]["fut_oi"] += int(r.open_interest) if r.open_interest else 0
                if sym_data[sym][dt]["price"] is None:
                    sym_data[sym][dt]["price"] = float(r.close_price) if r.close_price else 0.0
            elif r.instrument_type in ['OPTIDX', 'OPTSTK', 'STO', 'IDO'] or (r.instrument_type and r.instrument_type.startswith('OPT')) or (r.option_type and r.option_type.strip().upper() in ['CE', 'PE']):
                opt_type = r.option_type.strip().upper() if r.option_type else ''
                if opt_type == 'CE':
                    sym_data[sym][dt]["call_oi"] += int(r.open_interest) if r.open_interest else 0
                elif opt_type == 'PE':
                    sym_data[sym][dt]["put_oi"] += int(r.open_interest) if r.open_interest else 0

            if r.instrument_type in ['STF', 'IDF']:
                 if sym_data[sym][dt]["price"] is None:
                     sym_data[sym][dt]["price"] = float(r.close_price) if r.close_price else 0.0

        atm_iv_records = db.query(HistoricalATMIV).filter(HistoricalATMIV.trade_date.in_(valid_dates)).all()
        atm_iv_map = {}
        for r in atm_iv_records:
            if r.symbol not in atm_iv_map:
                atm_iv_map[r.symbol] = {}
            atm_iv_map[r.symbol][r.trade_date] = float(r.atm_iv) if r.atm_iv else 0.0

        insert_data = []

        for sym, date_dict in sym_data.items():
            for i in range(len(valid_dates)):
                curr_date = valid_dates[i]

                # Only insert/update rows for dates we need to compute
                if curr_date not in dates_to_compute:
                    continue

                if i + 1 >= len(valid_dates): break
                prev_date = valid_dates[i+1]

                date_30d_idx = min(i + 30, len(valid_dates) - 1)
                date_30d = valid_dates[date_30d_idx]

                cd = date_dict[curr_date]
                pd = date_dict[prev_date]
                d30 = date_dict[date_30d]

                c_price = cd["price"] or 0
                p_price = pd["price"] or 0

                c_fut_oi = cd["fut_oi"]
                p_fut_oi = pd["fut_oi"]
                d30_fut_oi = d30["fut_oi"]

                c_ce_oi = cd["call_oi"]
                p_ce_oi = pd["call_oi"]
                d30_ce_oi = d30["call_oi"]

                c_pe_oi = cd["put_oi"]
                p_pe_oi = pd["put_oi"]
                d30_pe_oi = d30["put_oi"]

                price_chg_pct = ((c_price - p_price) / p_price * 100) if p_price > 0 else 0

                fut_oi_chg = c_fut_oi - p_fut_oi
                call_oi_chg = c_ce_oi - p_ce_oi
                put_oi_chg = c_pe_oi - p_pe_oi

                fut_oi_chg_pct = (fut_oi_chg / p_fut_oi * 100) if p_fut_oi > 0 else 0
                call_oi_chg_pct = (call_oi_chg / p_ce_oi * 100) if p_ce_oi > 0 else 0
                put_oi_chg_pct = (put_oi_chg / p_pe_oi * 100) if p_pe_oi > 0 else 0

                total_oi_c = c_fut_oi + c_ce_oi + c_pe_oi
                total_oi_p = p_fut_oi + p_ce_oi + p_pe_oi
                oi_chg_pct = ((total_oi_c - total_oi_p) / total_oi_p * 100) if total_oi_p > 0 else 0

                fut_oi_chg_pct_30d = ((c_fut_oi - d30_fut_oi) / d30_fut_oi * 100) if d30_fut_oi > 0 else 0
                call_oi_chg_pct_30d = ((c_ce_oi - d30_ce_oi) / d30_ce_oi * 100) if d30_ce_oi > 0 else 0
                put_oi_chg_pct_30d = ((c_pe_oi - d30_pe_oi) / d30_pe_oi * 100) if d30_pe_oi > 0 else 0

                pcr = (c_pe_oi / c_ce_oi) if c_ce_oi and c_ce_oi > 0 else 0

                atm_iv = atm_iv_map.get(sym, {}).get(curr_date, 0.0)

                insert_data.append({
                    "trade_date": curr_date,
                    "symbol": sym,
                    "price": c_price,
                    "price_chg_pct": price_chg_pct,
                    "fut_oi": c_fut_oi,
                    "call_oi": c_ce_oi,
                    "put_oi": c_pe_oi,
                    "total_oi": total_oi_c,
                    "fut_oi_chg_pct": fut_oi_chg_pct,
                    "call_oi_chg_pct": call_oi_chg_pct,
                    "put_oi_chg_pct": put_oi_chg_pct,
                    "oi_chg_pct": oi_chg_pct,
                    "fut_oi_chg_pct_30d": fut_oi_chg_pct_30d,
                    "call_oi_chg_pct_30d": call_oi_chg_pct_30d,
                    "put_oi_chg_pct_30d": put_oi_chg_pct_30d,
                    "fut_oi_chg": fut_oi_chg,
                    "call_oi_chg": call_oi_chg,
                    "put_oi_chg": put_oi_chg,
                    "pcr": pcr,
                    "atm_iv": atm_iv
                })

        if insert_data:
            if db.bind.dialect.name == 'postgresql':
                stmt = insert(OiAnalysisMetrics).values(insert_data)
                stmt = stmt.on_conflict_do_update(
                    constraint='uq_oi_analysis_metrics_date_symbol',
                    set_={
                        'price': stmt.excluded.price,
                        'price_chg_pct': stmt.excluded.price_chg_pct,
                        'fut_oi': stmt.excluded.fut_oi,
                        'call_oi': stmt.excluded.call_oi,
                        'put_oi': stmt.excluded.put_oi,
                        'total_oi': stmt.excluded.total_oi,
                        'fut_oi_chg_pct': stmt.excluded.fut_oi_chg_pct,
                        'call_oi_chg_pct': stmt.excluded.call_oi_chg_pct,
                        'put_oi_chg_pct': stmt.excluded.put_oi_chg_pct,
                        'oi_chg_pct': stmt.excluded.oi_chg_pct,
                        'fut_oi_chg_pct_30d': stmt.excluded.fut_oi_chg_pct_30d,
                        'call_oi_chg_pct_30d': stmt.excluded.call_oi_chg_pct_30d,
                        'put_oi_chg_pct_30d': stmt.excluded.put_oi_chg_pct_30d,
                        'fut_oi_chg': stmt.excluded.fut_oi_chg,
                        'call_oi_chg': stmt.excluded.call_oi_chg,
                        'put_oi_chg': stmt.excluded.put_oi_chg,
                        'pcr': stmt.excluded.pcr,
                        'atm_iv': stmt.excluded.atm_iv
                    }
                )
                db.execute(stmt)
            else:
                for data in insert_data:
                    existing = db.query(OiAnalysisMetrics).filter(
                        OiAnalysisMetrics.trade_date == data['trade_date'],
                        OiAnalysisMetrics.symbol == data['symbol']
                    ).first()
                    if existing:
                        for k, v in data.items():
                            setattr(existing, k, v)
                    else:
                        db.add(OiAnalysisMetrics(**data))

            db.commit()

        return {"status": "success", "message": f"Upserted {len(insert_data)} OI Analysis records."}
    except Exception as e:
        db.rollback()
        import traceback
        return {"status": "error", "message": str(e), "traceback": traceback.format_exc()}


@router.get("/api/data/analysis/oi")
def get_aggregated_oi_analysis(days: int = Query(30), db: Session = Depends(get_db)):
    """
    Retrieves OI vs Price Quadrant Analysis.
    """
    try:
        from backend.ingest.nse_models import OiAnalysisMetrics, SymbolMaster
        from sqlalchemy import desc

        limit_days = min(days + 1, 60) # Limit to a max to be safe, get days+1 for calculations if needed
        dates_query = db.query(OiAnalysisMetrics.trade_date)\
            .distinct()\
            .order_by(desc(OiAnalysisMetrics.trade_date))\
            .limit(limit_days).all()

        if not dates_query:
            return {"data": []}

        valid_dates = [d[0] for d in dates_query]

        records = db.query(
            OiAnalysisMetrics,
            SymbolMaster.sector_index
        ).outerjoin(
            SymbolMaster,
            OiAnalysisMetrics.symbol == SymbolMaster.symbol
        ).filter(
            OiAnalysisMetrics.trade_date.in_(valid_dates)
        ).order_by(OiAnalysisMetrics.trade_date.desc()).all()

        sym_map = {}
        for analysis, sector in records:
            sym = analysis.symbol
            if sym not in sym_map:
                sym_map[sym] = {"sector": sector or "Unknown", "history": []}

            p_chg = analysis.price_chg_pct or 0
            oi_chg = analysis.oi_chg_pct or 0
            interpretation = "Indecision"
            if p_chg > 0 and oi_chg > 0: interpretation = "Long Build Up"
            elif p_chg < 0 and oi_chg > 0: interpretation = "Short Build Up"
            elif p_chg > 0 and oi_chg < 0: interpretation = "Short Covering"
            elif p_chg < 0 and oi_chg < 0: interpretation = "Long Unwinding"

            sym_map[sym]["history"].append({
                "date": str(analysis.trade_date),
                "price": analysis.price,
                "price_chg_pct": analysis.price_chg_pct,
                "fut_oi": analysis.fut_oi,
                "fut_oi_chg_pct": analysis.fut_oi_chg_pct,
                "call_oi": analysis.call_oi,
                "call_oi_chg_pct": analysis.call_oi_chg_pct,
                "put_oi": analysis.put_oi,
                "put_oi_chg_pct": analysis.put_oi_chg_pct,
                "total_oi": analysis.total_oi,
                "oi_chg_pct": analysis.oi_chg_pct,
                "pcr": analysis.pcr,
                "atm_iv": analysis.atm_iv,
                "interpretation": interpretation,
                "fut_oi_chg_pct_30d": analysis.fut_oi_chg_pct_30d,
                "call_oi_chg_pct_30d": analysis.call_oi_chg_pct_30d,
                "put_oi_chg_pct_30d": analysis.put_oi_chg_pct_30d,
                "fut_oi_chg": analysis.fut_oi_chg,
                "call_oi_chg": analysis.call_oi_chg,
                "put_oi_chg": analysis.put_oi_chg
            })

        output = []
        for sym, d in sym_map.items():
            if not d["history"]: continue
            latest = d["history"][0]
            output.append({
                "symbol": sym,
                "sector": d["sector"],
                "price": latest["price"],
                "price_chg_pct": latest["price_chg_pct"],
                "fut_oi": latest["fut_oi"],
                "fut_oi_chg_pct": latest["fut_oi_chg_pct"],
                "call_oi": latest["call_oi"],
                "call_oi_chg_pct": latest["call_oi_chg_pct"],
                "put_oi": latest["put_oi"],
                "put_oi_chg_pct": latest["put_oi_chg_pct"],
                "total_oi": latest["total_oi"],
                "oi_chg_pct": latest["oi_chg_pct"],
                "pcr": latest["pcr"],
                "atm_iv": latest["atm_iv"],
                "interpretation": latest["interpretation"],
                "fut_oi_chg_pct_30d": latest.get("fut_oi_chg_pct_30d", 0),
                "call_oi_chg_pct_30d": latest.get("call_oi_chg_pct_30d", 0),
                "put_oi_chg_pct_30d": latest.get("put_oi_chg_pct_30d", 0),
                "fut_oi_chg": latest.get("fut_oi_chg", 0),
                "call_oi_chg": latest.get("call_oi_chg", 0),
                "put_oi_chg": latest.get("put_oi_chg", 0),
                "history": d["history"]
            })

        return {"data": output}
    except Exception as e:
        import traceback
        print(f"Error fetching aggregated OI analysis: {e}")
        return {"data": [], "error": str(e)}

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

        from backend.ingest.nse_models import BhavcopyFO

        # Get last 11 dates to calculate 10 days of history + previous day for % changes
        dates_query = db.query(BhavcopyFO.trade_date)\
                  .filter(BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK', 'FUTIVX', 'FUTIRC']))\
                  .distinct()\
                  .order_by(BhavcopyFO.trade_date.desc())\
                  .limit(11).all()

        hist_dates = [d[0] for d in dates_query]

        if not hist_dates:
            return {"data": []}

        # Get futures data for all historical dates
        hist_futs = db.query(
            BhavcopyFO.ticker_symb,
            BhavcopyFO.trade_date,
            BhavcopyFO.expiry_date,
            BhavcopyFO.close_price,
            BhavcopyFO.open_interest
        ).filter(
            BhavcopyFO.trade_date.in_(hist_dates),
            BhavcopyFO.expiry_date >= BhavcopyFO.trade_date,
            BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK', 'FUTIVX', 'FUTIRC'])
        ).order_by(BhavcopyFO.trade_date.asc(), BhavcopyFO.ticker_symb.asc(), BhavcopyFO.expiry_date.asc()).all()

        # Group historical data by symbol and date
        # sym -> date -> [futs ordered by expiry]
        hist_map = {}
        for f in hist_futs:
            sym = f.ticker_symb
            dt = f.trade_date
            if sym not in hist_map:
                hist_map[sym] = {}
            if dt not in hist_map[sym]:
                hist_map[sym][dt] = []
            hist_map[sym][dt].append(f)

        from backend.ingest.nse_models import SymbolMaster
        symbols_list = list(hist_map.keys())
        sector_query = db.query(SymbolMaster.symbol, SymbolMaster.sector_index).filter(SymbolMaster.symbol.in_(symbols_list)).all()
        sector_map = {r.symbol: r.sector_index for r in sector_query}

        results = []
        for sym, date_dict in hist_map.items():
            if latest_date not in date_dict or len(date_dict[latest_date]) < 2:
                continue

            latest_futs = date_dict[latest_date]
            total_oi = sum([(int(f.open_interest) if f.open_interest else 0) for f in latest_futs])
            near = latest_futs[0]
            next_month = latest_futs[1]
            far_month = latest_futs[2] if len(latest_futs) > 2 else None

            near_oi = int(near.open_interest) if near.open_interest else 0
            next_oi = int(next_month.open_interest) if next_month.open_interest else 0
            far_oi = int(far_month.open_interest) if far_month and far_month.open_interest else 0

            rollover_pct = 0
            if total_oi > 0:
                rollover_pct = ((next_oi + far_oi) / total_oi) * 100

            near_price = float(near.close_price) if near.close_price else 0
            next_price = float(next_month.close_price) if next_month.close_price else 0
            spread = next_price - near_price
            spread_pct = (spread / near_price) * 100 if near_price > 0 else 0

            # Calculate historical 10 days
            history_arr = []
            sorted_dates_desc = sorted(date_dict.keys(), reverse=True)

            # Need previous day for today's % changes
            price_chg_pct_today = 0
            oi_chg_pct_today = 0

            for i in range(len(sorted_dates_desc)):
                dt = sorted_dates_desc[i]
                curr_futs = date_dict[dt]
                if not curr_futs: continue

                c_near = curr_futs[0]
                c_next = curr_futs[1] if len(curr_futs) > 1 else None
                c_far = curr_futs[2] if len(curr_futs) > 2 else None

                c_near_oi = int(c_near.open_interest) if c_near.open_interest else 0
                c_next_oi = int(c_next.open_interest) if c_next and c_next.open_interest else 0
                c_far_oi = int(c_far.open_interest) if c_far and c_far.open_interest else 0

                c_price = float(c_near.close_price) if c_near.close_price else 0
                c_next_price = float(c_next.close_price) if c_next and c_next.close_price else 0

                c_total_oi = sum([(int(f.open_interest) if f.open_interest else 0) for f in curr_futs])

                c_rollover_pct = 0
                if c_total_oi > 0:
                    c_rollover_pct = ((c_next_oi + c_far_oi) / c_total_oi) * 100

                c_spread = c_next_price - c_price
                c_spread_pct = (c_spread / c_price) * 100 if c_price > 0 else 0

                p_price_chg = 0
                p_oi_chg = 0

                # Compare to previous day (which is i+1 in descending sort)
                if i + 1 < len(sorted_dates_desc):
                    prev_dt = sorted_dates_desc[i+1]
                    prev_futs = date_dict.get(prev_dt, [])
                    if prev_futs:
                        p_near = prev_futs[0]
                        p_price = float(p_near.close_price) if p_near.close_price else 0
                        p_total_oi = sum([(int(f.open_interest) if f.open_interest else 0) for f in prev_futs])

                        if p_price > 0:
                            p_price_chg = ((c_price - p_price) / p_price) * 100
                        if p_total_oi > 0:
                            p_oi_chg = ((c_total_oi - p_total_oi) / p_total_oi) * 100

                if dt == latest_date:
                    price_chg_pct_today = p_price_chg
                    oi_chg_pct_today = p_oi_chg

                # Add to history if within the top 10 dates (excluding the 11th which is just for diffs)
                if i < 10 and dt in hist_dates[:10]:
                    history_arr.append({
                        "date": str(dt),
                        "rollover_pct": round(c_rollover_pct, 2),
                        "rollover_cost": round(c_spread, 2),
                        "rollover_cost_pct": round(c_spread_pct, 2),
                        "price": c_price,
                        "oi": c_total_oi,
                        "price_chg_pct": round(p_price_chg, 2),
                        "oi_chg_pct": round(p_oi_chg, 2)
                    })

            results.append({
                "symbol": sym,
                "sector": sector_map.get(sym, "Unknown"),
                "rollover_pct": round(rollover_pct, 2),
                "rollover_cost": round(spread, 2),
                "rollover_cost_pct": round(spread_pct, 2),
                "near_oi": near_oi,
                "total_oi": total_oi,
                "price": near_price,
                "near_price": near_price,
                "next_price": next_price,
                "price_chg_pct": round(price_chg_pct_today, 2),
                "oi_chg_pct": round(oi_chg_pct_today, 2),
                "history": history_arr
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

        far_month = futs[2] if len(futs) > 2 else None

        near_oi = int(near.open_interest) if near.open_interest else 0
        next_oi = int(next_month.open_interest) if next_month.open_interest else 0
        far_oi = int(far_month.open_interest) if far_month and far_month.open_interest else 0

        # Calculate rollover
        # True rollover typically is (Next OI + Far OI) / Total OI * 100
        rollover_pct = ((next_oi + far_oi) / total_oi * 100) if total_oi > 0 else 0.0

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
            latest_fo_date_row = db.query(BhavcopyFO.trade_date)\
                                   .order_by(desc(BhavcopyFO.trade_date))\
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


@router.get("/api/data/analysis/rollover/sectors")
def get_sector_rollover_history(db: Session = Depends(get_db)):
    """
    Returns the rollover percentage for the previous 2 expiries for Nifty, BankNifty, and all other sectoral indices.
    """
    from backend.ingest.nse_models import BhavcopyFO, SymbolMaster
    from sqlalchemy import desc
    import datetime

    # Get last 3 expiry dates
    latest_futs = db.query(BhavcopyFO.expiry_date)\
        .filter(BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK']))\
        .distinct()\
        .order_by(desc(BhavcopyFO.expiry_date))\
        .limit(3).all()

    expiries = sorted([e[0] for e in latest_futs])
    if len(expiries) < 2:
        return {"data": []}

    # We need to get the "expiry day" trade data for the previous 2 expiries.
    # Expiry 1 (oldest of the 3), Expiry 2.
    # For a given expiry date, what was the rollover ON that expiry date (or the closest trade date before it)?
    # Since we don't know the exact trade dates, let's just query the data on the exact expiry dates
    # (NSE usually has a trade date on the expiry date).

    target_dates = expiries[:2]  # the previous 2 expiries

    # Actually, rollover is typically calculated on the expiry day of the near month.
    # So we want to find the rollover of the sector constituents on that specific date.

    results = {}

    for dt in target_dates:
        # Find the actual closest trade date on or before the expiry
        closest_trade_date_row = db.query(BhavcopyFO.trade_date)\
            .filter(BhavcopyFO.trade_date <= dt)\
            .order_by(desc(BhavcopyFO.trade_date))\
            .first()

        if not closest_trade_date_row:
            continue

        trade_date = closest_trade_date_row[0]

        # Get all futures on this trade date
        futs = db.query(
            BhavcopyFO.ticker_symb,
            BhavcopyFO.expiry_date,
            BhavcopyFO.open_interest
        ).filter(
            BhavcopyFO.trade_date == trade_date,
            BhavcopyFO.expiry_date >= trade_date,
            BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK'])
        ).order_by(BhavcopyFO.ticker_symb.asc(), BhavcopyFO.expiry_date.asc()).all()

        # Map futures by symbol
        hist_map = {}
        for f in futs:
            sym = f.ticker_symb
            if sym not in hist_map:
                hist_map[sym] = []
            hist_map[sym].append(f)

        # Get sectors
        symbols_list = list(hist_map.keys())
        sector_query = db.query(SymbolMaster.symbol, SymbolMaster.sector_index).filter(SymbolMaster.symbol.in_(symbols_list)).all()
        sector_map = {r.symbol: r.sector_index for r in sector_query}

        sector_totals = {}
        for sym, sym_futs in hist_map.items():
            if len(sym_futs) < 2:
                continue

            sector = sector_map.get(sym, "Unknown")
            if not sector or sector == "Unknown":
                continue

            total_oi = sum([(int(f.open_interest) if f.open_interest else 0) for f in sym_futs])
            near_oi = int(sym_futs[0].open_interest) if sym_futs[0].open_interest else 0

            if sector not in sector_totals:
                sector_totals[sector] = {"total_oi": 0, "near_oi": 0}

            sector_totals[sector]["total_oi"] += total_oi
            sector_totals[sector]["near_oi"] += near_oi

        for sector, totals in sector_totals.items():
            if sector not in results:
                results[sector] = {}

            rollover_pct = 0
            if totals["total_oi"] > 0:
                rollover_pct = ((totals["total_oi"] - totals["near_oi"]) / totals["total_oi"]) * 100

            results[sector][str(dt)] = round(rollover_pct, 2)

    # Format the response
    exp_strs = [str(d) for d in target_dates]
    sectors = sorted(list(results.keys()))

    exp1_data = []
    exp2_data = []

    for sector in sectors:
        vals = results[sector]
        exp1_data.append(vals.get(exp_strs[0], 0))
        if len(exp_strs) > 1:
            exp2_data.append(vals.get(exp_strs[1], 0))

    return {
        "data": {
            "sectors": sectors,
            "exp1_name": exp_strs[0] if exp_strs else "Exp 1",
            "exp2_name": exp_strs[1] if len(exp_strs) > 1 else "Exp 2",
            "exp1_data": exp1_data,
            "exp2_data": exp2_data
        }
    }


@router.get("/api/data/analysis/rollover/history/{symbol}")
def get_stock_rollover_history(symbol: str, db: Session = Depends(get_db)):
    """
    Returns 12-month rollover history for a given stock symbol.
    """
    from backend.ingest.nse_models import BhavcopyFO
    from sqlalchemy import desc

    # Get last 12 expiries
    expiries = db.query(BhavcopyFO.expiry_date)\
        .filter(BhavcopyFO.ticker_symb == symbol)\
        .filter(BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK']))\
        .distinct()\
        .order_by(desc(BhavcopyFO.expiry_date))\
        .limit(12).all()

    exp_dates = sorted([e[0] for e in expiries])
    if not exp_dates:
        return {"data": []}

    results = []

    for dt in exp_dates:
        # Find the trade date closest to (or exactly on) the expiry date
        closest_trade_date_row = db.query(BhavcopyFO.trade_date)\
            .filter(BhavcopyFO.ticker_symb == symbol)\
            .filter(BhavcopyFO.trade_date <= dt)\
            .order_by(desc(BhavcopyFO.trade_date))\
            .first()

        if not closest_trade_date_row:
            continue

        trade_date = closest_trade_date_row[0]

        # Get futures for this symbol on this trade date
        futs = db.query(BhavcopyFO.open_interest, BhavcopyFO.expiry_date)\
            .filter(BhavcopyFO.ticker_symb == symbol)\
            .filter(BhavcopyFO.trade_date == trade_date)\
            .filter(BhavcopyFO.expiry_date >= trade_date)\
            .order_by(BhavcopyFO.expiry_date.asc())\
            .all()

        if len(futs) < 2:
            continue

        total_oi = sum([(int(f.open_interest) if f.open_interest else 0) for f in futs])
        near_oi = int(futs[0].open_interest) if futs[0].open_interest else 0

        rollover_pct = 0
        if total_oi > 0:
            rollover_pct = ((total_oi - near_oi) / total_oi) * 100

        results.append({
            "date": str(dt),
            "rollover_pct": round(rollover_pct, 2)
        })

    return {"data": results}
