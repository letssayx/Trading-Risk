import re

with open("backend/web/api/data/derivatives_routes.py", "r") as f:
    content = f.read()

new_endpoints = """
@router.get("/api/data/analysis/rollover/sectors")
def get_sectoral_rollover(db: Session = Depends(get_db)):
    \"\"\"
    Computes Sector-wide Rollover metrics (average rollover percentage)
    for the last 2 Expiry days.
    \"\"\"
    try:
        from backend.ingest.nse_models import BhavcopyFO, SymbolMaster
        from sqlalchemy import text

        # In NSE, rollover typically peaks on Expiry Day (last Thursday of the month)
        # However, to be general, we can look at the last 2 days where many expiries happened,
        # or just find the last 2 dates where a Near Month contract expired.
        # A simpler approach: find the last 2 expiry dates that have passed.

        expired_dates_query = db.query(BhavcopyFO.expiry_date)\\
            .filter(BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK']))\\
            .filter(BhavcopyFO.expiry_date <= func.current_date())\\
            .distinct()\\
            .order_by(desc(BhavcopyFO.expiry_date))\\
            .limit(2).all()

        if len(expired_dates_query) < 2:
            return {"data": []}

        exp2 = expired_dates_query[0][0] # Most recent expiry
        exp1 = expired_dates_query[1][0] # Previous expiry

        # For each expiry, we want the data ON that expiry day (or the last available trade date on/before it).
        # We query the positions on trade_date = exp1 and trade_date = exp2
        # Then group by Sector.

        results = []
        for d in [exp1, exp2]:
            if not d: continue

            futs = db.query(
                BhavcopyFO.ticker_symb,
                BhavcopyFO.expiry_date,
                BhavcopyFO.open_interest
            ).filter(
                BhavcopyFO.trade_date == d,
                BhavcopyFO.expiry_date >= d,
                BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK'])
            ).order_by(BhavcopyFO.ticker_symb.asc(), BhavcopyFO.expiry_date.asc()).all()

            # Organize
            sym_futs = {}
            for f in futs:
                if f.ticker_symb not in sym_futs:
                    sym_futs[f.ticker_symb] = []
                sym_futs[f.ticker_symb].append(f)

            # Compute Rollover per symbol
            sym_rollovers = {}
            for sym, s_futs in sym_futs.items():
                if len(s_futs) < 2: continue
                total_oi = sum([(int(f.open_interest) if f.open_interest else 0) for f in s_futs])
                near_oi = int(s_futs[0].open_interest) if s_futs[0].open_interest else 0
                roll_pct = ((total_oi - near_oi) / total_oi) * 100 if total_oi > 0 else 0
                sym_rollovers[sym] = roll_pct

            # Group by Sector
            symbols_list = list(sym_rollovers.keys())
            sector_query = db.query(SymbolMaster.symbol, SymbolMaster.sector_index).filter(SymbolMaster.symbol.in_(symbols_list)).all()
            sector_map = {r.symbol: r.sector_index for r in sector_query}

            sector_aggregates = {}
            for sym, roll in sym_rollovers.items():
                sect = sector_map.get(sym, "Unknown")
                if not sect: sect = "Unknown"
                if sect not in sector_aggregates:
                    sector_aggregates[sect] = []
                sector_aggregates[sect].append(roll)

            for sect, rolls in sector_aggregates.items():
                avg_roll = sum(rolls) / len(rolls)
                results.append({
                    "date": str(d),
                    "sector": sect,
                    "avg_rollover_pct": round(avg_roll, 2)
                })

        return {"data": results}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))

@router.get("/api/data/analysis/rollover/history/{symbol}")
def get_symbol_rollover_history(symbol: str, db: Session = Depends(get_db)):
    \"\"\"
    Gets rollover history for the last 12 expiry days for a specific stock/index.
    \"\"\"
    try:
        from backend.ingest.nse_models import BhavcopyFO
        symbol = symbol.upper()

        # Get last 12 unique expiry dates for this symbol
        expired_dates_query = db.query(BhavcopyFO.expiry_date)\\
            .filter(BhavcopyFO.ticker_symb == symbol)\\
            .filter(BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK']))\\
            .filter(BhavcopyFO.expiry_date <= func.current_date())\\
            .distinct()\\
            .order_by(desc(BhavcopyFO.expiry_date))\\
            .limit(12).all()

        expired_dates = [d[0] for d in expired_dates_query]
        expired_dates.reverse() # chronological order

        results = []
        for d in expired_dates:
            # For each expiry date, compute the rollover on that exact day
            futs = db.query(
                BhavcopyFO.expiry_date,
                BhavcopyFO.open_interest
            ).filter(
                BhavcopyFO.trade_date == d,
                BhavcopyFO.ticker_symb == symbol,
                BhavcopyFO.expiry_date >= d,
                BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK'])
            ).order_by(BhavcopyFO.expiry_date.asc()).all()

            if len(futs) < 2: continue

            total_oi = sum([(int(f.open_interest) if f.open_interest else 0) for f in futs])
            near_oi = int(futs[0].open_interest) if futs[0].open_interest else 0
            roll_pct = ((total_oi - near_oi) / total_oi) * 100 if total_oi > 0 else 0

            results.append({
                "date": str(d),
                "rollover_pct": round(roll_pct, 2)
            })

        return {"symbol": symbol, "data": results}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))
"""

# Append the new endpoints before the router definition ends (which isn't specifically marked, we can append to the file)
with open("backend/web/api/data/derivatives_routes.py", "a") as f:
    f.write(new_endpoints)
