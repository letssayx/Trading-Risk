import re

with open('backend/web/api/data/derivatives_routes.py', 'r') as f:
    content = f.read()

# We need to add sectoral historical rollover data.
# The endpoint /api/data/analysis/rollover is fine, but maybe we need a new one
# or modify it to also return sector rollover history. Let's create a new endpoint
# for sector rollover history to avoid cluttering the main aggregated one.

new_endpoint = """
@router.get("/api/data/analysis/rollover/sectors")
def get_sector_rollover_history(db: Session = Depends(get_db)):
    \"\"\"
    Returns the rollover percentage for the previous 2 expiries for Nifty, BankNifty, and all other sectoral indices.
    \"\"\"
    from backend.ingest.nse_models import BhavcopyFO, SymbolMaster
    from sqlalchemy import desc
    import datetime

    # Get last 3 expiry dates
    latest_futs = db.query(BhavcopyFO.expiry_date)\\
        .filter(BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK']))\\
        .distinct()\\
        .order_by(desc(BhavcopyFO.expiry_date))\\
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
        closest_trade_date_row = db.query(BhavcopyFO.trade_date)\\
            .filter(BhavcopyFO.trade_date <= dt)\\
            .order_by(desc(BhavcopyFO.trade_date))\\
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
    formatted = []
    exp_strs = [str(d) for d in target_dates]
    for sector, vals in results.items():
        formatted.append({
            "sector": sector,
            "exp1": exp_strs[0],
            "exp1_roll": vals.get(exp_strs[0], 0),
            "exp2": exp_strs[1] if len(exp_strs) > 1 else "",
            "exp2_roll": vals.get(exp_strs[1], 0) if len(exp_strs) > 1 else 0
        })

    return {"data": formatted, "expiries": exp_strs}
"""

if "@router.get(\"/api/data/analysis/rollover/sectors\")" not in content:
    content += "\n" + new_endpoint
    with open('backend/web/api/data/derivatives_routes.py', 'w') as f:
        f.write(content)
    print("Added /api/data/analysis/rollover/sectors endpoint.")
else:
    print("Endpoint already exists.")
