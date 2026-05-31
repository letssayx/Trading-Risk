from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.infrastructure.db import get_db
from backend.ingest.nse_models import BhavcopyFO, BhavcopyEQ

router = APIRouter()


@router.post("/api/data/analysis/oi/sync")
def sync_aggregated_oi_analysis(force: str = "false", db: Session = Depends(get_db)):
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

        # Check for corrupted/empty metric records
        if latest_metric_date:
            corrupt_count = db.query(OiAnalysisMetrics).filter(
                OiAnalysisMetrics.trade_date == latest_metric_date,
                OiAnalysisMetrics.fut_oi == 0,
                OiAnalysisMetrics.call_oi == 0,
                OiAnalysisMetrics.put_oi == 0
            ).count()

            # If all rows for the latest date have 0 OI, assume it was corrupted by earlier bugs
            if corrupt_count > 0:
                total_count = db.query(OiAnalysisMetrics).filter(OiAnalysisMetrics.trade_date == latest_metric_date).count()
                if corrupt_count >= total_count * 0.9: # If 90%+ is corrupt
                    # Delete the corrupted date so it forces a recompute for it
                    db.query(OiAnalysisMetrics).filter(OiAnalysisMetrics.trade_date == latest_metric_date).delete()
                    db.commit()
                    # Re-fetch latest metric date
                    latest_metric_date = db.query(func.max(OiAnalysisMetrics.trade_date)).scalar()

        if latest_raw_date and latest_metric_date and latest_raw_date <= latest_metric_date and force.lower() != "true":
            return {"status": "success", "message": "Data is already up to date.", "computed": False, "latest_date": str(latest_raw_date)}

        # If we reach here, we need to compute
        compute_lookback = None if force.lower() == "true" else (str(latest_metric_date) if latest_metric_date else None)
        return compute_aggregated_oi_analysis(db, latest_metric_date=compute_lookback)
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

        # BEFORE COMPUTING METRICS, UPDATE HISTORICAL ATM IV if needed
        try:
            from backend.analysis.historical_iv_calculator import calculate_historical_atm_iv
            from sqlalchemy import text
            unique_syms = db.execute(text("SELECT DISTINCT ticker_symb FROM bhavcopy_fo WHERE trade_date = ANY(:dates)") , {"dates": dates_to_compute}).fetchall()
            for (sym,) in unique_syms:
                calculate_historical_atm_iv(db, sym, lookback_days=len(dates_to_compute) + 10)
        except Exception as e:
            print(f"Failed to pre-compute ATM IV: {e}")

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

            inst_type_up = r.instrument_type.upper().strip() if r.instrument_type else ""
            opt_type_up = r.option_type.upper().strip() if r.option_type else ""

            if inst_type_up in ['FUTIDX', 'FUTSTK', 'FUTIVX', 'FUTIRC', 'STF', 'IDF'] or inst_type_up.startswith('FUT') or (inst_type_up == '' and opt_type_up == ''):
                sym_data[sym][dt]["fut_oi"] += int(r.open_interest) if r.open_interest else 0
                if sym_data[sym][dt]["price"] is None:
                    sym_data[sym][dt]["price"] = float(r.close_price) if r.close_price else 0.0

            if inst_type_up in ['OPTIDX', 'OPTSTK', 'STO', 'IDO'] or inst_type_up.startswith('OPT') or opt_type_up in ['CE', 'PE'] or (inst_type_up == '' and opt_type_up in ['CE', 'PE']):
                if opt_type_up == 'CE':
                    sym_data[sym][dt]["call_oi"] += int(r.open_interest) if r.open_interest else 0
                elif opt_type_up == 'PE':
                    sym_data[sym][dt]["put_oi"] += int(r.open_interest) if r.open_interest else 0

            if inst_type_up in ['STF', 'IDF'] or inst_type_up.startswith('FUT'):
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

                if i + 1 >= len(valid_dates): break

                # Only insert/update rows for dates we need to compute
                if curr_date not in dates_to_compute:
                    continue

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

                fut_oi_chg_pct = (fut_oi_chg / abs(p_fut_oi) * 100) if p_fut_oi != 0 else 0
                call_oi_chg_pct = (call_oi_chg / abs(p_ce_oi) * 100) if p_ce_oi != 0 else 0
                put_oi_chg_pct = (put_oi_chg / abs(p_pe_oi) * 100) if p_pe_oi != 0 else 0

                total_oi_c = c_fut_oi + c_ce_oi + c_pe_oi
                total_oi_p = p_fut_oi + p_ce_oi + p_pe_oi
                oi_chg_pct = ((total_oi_c - total_oi_p) / abs(total_oi_p) * 100) if total_oi_p != 0 else 0

                fut_oi_chg_pct_30d = ((c_fut_oi - d30_fut_oi) / abs(d30_fut_oi) * 100) if d30_fut_oi != 0 else 0
                call_oi_chg_pct_30d = ((c_ce_oi - d30_ce_oi) / abs(d30_ce_oi) * 100) if d30_ce_oi != 0 else 0
                put_oi_chg_pct_30d = ((c_pe_oi - d30_pe_oi) / abs(d30_pe_oi) * 100) if d30_pe_oi != 0 else 0

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
def get_aggregated_oi_analysis(days: int = Query(30), target_date: str = None, db: Session = Depends(get_db)):
    """
    Retrieves OI vs Price Quadrant Analysis.
    """
    try:
        from backend.ingest.nse_models import OiAnalysisMetrics, SymbolMaster
        from sqlalchemy import desc

        limit_days = min(days + 1, 60) # Limit to a max to be safe, get days+1 for calculations if needed

        dq = db.query(OiAnalysisMetrics.trade_date).distinct()
        if target_date:
            dq = dq.filter(OiAnalysisMetrics.trade_date <= target_date)

        dates_query = dq.order_by(desc(OiAnalysisMetrics.trade_date)).limit(limit_days).all()

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
        print(f"Error fetching aggregated OI analysis: {e}")
        return {"data": [], "error": str(e)}


@router.get("/api/data/analysis/oi/{symbol}")
def get_oi_analysis(symbol: str, db: Session = Depends(get_db)):
    """
    Computes OI vs Price Quadrant Analysis.
    """
    try:
        from backend.ingest.nse_models import OiAnalysisMetrics
        symbol = symbol.upper()

        # Fetch from persistent table
        records = db.query(OiAnalysisMetrics).filter(
            OiAnalysisMetrics.symbol == symbol
        ).order_by(OiAnalysisMetrics.trade_date.asc()).all()

        if not records:
            return {"symbol": symbol, "history": []}

        history = []
        for r in records:
            p_chg = float(r.price_chg_pct) if r.price_chg_pct is not None else 0.0
            oi_chg = float(r.fut_oi_chg_pct) if r.fut_oi_chg_pct is not None else 0.0

            interpretation = "Indecision"
            if p_chg > 0 and oi_chg > 0: interpretation = "Long Build Up"
            elif p_chg < 0 and oi_chg > 0: interpretation = "Short Build Up"
            elif p_chg > 0 and oi_chg < 0: interpretation = "Short Covering"
            elif p_chg < 0 and oi_chg < 0: interpretation = "Long Unwinding"

            history.append({
                "time": str(r.trade_date),
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
def get_aggregated_rollover_analysis(days: int = 14, expiry_only: str = "false", db: Session = Depends(get_db)):
    """
    Computes Rollover Analysis metrics for all F&O symbols on the latest trading day directly from RolloverAnalysisMetrics.
    """
    try:
        from backend.ingest.nse_models import RolloverAnalysisMetrics, SymbolMaster, BhavcopyFO
        from sqlalchemy import func, desc

        latest_date = db.query(func.max(RolloverAnalysisMetrics.trade_date)).scalar()
        if not latest_date:
            return {"data": []}

        is_expiry_only = expiry_only.lower() == "true"
        hist_dates = []

        if is_expiry_only:
            target_months = 24
            # Get historical expiry dates
            expiries = db.query(BhavcopyFO.expiry_date).filter(
                BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK'])
            ).distinct().order_by(desc(BhavcopyFO.expiry_date)).all()
            expiry_dates = [e[0] for e in expiries]

            # Fetch the closest trade dates that match the expiries, plus the latest date
            dates_query = db.query(RolloverAnalysisMetrics.trade_date)\
                      .distinct()\
                      .order_by(RolloverAnalysisMetrics.trade_date.desc())\
                      .limit(600).all()
            all_trade_dates = [d[0] for d in dates_query]

            hist_dates.append(latest_date) # Always include latest

            seen_expiries = set()
            for e_date in expiry_dates:
                if len(hist_dates) >= target_months + 1:
                    break
                # Find the closest trade date on or before the expiry date
                for t_date in all_trade_dates:
                    if t_date <= e_date and (e_date - t_date).days < 30:
                        if e_date not in seen_expiries and t_date not in hist_dates:
                            hist_dates.append(t_date)
                            seen_expiries.add(e_date)
                        break
        else:
            # Need last days+1 dates to calculate changes/history
            dates_query = db.query(RolloverAnalysisMetrics.trade_date)\
                      .distinct()\
                      .order_by(RolloverAnalysisMetrics.trade_date.desc())\
                      .limit(days + 1).all()
            hist_dates = [d[0] for d in dates_query]

        records = db.query(RolloverAnalysisMetrics).filter(RolloverAnalysisMetrics.trade_date.in_(hist_dates)).all()

        hist_map = {}
        for r in records:
            if r.symbol not in hist_map:
                hist_map[r.symbol] = {}
            hist_map[r.symbol][r.trade_date] = r

        symbols_list = list(hist_map.keys())
        sector_query = db.query(SymbolMaster.symbol, SymbolMaster.sector_index).filter(SymbolMaster.symbol.in_(symbols_list)).all()
        sector_map = {r.symbol: r.sector_index for r in sector_query}

        results = []
        for sym, date_dict in hist_map.items():
            if latest_date not in date_dict:
                continue

            latest_r = date_dict[latest_date]
            rollover_pct = latest_r.rollover_pct

            near_price = latest_r.fut_close
            spread = latest_r.rollover_cost
            spread_pct = (spread / near_price) * 100 if near_price > 0 else 0

            # Calculate historical 10 days
            history_arr = []
            sorted_dates_desc = sorted(date_dict.keys(), reverse=True)

            price_chg_pct_today = latest_r.price_chg_pct
            oi_chg_pct_today = latest_r.oi_chg_pct

            for i in range(len(sorted_dates_desc)):
                dt = sorted_dates_desc[i]
                curr_r = date_dict[dt]

                c_price = curr_r.fut_close
                c_total_oi = curr_r.total_oi
                c_rollover_pct = curr_r.rollover_pct
                c_spread = curr_r.rollover_cost
                c_spread_pct = curr_r.rollover_cost_pct

                p_price_chg = curr_r.price_chg_pct
                p_oi_chg = curr_r.oi_chg_pct

                target_len = 24 if is_expiry_only else days

                if len(history_arr) < target_len and dt in hist_dates:
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
                "near_oi": latest_r.near_month_oi,
                "total_oi": latest_r.total_oi,
                "price": near_price,
                "near_price": near_price,
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
def get_mwpl_historical(days: int = 14, db: Session = Depends(get_db)):
    """
    Fetches the last N trading days of MWPL data directly from the persistent MwplAnalysisMetrics table.
    """
    from backend.ingest.nse_models import MwplAnalysisMetrics, MWPLClientPosition
    from collections import defaultdict

    dates_query = db.query(MwplAnalysisMetrics.trade_date).distinct().order_by(MwplAnalysisMetrics.trade_date.desc()).limit(days).all()
    if not dates_query:
        return {"data": {}}

    dates = [d[0] for d in dates_query]

    # Need old client arrays to preserve UI parsing logic
    mwpl_raw_records = db.query(MWPLClientPosition).filter(MWPLClientPosition.date.in_(dates)).all()
    grouped_mwpl = defaultdict(list)
    for r in mwpl_raw_records:
        grouped_mwpl[(r.date, r.underlying_stock)].append({
            "client": r.client_position_num,
            "pct": float(r.position_pct) if r.position_pct else 0.0
        })

    records = db.query(MwplAnalysisMetrics).filter(MwplAnalysisMetrics.trade_date.in_(dates)).all()

    result = defaultdict(list)
    for r in records:
        d = r.trade_date
        sym = r.symbol
        clients = grouped_mwpl.get((d, sym), [])
        clients.sort(key=lambda x: x["pct"], reverse=True)

        parsed_arr = []
        for idx, client in enumerate(clients):
            parsed_arr.append({f"Client {idx+1}": client["pct"]})

        result[sym].append({
            "date": d.strftime("%Y-%m-%d"),
            "eq_close": r.price,  # the UI calculates change based on this
            "fut1_close": r.price,
            "mwpl": r.mwpl_pct,
            "mwpl_array": parsed_arr,
            "interpretation": "Neutral",
            "fut_oi_chg_pct": 0.0
        })

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
    except Exception:
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
            "trade_date": str(latest_fo_date),
            "expiry": str(r.expiry_date),
            "price": float(r.close_price) if r.close_price else 0.0,
            "vol": int(r.total_trading_vol) if r.total_trading_vol else 0,
            "oi": int(r.open_interest) if r.open_interest else 0,
            "chg_oi": int(r.change_in_oi) if r.change_in_oi else 0,
            "dte": dte
        })

    for sym in fut_map:
        fut_map[sym].sort(key=lambda x: x["expiry"])

    # 3. Fetch Corporate Actions and Board Meetings
    ca_map = {}
    sector_map = {}
    lot_size_map = {}
    try:
        from backend.ingest.nse_models import CorporateAction, BoardMeeting, SecurityMaster, SymbolMaster
        import datetime
        next_month = latest_fo_date + datetime.timedelta(days=30)

        # Lot Size Mapping
        sec_masters = db.query(SecurityMaster.ticker_symb, SecurityMaster.new_brd_lot_qty).all()
        for sm in sec_masters:
            if sm.new_brd_lot_qty:
                lot_size_map[sm.ticker_symb] = sm.new_brd_lot_qty

        # Sector Mapping from SymbolMaster
        sym_masters = db.query(SymbolMaster.symbol, SymbolMaster.sector_index).all()
        for sym in sym_masters:
            if sym.sector_index:
                sector_map[sym.symbol] = sym.sector_index

        # Comprehensive Special Sits Logic for Market Watch
        import datetime
        from collections import defaultdict

        today_date = latest_fo_date

        # Determine the universe explicitly and convert to python list
        fo_universe = list(fut_map.keys())

        # We need all corporate actions for cycle forecasting
        all_ca_records = db.query(CorporateAction).filter(
            CorporateAction.symbol.in_(fo_universe)
        ).all()

        ca_by_symbol = defaultdict(list)
        for r in all_ca_records:
            if r.parsed_dividend_amount is not None:
                ca_by_symbol[r.symbol.upper()].append({
                    "ex_date": r.ex_date.strftime("%Y-%m-%d") if r.ex_date else None,
                    "ex_date_obj": r.ex_date,
                    "announcement_date_obj": r.date,
                    "broadcast_date": r.broadcast_date if hasattr(r, 'broadcast_date') else None,
                    "dividend_type": r.dividend_type,
                    "purpose": r.purpose,
                    "amount": r.parsed_dividend_amount,
                    "raw_amount": r.parsed_dividend_amount
                })

        # We need all board meetings for merging
        all_bm_records = db.query(BoardMeeting).filter(
            BoardMeeting.symbol.in_(fo_universe)
        ).all()

        bm_by_symbol = defaultdict(list)
        for bm in all_bm_records:
            bm_by_symbol[bm.symbol.upper()].append(bm)

        def get_doy(d): return d.timetuple().tm_yday
        def circ_diff(d1, d2):
            diff = abs(d1 - d2)
            return min(diff, 365 - diff)

        for sym in fo_universe:
            history = ca_by_symbol.get(sym.upper(), [])
            bms = bm_by_symbol.get(sym.upper(), [])

            chained_history = []
            for h in history:
                if h.get('dividend_type') not in ['Bonus', 'Split', 'Demerger']:
                    ca_date = h['ex_date_obj'] or h.get('announcement_date_obj')
                    if ca_date:
                        best_bm = None
                        min_diff = float('inf')
                        for bm in bms:
                            if bm.extracted_dividend_type == h['dividend_type'] or not bm.extracted_dividend_type:
                                if bm.date:
                                    diff = (ca_date - bm.date).days
                                    if -10 <= diff <= 60 and abs(diff) < min_diff:
                                        if h.get('amount') and bm.extracted_dividend_amount:
                                            if float(h['amount']) != float(bm.extracted_dividend_amount):
                                                continue
                                        min_diff = abs(diff)
                                        best_bm = bm
                        if best_bm:
                            h['broadcast_date'] = best_bm.broadcast_date
                            h['announcement_date_obj'] = best_bm.meeting_date or best_bm.broadcast_date or best_bm.date
                            if not h.get('amount') and best_bm.extracted_dividend_amount:
                                h['amount'] = best_bm.extracted_dividend_amount
                            try:
                                bms.remove(best_bm)
                            except ValueError:
                                pass
                chained_history.append(h)

            for bm in bms:
                if bm.date and bm.date < today_date - datetime.timedelta(days=60):
                    continue
                amt = bm.extracted_dividend_amount
                purpose_lower = (bm.purpose or '').lower()

                is_valid_standalone = False
                if amt is not None:
                    is_valid_standalone = True
                elif bm.date and bm.date >= today_date:
                    is_valid_standalone = True
                elif 'dividend' in purpose_lower and not any(x in purpose_lower for x in ['financial results', 'agm', 'annual general meeting', 'postponed']):
                    is_valid_standalone = True

                if is_valid_standalone:
                    chained_history.append({
                        "ex_date": 'Record date not yet declared',
                        "ex_date_obj": None,
                        "broadcast_date": bm.broadcast_date,
                        "announcement_date_obj": bm.meeting_date or bm.broadcast_date or bm.date,
                        "dividend_type": bm.extracted_dividend_type or 'Interim',
                        "purpose": bm.purpose or "Dividend Declared in Board Meeting",
                        "amount": amt,
                        "raw_amount": amt
                    })

            def get_sort_key_asc(x):
                if x.get('ex_date_obj'): return x['ex_date_obj']
                ann_dt = x.get('announcement_date_obj')
                if ann_dt is None: return datetime.date.min
                if hasattr(ann_dt, 'date'): return ann_dt.date()
                return ann_dt

            history_asc = sorted(chained_history, key=get_sort_key_asc)

            events_str = []

            # Get a set of known amounts that have actual future ex-dates so we don't output "Awaited" for them
            known_ex_dates = set()
            for h in history_asc:
                ex_date_obj = h.get('ex_date_obj')
                if ex_date_obj and ex_date_obj >= today_date and h.get('amount') is not None:
                    try:
                        known_ex_dates.add(float(h['amount']))
                    except ValueError:
                        pass

            # ACTIVE EVENTS FROM HISTORY (Announced but ex-date in future, or awaited)
            for h in history_asc:
                ex_date_obj = h.get('ex_date_obj')
                amt = h.get('amount')
                if ex_date_obj and ex_date_obj >= today_date:
                    if amt is not None:
                        events_str.append(f"div - {amt}, Ex-date {ex_date_obj.strftime('%d-%m-%Y')}")
                elif not ex_date_obj or h.get('ex_date') == 'Record date not yet declared':
                    if amt is not None:
                        # ONLY append Awaited if we don't already have a concrete ex-date for this amount
                        try:
                            if float(amt) not in known_ex_dates:
                                events_str.append(f"Div: Rs {amt}, Ex-Date Awaited")
                        except ValueError:
                            events_str.append(f"Div: Rs {amt}, Ex-Date Awaited")

            # UPCOMING BOARD MEETINGS (That haven't declared an amount yet)
            upcoming_bms = [bm for bm in bms if (bm.meeting_date and bm.meeting_date >= today_date) or (not bm.meeting_date and bm.date and bm.date >= today_date)]
            # Sort upcoming BMs by date
            upcoming_bms.sort(key=lambda x: x.meeting_date or x.date)
            for bm in upcoming_bms:
                if not bm.extracted_dividend_amount:
                    d = bm.meeting_date or bm.date
                    events_str.append(f"Boardmeeting, date-{d.strftime('%d-%m-%Y')}")

            # FORECASTING FOR FUTURE DIVIDENDS
            final_cluster = []
            interim_clusters = []
            five_years_ago = today_date - datetime.timedelta(days=365*5)
            recent_hist = [h for h in history_asc if h.get('ex_date_obj') and h['ex_date_obj'] >= five_years_ago]

            for h in recent_hist:
                if 'special' in (h.get('purpose') or '').lower() or h.get('dividend_type') == 'Special':
                    continue
                if h.get('dividend_type') == 'Final':
                    final_cluster.append(h)
                else:
                    doy = get_doy(h['ex_date_obj'])
                    placed = False
                    for c in interim_clusters:
                        mean_doy = sum(get_doy(x['ex_date_obj']) for x in c) / len(c)
                        if circ_diff(doy, mean_doy) <= 90:
                            if not any(x['ex_date_obj'].year == h['ex_date_obj'].year for x in c):
                                c.append(h)
                                placed = True
                                break
                    if not placed:
                        interim_clusters.append([h])

            clusters = [final_cluster] + interim_clusters if final_cluster else interim_clusters

            forecasts = []
            for c in clusters:
                if not c: continue
                most_recent = c[-1]
                mr_date = most_recent['ex_date_obj']

                # To handle testing/mock futuristic dates gracefully:
                # We only kill the cycle if the most recent dividend was more than 2 years BEFORE the LATEST historical dividend recorded overall,
                # rather than relative to the FO trade_date, which might be artificially pushed to 2026.
                max_hist_date = max((h.get('ex_date_obj') for h in history_asc if h.get('ex_date_obj')), default=today_date)

                # Use min() so if max_hist_date is way in the past (e.g. 2024) but today_date is 2026, we don't kill valid 2024 cycles
                anchor_year = min(today_date.year, max_hist_date.year)

                if mr_date.year < anchor_year - 1:
                    continue

                if mr_date < today_date:
                    next_year = mr_date.year + 1
                    try:
                        next_date = datetime.date(next_year, mr_date.month, mr_date.day)
                    except ValueError:
                        next_date = datetime.date(next_year, mr_date.month, mr_date.day - 1)
                    while next_date < today_date - datetime.timedelta(days=15):
                        next_year += 1
                        try:
                            next_date = datetime.date(next_year, mr_date.month, mr_date.day)
                        except ValueError:
                            next_date = datetime.date(next_year, mr_date.month, mr_date.day - 1)

                    # Check if it falls within the next 45 days (typical FO cycle scope)
                    if next_date <= today_date + datetime.timedelta(days=45):
                        # Calculate expected amount based on last amount (no growth calc needed for string UI)
                        exp_amt = most_recent['amount']
                        forecasts.append(f"Expected: {next_date.strftime('%d-%m-%Y')} (Rs {exp_amt})")

            # deduplicate matching events if multiple cycles hit or logic overlaps
            all_events = []
            seen = set()
            for e in events_str + forecasts:
                if e not in seen:
                    all_events.append(e)
                    seen.add(e)

            if all_events:
                ca_map[sym.upper()] = " | ".join(all_events)
    except Exception as e:
        import traceback
        traceback.print_exc()
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

            # Removed conversion to lot size, leaving volume in contracts.

        # CA Map might have uppercase, lowercase or symbol variants. Ensure upper matching
        # Also fut_map keys are straight from ticker_symb, so make sure sym.upper()
        ca_string = ca_map.get(sym.upper(), ca_map.get(sym, ""))

        result[sym] = {
            "eq": {
                "price": eq_data["price"],
                "prev_close": eq_data.get("prev_close", 0.0),
                "pct_change": eq_data.get("pct_change", 0.0),
                "vol": eq_data["vol"],
                "atp": eq_data["atp"],
                "sector": sector_map.get(sym, "-"),
                "ca": ca_string
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
                            "sector": sector_map.get(csym, "-"),
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
def get_stock_rollover_history(symbol: str, expiry_only: str = "false", db: Session = Depends(get_db)):
    """
    Returns rollover history for a given stock symbol directly from RolloverAnalysisMetrics.
    If expiry_only is 'true', it only returns the data for the final expiry days (Month-on-Month trend).
    """
    from backend.ingest.nse_models import RolloverAnalysisMetrics, BhavcopyFO
    from sqlalchemy import desc

    symbol = symbol.upper()
    is_expiry_only = expiry_only.lower() == "true"

    if is_expiry_only:
        # Get historical expiry dates
        expiries = db.query(BhavcopyFO.expiry_date).filter(
            BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK'])
        ).distinct().order_by(desc(BhavcopyFO.expiry_date)).all()
        expiry_dates = [e[0] for e in expiries]

        # Fetch records specifically on or just before these expiry dates for the symbol
        # For simplicity, if we query the last 300 days of rollover metrics, we can just filter in memory
        records = db.query(RolloverAnalysisMetrics).filter(
            RolloverAnalysisMetrics.symbol == symbol
        ).order_by(desc(RolloverAnalysisMetrics.trade_date)).limit(600).all()

        results = []
        seen_expiries = set()

        # We need exactly 24 expiry points
        for e_date in expiry_dates:
            if len(results) >= 24:
                break

            # Find the closest trade date on or before the expiry date
            closest_record = None
            for r in records:
                if r.trade_date <= e_date:
                    # Also make sure this record actually belongs to this expiry cycle
                    # by ensuring the trade_date is within ~30 days of the expiry
                    if (e_date - r.trade_date).days < 30:
                        closest_record = r
                    break

            if closest_record and e_date not in seen_expiries:
                seen_expiries.add(e_date)
                results.append({
                    "date": str(e_date),  # Show the expiry date as the label
                    "rollover_pct": round(closest_record.rollover_pct, 2),
                    "rollover_cost": round(closest_record.rollover_cost, 2),
                    "rollover_cost_pct": round(closest_record.rollover_cost_pct, 2),
                    "price": float(closest_record.fut_close) if closest_record.fut_close else None
                })
    else:
        # Standard daily progression (last 12 trading days)
        records = db.query(RolloverAnalysisMetrics).filter(
            RolloverAnalysisMetrics.symbol == symbol
        ).order_by(desc(RolloverAnalysisMetrics.trade_date)).limit(12).all()

        results = []
        for r in records:
            results.append({
                "date": str(r.trade_date),
                "rollover_pct": round(r.rollover_pct, 2),
                "rollover_cost": round(r.rollover_cost, 2),
                "rollover_cost_pct": round(r.rollover_cost_pct, 2),
                "price": float(r.fut_close) if r.fut_close else None
            })

    # Maintain ascending chronological order as original UI expects
    results.reverse()

    return {"data": results}

@router.post("/api/data/analysis/mwpl/sync")
def sync_mwpl_analysis(force: str = "false", db: Session = Depends(get_db)):
    try:
        from backend.ingest.nse_models import MWPLClientPosition, MwplAnalysisMetrics
        from sqlalchemy import func

        latest_raw_date = db.query(func.max(MWPLClientPosition.date)).scalar()
        latest_metric_date = db.query(func.max(MwplAnalysisMetrics.trade_date)).scalar()

        if latest_raw_date and latest_metric_date and latest_raw_date <= latest_metric_date and force.lower() != "true":
            return {"status": "success", "message": "Data is already up to date.", "computed": False, "latest_date": str(latest_raw_date)}

        compute_lookback = None if force.lower() == "true" else (str(latest_metric_date) if latest_metric_date else None)
        return compute_mwpl_analysis(db, latest_metric_date=compute_lookback)
    except Exception as e:
        import traceback
        return {"status": "error", "message": str(e), "traceback": traceback.format_exc()}

@router.post("/api/data/analysis/mwpl/compute")
def compute_mwpl_analysis(db: Session = Depends(get_db), latest_metric_date: str = None):
    try:
        from backend.ingest.nse_models import MWPLClientPosition, BhavcopyEQ, BhavcopyFO, MwplAnalysisMetrics
        from sqlalchemy.dialects.postgresql import insert
        import datetime

        latest_metric_date_obj = datetime.datetime.strptime(latest_metric_date, "%Y-%m-%d").date() if latest_metric_date else None

        all_dates_query = db.query(MWPLClientPosition.date).distinct().order_by(MWPLClientPosition.date.desc()).all()
        all_dates = [d[0] for d in all_dates_query]

        if not all_dates:
            return {"status": "error", "message": "No data found."}

        dates_to_compute = []
        if latest_metric_date_obj:
            dates_to_compute = [d for d in all_dates if d > latest_metric_date_obj]
        else:
            dates_to_compute = all_dates[:500]

        if not dates_to_compute:
            return {"status": "success", "message": "No new dates to compute.", "computed": False}

        from sqlalchemy import func

        # MWPLClientPosition contains multiple records per symbol/date (one for each client)
        # We need the max position_pct, or sum, depending on how MWPL is structured.
        # But wait, MWPL_client_position_pct usually means the aggregated limit is what we want.
        # Wait, the frontend code sorts by 'pct' and creates an array of clients.
        # However, for `MwplAnalysisMetrics`, it just needs the aggregate `mwpl_pct`.
        # Usually, NSE MWPL csv has an aggregated "MWPL %" column, but if it only has clients, we can take the sum.
        mwpl_records = db.query(
            MWPLClientPosition.date,
            MWPLClientPosition.underlying_stock,
            func.sum(MWPLClientPosition.position_pct).label('position_pct')
        ).filter(
            MWPLClientPosition.date.in_(dates_to_compute)
        ).group_by(MWPLClientPosition.date, MWPLClientPosition.underlying_stock).all()

        eq_records = db.query(
            BhavcopyEQ.trade_date, BhavcopyEQ.symbol, BhavcopyEQ.close_price
        ).filter(BhavcopyEQ.trade_date.in_(dates_to_compute), BhavcopyEQ.series.in_(['EQ', 'BE', 'SM', 'BZ'])).all()
        eq_map = {(r.trade_date, r.symbol): float(r.close_price) if r.close_price else 0.0 for r in eq_records}

        fo_records = db.query(
            BhavcopyFO.trade_date, BhavcopyFO.ticker_symb, BhavcopyFO.close_price, BhavcopyFO.expiry_date, BhavcopyFO.open_interest
        ).filter(BhavcopyFO.trade_date.in_(dates_to_compute), BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK'])).all()

        fo_map = {}
        for r in fo_records:
            key = (r.trade_date, r.ticker_symb)
            if key not in fo_map:
                fo_map[key] = []
            fo_map[key].append({"expiry": r.expiry_date, "close": float(r.close_price) if r.close_price else 0.0, "oi": float(r.open_interest) if r.open_interest else 0.0})

        for key, futs in fo_map.items():
            futs.sort(key=lambda x: x["expiry"])
            fo_map[key] = {"close": futs[0]["close"], "oi": sum([x["oi"] for x in futs])}

        # Need previous date OI & Price for Chg %
        prev_dates = list(set([d for d in all_dates if d not in dates_to_compute] + dates_to_compute))
        prev_dates.sort()

        # Fast way is to just fetch the last 500 days of required stuff
        prev_fo_records = db.query(
            BhavcopyFO.trade_date, BhavcopyFO.ticker_symb, BhavcopyFO.close_price, BhavcopyFO.expiry_date, BhavcopyFO.open_interest
        ).filter(BhavcopyFO.trade_date.in_(prev_dates), BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK'])).all()

        prev_fo_map = {}
        for r in prev_fo_records:
            key = (r.trade_date, r.ticker_symb)
            if key not in prev_fo_map:
                prev_fo_map[key] = []
            prev_fo_map[key].append({"expiry": r.expiry_date, "close": float(r.close_price) if r.close_price else 0.0, "oi": float(r.open_interest) if r.open_interest else 0.0})

        aggregated_prev_fo = {}
        for key, futs in prev_fo_map.items():
            futs.sort(key=lambda x: x["expiry"])
            aggregated_prev_fo[key] = {"close": futs[0]["close"], "oi": sum([x["oi"] for x in futs])}

        metrics = []
        for r in mwpl_records:
            d = r.date
            sym = r.underlying_stock
            mwpl_pct = float(r.position_pct) if r.position_pct else 0.0

            price = eq_map.get((d, sym), fo_map.get((d, sym), {}).get("close", 0.0))
            oi = fo_map.get((d, sym), {}).get("oi", 0.0)

            # Find previous date
            idx = prev_dates.index(d)
            prev_d = prev_dates[idx-1] if idx > 0 else None

            price_chg_pct = 0.0
            oi_chg_pct = 0.0
            if prev_d:
                prev_price = eq_map.get((prev_d, sym), aggregated_prev_fo.get((prev_d, sym), {}).get("close", price))
                prev_oi = aggregated_prev_fo.get((prev_d, sym), {}).get("oi", oi)
                if prev_price and prev_price > 0:
                    price_chg_pct = ((price - prev_price) / prev_price) * 100
                if prev_oi and prev_oi > 0:
                    oi_chg_pct = ((oi - prev_oi) / abs(prev_oi)) * 100

            interp = "Neutral"
            if price_chg_pct > 0 and oi_chg_pct > 0: interp = "Long Build Up"
            elif price_chg_pct < 0 and oi_chg_pct > 0: interp = "Short Build Up"
            elif price_chg_pct > 0 and oi_chg_pct < 0: interp = "Short Covering"
            elif price_chg_pct < 0 and oi_chg_pct < 0: interp = "Long Unwinding"

            prev_mwpl = 0.0
            if prev_d:
                # We need prev mwpl pct to calculate mwpl_chg_pct. It is easier to fetch it from the records since we are looping or grouping.
                # For this PR, since the table only uses 'mwpl_pct' in the UI directly (it doesn't show mwpl_chg_pct in the existing UI table), we will set it to 0.0.
                pass

            metrics.append({
                "trade_date": d,
                "symbol": sym,
                "mwpl_pct": mwpl_pct,
                "mwpl_chg_pct": 0.0,
                "open_interest": oi,
                "limit_for_next_day": 0,
                "price": price,
                "price_chg_pct": price_chg_pct
            })

        if metrics:
            stmt = insert(MwplAnalysisMetrics).values(metrics)
            stmt = stmt.on_conflict_do_update(
                constraint='uq_mwpl_analysis_metrics_date_symbol',
                set_={
                    'mwpl_pct': stmt.excluded.mwpl_pct,
                    'mwpl_chg_pct': stmt.excluded.mwpl_chg_pct,
                    'open_interest': stmt.excluded.open_interest,
                    'limit_for_next_day': stmt.excluded.limit_for_next_day,
                    'price': stmt.excluded.price,
                    'price_chg_pct': stmt.excluded.price_chg_pct
                }
            )
            db.execute(stmt)
            db.commit()

        return {"status": "success", "message": f"Computed {len(metrics)} records for {len(dates_to_compute)} dates.", "computed": True}
    except Exception as e:
        import traceback
        return {"status": "error", "message": str(e), "traceback": traceback.format_exc()}

@router.post("/api/data/analysis/rollover/sync")
def sync_rollover_analysis(force: str = "false", db: Session = Depends(get_db)):
    try:
        from backend.ingest.nse_models import BhavcopyFO, RolloverAnalysisMetrics
        from sqlalchemy import func

        latest_raw_date = db.query(func.max(BhavcopyFO.trade_date)).filter(BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK'])).scalar()
        latest_metric_date = db.query(func.max(RolloverAnalysisMetrics.trade_date)).scalar()

        if latest_raw_date and latest_metric_date and latest_raw_date <= latest_metric_date and force.lower() != "true":
            return {"status": "success", "message": "Data is already up to date.", "computed": False, "latest_date": str(latest_raw_date)}

        compute_lookback = None if force.lower() == "true" else (str(latest_metric_date) if latest_metric_date else None)
        return compute_rollover_analysis(db, latest_metric_date=compute_lookback)
    except Exception as e:
        import traceback
        return {"status": "error", "message": str(e), "traceback": traceback.format_exc()}

@router.post("/api/data/analysis/rollover/compute")
def compute_rollover_analysis(db: Session = Depends(get_db), latest_metric_date: str = None):
    try:
        from backend.ingest.nse_models import BhavcopyFO, RolloverAnalysisMetrics
        from sqlalchemy.dialects.postgresql import insert
        import datetime

        latest_metric_date_obj = datetime.datetime.strptime(latest_metric_date, "%Y-%m-%d").date() if latest_metric_date else None

        all_dates_query = db.query(BhavcopyFO.trade_date).filter(BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK'])).distinct().order_by(BhavcopyFO.trade_date.desc()).all()
        all_dates = [d[0] for d in all_dates_query]

        if not all_dates:
            return {"status": "error", "message": "No data found."}

        dates_to_compute = []
        if latest_metric_date_obj:
            dates_to_compute = [d for d in all_dates if d > latest_metric_date_obj]
        else:
            dates_to_compute = all_dates[:500]

        if not dates_to_compute:
            return {"status": "success", "message": "No new dates to compute.", "computed": False}

        fo_records = db.query(
            BhavcopyFO.trade_date, BhavcopyFO.ticker_symb, BhavcopyFO.close_price, BhavcopyFO.expiry_date, BhavcopyFO.open_interest
        ).filter(BhavcopyFO.trade_date.in_(dates_to_compute), BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK'])).all()

        fo_map = {}
        for r in fo_records:
            d = r.trade_date
            sym = r.ticker_symb
            key = (d, sym)
            if key not in fo_map:
                fo_map[key] = []
            fo_map[key].append({"expiry": r.expiry_date, "close": float(r.close_price) if r.close_price else 0.0, "oi": float(r.open_interest) if r.open_interest else 0.0})

        # Need previous date OI & Price for Chg %
        prev_dates = list(set([d for d in all_dates if d not in dates_to_compute] + dates_to_compute))
        prev_dates.sort()

        # Fast way is to just fetch the last 500 days of required stuff
        prev_fo_records = db.query(
            BhavcopyFO.trade_date, BhavcopyFO.ticker_symb, BhavcopyFO.close_price, BhavcopyFO.expiry_date, BhavcopyFO.open_interest
        ).filter(BhavcopyFO.trade_date.in_(prev_dates), BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK'])).all()

        prev_fo_map = {}
        for r in prev_fo_records:
            key = (r.trade_date, r.ticker_symb)
            if key not in prev_fo_map:
                prev_fo_map[key] = []
            prev_fo_map[key].append({"expiry": r.expiry_date, "close": float(r.close_price) if r.close_price else 0.0, "oi": float(r.open_interest) if r.open_interest else 0.0})

        aggregated_prev_fo = {}
        for key, futs in prev_fo_map.items():
            futs.sort(key=lambda x: x["expiry"])
            aggregated_prev_fo[key] = {"close": futs[0]["close"], "oi": sum([x["oi"] for x in futs])}

        metrics = []
        for (d, sym), futs in fo_map.items():
            futs.sort(key=lambda x: x["expiry"])
            if len(futs) < 2:
                continue

            near = futs[0]
            next_month = futs[1]
            far_oi = sum(f["oi"] for f in futs[2:]) if len(futs) > 2 else 0

            total_oi = near["oi"] + next_month["oi"] + far_oi
            rollover_pct = ((next_month["oi"] + far_oi) / total_oi * 100) if total_oi > 0 else 0
            rollover_cost = next_month["close"] - near["close"]

            interp = "Neutral"
            if rollover_pct > 75 and rollover_cost > 0: interp = "Long Rollover"
            elif rollover_pct > 75 and rollover_cost < 0: interp = "Short Rollover"

            rollover_cost_pct = (rollover_cost / near["close"] * 100) if near["close"] > 0 else 0.0

            # Calculate historical changes if possible
            idx = prev_dates.index(d)
            prev_d = prev_dates[idx-1] if idx > 0 else None
            price_chg_pct = 0.0
            oi_chg_pct = 0.0

            if prev_d:
                prev_fo = aggregated_prev_fo.get((prev_d, sym))
                if prev_fo:
                    p_price = prev_fo["close"]
                    p_oi = prev_fo["oi"]
                    if p_price > 0:
                        price_chg_pct = ((near["close"] - p_price) / p_price) * 100
                    if p_oi > 0:
                        oi_chg_pct = ((total_oi - p_oi) / p_oi) * 100

            metrics.append({
                "trade_date": d,
                "symbol": sym,
                "rollover_pct": rollover_pct,
                "rollover_cost": rollover_cost,
                "rollover_cost_pct": rollover_cost_pct,
                "near_month_oi": near["oi"],
                "next_month_oi": next_month["oi"],
                "total_oi": total_oi,
                "fut_close": near["close"],
                "price_chg_pct": price_chg_pct,
                "oi_chg_pct": oi_chg_pct
            })

        if metrics:
            stmt = insert(RolloverAnalysisMetrics).values(metrics)
            stmt = stmt.on_conflict_do_update(
                constraint='uq_rollover_analysis_metrics_date_symbol',
                set_={
                    'rollover_pct': stmt.excluded.rollover_pct,
                    'rollover_cost': stmt.excluded.rollover_cost,
                    'rollover_cost_pct': stmt.excluded.rollover_cost_pct,
                    'near_month_oi': stmt.excluded.near_month_oi,
                    'next_month_oi': stmt.excluded.next_month_oi,
                    'total_oi': stmt.excluded.total_oi,
                    'fut_close': stmt.excluded.fut_close,
                    'price_chg_pct': stmt.excluded.price_chg_pct,
                    'oi_chg_pct': stmt.excluded.oi_chg_pct
                }
            )
            db.execute(stmt)
            db.commit()

        return {"status": "success", "message": f"Computed {len(metrics)} records for {len(dates_to_compute)} dates.", "computed": True}
    except Exception as e:
        import traceback
        return {"status": "error", "message": str(e), "traceback": traceback.format_exc()}

@router.post("/api/data/analysis/basis/sync")
def sync_basis_watch(force: str = "false", db: Session = Depends(get_db)):
    try:
        from backend.ingest.nse_models import BhavcopyFO, BasisWatchMetrics
        from sqlalchemy import func

        latest_raw_date = db.query(func.max(BhavcopyFO.trade_date)).filter(BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK'])).scalar()
        latest_metric_date = db.query(func.max(BasisWatchMetrics.trade_date)).scalar()

        if latest_raw_date and latest_metric_date and latest_raw_date <= latest_metric_date and force.lower() != "true":
            return {"status": "success", "message": "Data is already up to date.", "computed": False, "latest_date": str(latest_raw_date)}

        compute_lookback = None if force.lower() == "true" else (str(latest_metric_date) if latest_metric_date else None)
        return compute_basis_watch(db, latest_metric_date=compute_lookback)
    except Exception as e:
        import traceback
        return {"status": "error", "message": str(e), "traceback": traceback.format_exc()}

@router.post("/api/data/analysis/basis/compute")
def compute_basis_watch(db: Session = Depends(get_db), latest_metric_date: str = None):
    try:
        from backend.ingest.nse_models import BhavcopyFO, BasisWatchMetrics, BhavcopyEQ
        from sqlalchemy.dialects.postgresql import insert
        import datetime

        latest_metric_date_obj = datetime.datetime.strptime(latest_metric_date, "%Y-%m-%d").date() if latest_metric_date else None

        all_dates_query = db.query(BhavcopyFO.trade_date).filter(BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK'])).distinct().order_by(BhavcopyFO.trade_date.desc()).all()
        all_dates = [d[0] for d in all_dates_query]

        if not all_dates:
            return {"status": "error", "message": "No data found."}

        dates_to_compute = []
        if latest_metric_date_obj:
            dates_to_compute = [d for d in all_dates if d > latest_metric_date_obj]
        else:
            dates_to_compute = all_dates[:500]

        if not dates_to_compute:
            return {"status": "success", "message": "No new dates to compute.", "computed": False}

        eq_records = db.query(
            BhavcopyEQ.trade_date, BhavcopyEQ.symbol, BhavcopyEQ.close_price
        ).filter(BhavcopyEQ.trade_date.in_(dates_to_compute), BhavcopyEQ.series.in_(['EQ', 'BE', 'SM', 'BZ'])).all()
        eq_map = {(r.trade_date, r.symbol): float(r.close_price) if r.close_price else 0.0 for r in eq_records}

        fo_records = db.query(
            BhavcopyFO.trade_date, BhavcopyFO.ticker_symb, BhavcopyFO.close_price, BhavcopyFO.expiry_date, BhavcopyFO.open_interest
        ).filter(BhavcopyFO.trade_date.in_(dates_to_compute), BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK'])).all()

        fo_map = {}
        for r in fo_records:
            key = (r.trade_date, r.ticker_symb)
            if key not in fo_map:
                fo_map[key] = []
            fo_map[key].append({"expiry": r.expiry_date, "close": float(r.close_price) if r.close_price else 0.0, "oi": float(r.open_interest) if r.open_interest else 0.0})

        metrics = []
        for key, futs in fo_map.items():
            d, sym = key
            futs.sort(key=lambda x: x["expiry"])
            near = futs[0]

            spot = eq_map.get((d, sym))
            if not spot: # try to fallback to futures if eq missing (like indices)
                spot = near["close"]

            fut_price = near["close"]
            basis = fut_price - spot
            basis_pct = (basis / spot * 100) if spot > 0 else 0

            dte = (near["expiry"] - d).days
            dte = max(dte, 1) # Prevent div by 0

            annualized = (basis_pct / dte) * 365

            interp = "Neutral"
            if basis_pct > 0.5: interp = "High Premium"
            elif basis_pct < -0.5: interp = "Discount"
            elif basis_pct > 0: interp = "Premium"

            metrics.append({
                "trade_date": d,
                "symbol": sym,
                "basis_value": basis,
                "basis_pct": basis_pct,
                "near_fut_close": fut_price,
                "cash_close": spot,
                "price_chg_pct": 0.0,
                "carry_cost_annualized": annualized
            })

        if metrics:
            stmt = insert(BasisWatchMetrics).values(metrics)
            stmt = stmt.on_conflict_do_update(
                constraint='uq_basis_watch_metrics_date_symbol',
                set_={
                    'basis_value': stmt.excluded.basis_value,
                    'basis_pct': stmt.excluded.basis_pct,
                    'near_fut_close': stmt.excluded.near_fut_close,
                    'cash_close': stmt.excluded.cash_close,
                    'price_chg_pct': stmt.excluded.price_chg_pct,
                    'carry_cost_annualized': stmt.excluded.carry_cost_annualized
                }
            )
            db.execute(stmt)
            db.commit()

        return {"status": "success", "message": f"Computed {len(metrics)} records for {len(dates_to_compute)} dates.", "computed": True}
    except Exception as e:
        import traceback
        return {"status": "error", "message": str(e), "traceback": traceback.format_exc()}


@router.post("/api/data/derivatives/index_basket_data")
def get_index_basket_data(symbols: list[str], expiry_type: str = "near", db: Session = Depends(get_db)):
    """
    Fetches the latest Futures data for a list of symbols to be used in the Index Basket.
    expiry_type: "near", "next", "far"
    Also fetches the Nifty target index future for the same expiry tier.
    """
    try:
        from backend.ingest.nse_models import BhavcopyFO
        from sqlalchemy import desc

        # 1. Find the latest trade date with Futures data
        latest_fo_date_row = db.query(BhavcopyFO.trade_date)\
                               .filter(BhavcopyFO.instrument_type.in_(['FUTSTK', 'FUTIDX', 'STF', 'IDF', 'FUTIRC']))\
                               .order_by(desc(BhavcopyFO.trade_date))\
                               .first()
        if not latest_fo_date_row:
            return {"data": {}, "nifty": None}
        latest_fo_date = latest_fo_date_row[0]

        # 2. Add NIFTY to symbols list if not present
        query_symbols = [s.upper() for s in symbols]
        if "NIFTY" not in query_symbols:
            query_symbols.append("NIFTY")

        # 3. Fetch Futures data for requested symbols
        fut_records = db.query(
            BhavcopyFO.ticker_symb,
            BhavcopyFO.expiry_date,
            BhavcopyFO.close_price,
            BhavcopyFO.open_interest,
            BhavcopyFO.total_trading_vol
        ).filter(
            BhavcopyFO.trade_date == latest_fo_date,
            BhavcopyFO.ticker_symb.in_(query_symbols),
            BhavcopyFO.instrument_type.in_(['FUTSTK', 'FUTIDX', 'STF', 'IDF', 'FUTIRC'])
        ).all()

        # Group by symbol
        grouped = {}
        for r in fut_records:
            sym = r.ticker_symb
            if sym not in grouped:
                grouped[sym] = []
            grouped[sym].append({
                "expiry": r.expiry_date.strftime('%Y-%m-%d') if r.expiry_date else None,
                "price": float(r.close_price) if r.close_price else 0.0,
                "oi": int(r.open_interest) if r.open_interest else 0,
                "vol": int(r.total_trading_vol) if r.total_trading_vol else 0,
                "timestamp": latest_fo_date.strftime('%Y-%m-%d')
            })

        # Select expiry tier
        expiry_index = 0 if expiry_type == "near" else (1 if expiry_type == "next" else 2)

        result_data = {}
        nifty_data = None

        for sym, expiries in grouped.items():
            # Sort by expiry date ascending
            expiries.sort(key=lambda x: x["expiry"])

            # Ensure we don't go out of bounds if a stock doesn't have 3 expiries
            idx = min(expiry_index, len(expiries) - 1)
            selected = expiries[idx]

            if sym == "NIFTY":
                nifty_data = selected
            if sym in [s.upper() for s in symbols]:
                result_data[sym] = selected

        return {
            "data": result_data,
            "nifty": nifty_data,
            "date": latest_fo_date.strftime('%Y-%m-%d')
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
