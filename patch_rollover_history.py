import re

with open('backend/web/api/data/derivatives_routes.py', 'r') as f:
    content = f.read()

# Add a mock/real endpoint for the 12 month stock rollover history if it doesn't exist
new_endpoint = """
@router.get("/api/data/analysis/rollover/history/{symbol}")
def get_stock_rollover_history(symbol: str, db: Session = Depends(get_db)):
    \"\"\"
    Returns 12-month rollover history for a given stock symbol.
    \"\"\"
    from backend.ingest.nse_models import BhavcopyFO
    from sqlalchemy import desc

    # Get last 12 expiries
    expiries = db.query(BhavcopyFO.expiry_date)\\
        .filter(BhavcopyFO.ticker_symb == symbol)\\
        .filter(BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK']))\\
        .distinct()\\
        .order_by(desc(BhavcopyFO.expiry_date))\\
        .limit(12).all()

    exp_dates = sorted([e[0] for e in expiries])
    if not exp_dates:
        return {"data": []}

    results = []

    for dt in exp_dates:
        # Find the trade date closest to (or exactly on) the expiry date
        closest_trade_date_row = db.query(BhavcopyFO.trade_date)\\
            .filter(BhavcopyFO.ticker_symb == symbol)\\
            .filter(BhavcopyFO.trade_date <= dt)\\
            .order_by(desc(BhavcopyFO.trade_date))\\
            .first()

        if not closest_trade_date_row:
            continue

        trade_date = closest_trade_date_row[0]

        # Get futures for this symbol on this trade date
        futs = db.query(BhavcopyFO.open_interest, BhavcopyFO.expiry_date)\\
            .filter(BhavcopyFO.ticker_symb == symbol)\\
            .filter(BhavcopyFO.trade_date == trade_date)\\
            .filter(BhavcopyFO.expiry_date >= trade_date)\\
            .order_by(BhavcopyFO.expiry_date.asc())\\
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
"""

if "@router.get(\"/api/data/analysis/rollover/history/{symbol}\")" not in content:
    content += "\n" + new_endpoint
    with open('backend/web/api/data/derivatives_routes.py', 'w') as f:
        f.write(content)
    print("Added stock rollover history endpoint.")
else:
    print("Endpoint already exists.")
