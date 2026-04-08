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
def get_aggregated_oi_analysis(force_compute: bool = False, db: Session = Depends(get_db)):
    """
    Reads OI vs Price Quadrant Analysis data instantly from the pre-computed oi_analysis_metrics table.
    Includes historical array for table expansion.
    """
    try:
        from backend.ingest.nse_models import OiAnalysisMetrics, SymbolMaster, BhavcopyFO
        from sqlalchemy import desc

        if force_compute:
            compute_aggregated_oi_analysis(db)

        dates_query = db.query(OiAnalysisMetrics.trade_date)\
            .distinct()\
            .order_by(desc(OiAnalysisMetrics.trade_date))\
            .limit(31).all()

        if not dates_query:
            return {"data": []}

        valid_dates = [d[0] for d in dates_query]
        latest_date = valid_dates[0]

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

            sym_map[sym]["history"].append({
                "date": str(analysis.trade_date),
                "price": analysis.price or 0.0,
                "price_chg_pct": analysis.price_chg_pct or 0.0,
                "fut_oi": analysis.fut_oi or 0,
                "call_oi": analysis.call_oi or 0,
                "put_oi": analysis.put_oi or 0,
                "total_oi": analysis.total_oi or 0,
                "fut_oi_chg_pct": analysis.fut_oi_chg_pct or 0.0,
                "call_oi_chg_pct": analysis.call_oi_chg_pct or 0.0,
                "put_oi_chg_pct": analysis.put_oi_chg_pct or 0.0,
                "oi_chg_pct": analysis.oi_chg_pct or 0.0,
                "fut_oi_chg_pct_30d": analysis.fut_oi_chg_pct_30d or 0.0,
                "call_oi_chg_pct_30d": analysis.call_oi_chg_pct_30d or 0.0,
                "put_oi_chg_pct_30d": analysis.put_oi_chg_pct_30d or 0.0,
                "fut_oi_chg": analysis.fut_oi_chg or 0,
                "call_oi_chg": analysis.call_oi_chg or 0,
                "put_oi_chg": analysis.put_oi_chg or 0,
                "pcr": analysis.pcr or 0.0,
                "atm_iv": analysis.atm_iv or 0.0
            })

        results = []
        for sym, data in sym_map.items():
            if not data["history"]:
                continue

            latest = data["history"][0]

            if latest["date"] != str(latest_date):
                continue

            res = {
                "symbol": sym,
                "sector": data["sector"],
                "date": latest["date"],
                "price": latest["price"],
                "price_chg_pct": latest["price_chg_pct"],
                "fut_oi": latest["fut_oi"],
                "call_oi": latest["call_oi"],
                "put_oi": latest["put_oi"],
                "total_oi": latest["total_oi"],
                "fut_oi_chg_pct": latest["fut_oi_chg_pct"],
                "call_oi_chg_pct": latest["call_oi_chg_pct"],
                "put_oi_chg_pct": latest["put_oi_chg_pct"],
                "oi_chg_pct": latest["oi_chg_pct"],
                "fut_oi_chg_pct_30d": latest["fut_oi_chg_pct_30d"],
                "call_oi_chg_pct_30d": latest["call_oi_chg_pct_30d"],
                "put_oi_chg_pct_30d": latest["put_oi_chg_pct_30d"],
                "fut_oi_chg": latest["fut_oi_chg"],
                "call_oi_chg": latest["call_oi_chg"],
                "put_oi_chg": latest["put_oi_chg"],
                "pcr": latest["pcr"],
                "atm_iv": latest["atm_iv"],
                "history": data["history"]
            }
            results.append(res)

        return {"data": results}

    except Exception as e:
        import logging
        logging.error(f"Error fetching aggregated OI analysis: {e}")
        return {"data": []}


@router.post("/api/data/analysis/oi/compute")
def compute_aggregated_oi_analysis(db: Session = Depends(get_db)):
    """
    Computes OI vs Price Quadrant Analysis for all F&O symbols.
    """
    try:
        from backend.ingest.nse_models import BhavcopyFO, HistoricalATMIV
        from sqlalchemy.dialects.postgresql import insert
        from backend.ingest.nse_models import OiAnalysisMetrics
        import datetime

        # Get last 32 dates to compute 30 full days of history
        dates_query = db.query(BhavcopyFO.trade_date)\
                  .filter(BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK', 'FUTIVX', 'FUTIRC']))\
                  .distinct()\
                  .order_by(BhavcopyFO.trade_date.desc())\
                  .limit(32).all()

        if len(dates_query) < 2:
            return {"status": "error", "message": "Not enough data"}

        valid_dates = [d[0] for d in dates_query]

        # Load all records for these 32 dates
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
            BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK', 'FUTIVX', 'FUTIRC', 'OPTIDX', 'OPTSTK'])
        ).order_by(BhavcopyFO.trade_date.asc(), BhavcopyFO.expiry_date.asc()).all()

        # Group data: symbol -> date -> metrics
        sym_data = {}
        for r in query:
            sym = r.ticker_symb
            dt = r.trade_date
            if sym not in sym_data:
                sym_data[sym] = {d: {"price": None, "fut_oi": 0, "call_oi": 0, "put_oi": 0} for d in valid_dates}

            if r.instrument_type in ['FUTIDX', 'FUTSTK', 'FUTIVX', 'FUTIRC']:
                sym_data[sym][dt]["fut_oi"] += int(r.open_interest) if r.open_interest else 0
                if sym_data[sym][dt]["price"] is None:
                    sym_data[sym][dt]["price"] = float(r.close_price) if r.close_price else 0.0
            elif r.instrument_type in ['OPTIDX', 'OPTSTK']:
                if r.option_type == 'CE':
                    sym_data[sym][dt]["call_oi"] += int(r.open_interest) if r.open_interest else 0
                elif r.option_type == 'PE':
                    sym_data[sym][dt]["put_oi"] += int(r.open_interest) if r.open_interest else 0

        atm_iv_records = db.query(HistoricalATMIV).filter(HistoricalATMIV.trade_date.in_(valid_dates)).all()
        atm_iv_map = {}
        for r in atm_iv_records:
            if r.symbol not in atm_iv_map:
                atm_iv_map[r.symbol] = {}
            atm_iv_map[r.symbol][r.trade_date] = float(r.atm_iv) if r.atm_iv else 0.0

        insert_data = []

        # For every symbol, compute history for the top 30 dates (excluding the 31st/32nd needed for 1d/30d lookbacks)
        # We compute history up to valid_dates[:-2] or wherever possible
        for sym, date_dict in sym_data.items():
            for i in range(len(valid_dates)):
                curr_date = valid_dates[i]

                # We need yesterday
                if i + 1 >= len(valid_dates): break
                prev_date = valid_dates[i+1]

                # We need 30 days ago
                date_30d_idx = min(i + 30, len(valid_dates) - 1)
                date_30d = valid_dates[date_30d_idx]

                cd = date_dict[curr_date]
                pd = date_dict[prev_date]
                m30d = date_dict[date_30d]

                if cd["price"] is None or cd["price"] == 0:
                    continue

                prev_p = pd["price"] if pd["price"] else cd["price"]
                p_chg = ((cd["price"] - prev_p) / prev_p) * 100 if prev_p > 0 else 0

                fut_oi_chg_1d = cd["fut_oi"] - pd["fut_oi"]
                call_oi_chg_1d = cd["call_oi"] - pd["call_oi"]
                put_oi_chg_1d = cd["put_oi"] - pd["put_oi"]

                fut_oi_chg_pct = (fut_oi_chg_1d / pd["fut_oi"] * 100) if pd["fut_oi"] > 0 else 0
                call_oi_chg_pct = (call_oi_chg_1d / pd["call_oi"] * 100) if pd["call_oi"] > 0 else 0
                put_oi_chg_pct = (put_oi_chg_1d / pd["put_oi"] * 100) if pd["put_oi"] > 0 else 0

                fut_oi_chg_pct_30d = ((cd["fut_oi"] - m30d["fut_oi"]) / m30d["fut_oi"] * 100) if m30d["fut_oi"] > 0 else 0
                call_oi_chg_pct_30d = ((cd["call_oi"] - m30d["call_oi"]) / m30d["call_oi"] * 100) if m30d["call_oi"] > 0 else 0
                put_oi_chg_pct_30d = ((cd["put_oi"] - m30d["put_oi"]) / m30d["put_oi"] * 100) if m30d["put_oi"] > 0 else 0

                tot_oi_curr = cd["fut_oi"] + cd["call_oi"] + cd["put_oi"]
                tot_oi_prev = pd["fut_oi"] + pd["call_oi"] + pd["put_oi"]
                tot_oi_chg_pct = ((tot_oi_curr - tot_oi_prev) / tot_oi_prev * 100) if tot_oi_prev > 0 else 0

                pcr = cd["put_oi"] / cd["call_oi"] if cd["call_oi"] > 0 else 0

                atm_val = 0.0
                if sym in atm_iv_map and curr_date in atm_iv_map[sym]:
                    atm_val = atm_iv_map[sym][curr_date]

                insert_data.append({
                    "trade_date": curr_date,
                    "symbol": sym,
                    "price": round(cd["price"], 2),
                    "price_chg_pct": round(p_chg, 2),
                    "fut_oi": cd["fut_oi"],
                    "call_oi": cd["call_oi"],
                    "put_oi": cd["put_oi"],
                    "total_oi": tot_oi_curr,
                    "fut_oi_chg": fut_oi_chg_1d,
                    "call_oi_chg": call_oi_chg_1d,
                    "put_oi_chg": put_oi_chg_1d,
                    "fut_oi_chg_pct": round(fut_oi_chg_pct, 2),
                    "call_oi_chg_pct": round(call_oi_chg_pct, 2),
                    "put_oi_chg_pct": round(put_oi_chg_pct, 2),
                    "oi_chg_pct": round(tot_oi_chg_pct, 2),
                    "fut_oi_chg_pct_30d": round(fut_oi_chg_pct_30d, 2),
                    "call_oi_chg_pct_30d": round(call_oi_chg_pct_30d, 2),
                    "put_oi_chg_pct_30d": round(put_oi_chg_pct_30d, 2),
                    "pcr": round(pcr, 2),
                    "atm_iv": round(atm_val, 2)
                })

        if insert_data:
            stmt = insert(OiAnalysisMetrics).values(insert_data)
            stmt = stmt.on_conflict_do_update(
                index_elements=['trade_date', 'symbol'],
                set_={
                    "price": stmt.excluded.price,
                    "price_chg_pct": stmt.excluded.price_chg_pct,
                    "fut_oi": stmt.excluded.fut_oi,
                    "call_oi": stmt.excluded.call_oi,
                    "put_oi": stmt.excluded.put_oi,
                    "total_oi": stmt.excluded.total_oi,
                    "fut_oi_chg_pct": stmt.excluded.fut_oi_chg_pct,
                    "call_oi_chg_pct": stmt.excluded.call_oi_chg_pct,
                    "put_oi_chg_pct": stmt.excluded.put_oi_chg_pct,
                    "oi_chg_pct": stmt.excluded.oi_chg_pct,
                    "fut_oi_chg_pct_30d": stmt.excluded.fut_oi_chg_pct_30d,
                    "call_oi_chg_pct_30d": stmt.excluded.call_oi_chg_pct_30d,
                    "put_oi_chg_pct_30d": stmt.excluded.put_oi_chg_pct_30d,
                    "fut_oi_chg": stmt.excluded.fut_oi_chg,
                    "call_oi_chg": stmt.excluded.call_oi_chg,
                    "put_oi_chg": stmt.excluded.put_oi_chg,
                    "pcr": stmt.excluded.pcr,
                    "atm_iv": stmt.excluded.atm_iv
                }
            )
            db.execute(stmt)
            db.commit()

        return {"status": "success", "message": f"Computed and backfilled 30 day history"}
    except Exception as e:
        import logging
        logging.error(f"Error computing aggregated OI analysis: {e}")
        return {"status": "error", "message": str(e)}

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
