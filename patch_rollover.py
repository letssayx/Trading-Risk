import re

with open("backend/web/api/data/derivatives_routes.py", "r") as f:
    content = f.read()

# Enhance get_aggregated_rollover_analysis endpoint
content = re.sub(
    r"# Get latest date\n\s+from backend\.ingest\.nse_models import BhavcopyEQ\n\s+latest_date_query = db\.query\(BhavcopyEQ\.trade_date\)\\\n\s+\.filter\(BhavcopyEQ\.series == 'EQ'\)\\\n\s+\.distinct\(\)\\\n\s+\.order_by\(BhavcopyEQ\.trade_date\.desc\(\)\)\\\n\s+\.first\(\)",
    """# Get latest date
        from backend.ingest.nse_models import BhavcopyFO
        dates_query = db.query(BhavcopyFO.trade_date)\\
                  .filter(BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK', 'FUTIVX', 'FUTIRC']))\\
                  .distinct()\\
                  .order_by(BhavcopyFO.trade_date.desc())\\
                  .limit(12).all()

        if not dates_query:
            return {"data": []}

        latest_date = dates_query[0][0]""",
    content
)

# Replace everything from "# Get all futures for the latest date" to the end of the function
start_marker = "# Get all futures for the latest date"
end_marker = "return {\"date\": str(latest_date), \"data\": results}"
start_idx = content.find(start_marker)
end_idx = content.find(end_marker) + len(end_marker)

replacement = """# Get all futures for the latest date
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

        from backend.ingest.nse_models import SymbolMaster
        symbols_list = list(sym_futs.keys())
        sector_query = db.query(SymbolMaster.symbol, SymbolMaster.sector_index).filter(SymbolMaster.symbol.in_(symbols_list)).all()
        sector_map = {r.symbol: r.sector_index for r in sector_query}

        target_dates = [d[0] for d in dates_query][:10]

        # Fetch history for the last 10 days for these symbols
        hist_query = db.query(
            BhavcopyFO.ticker_symb,
            BhavcopyFO.trade_date,
            BhavcopyFO.close_price,
            BhavcopyFO.open_interest,
            BhavcopyFO.expiry_date
        ).filter(
            BhavcopyFO.trade_date.in_(target_dates),
            BhavcopyFO.expiry_date >= BhavcopyFO.trade_date,
            BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK', 'FUTIVX', 'FUTIRC'])
        ).order_by(BhavcopyFO.trade_date.desc(), BhavcopyFO.expiry_date.asc()).all()

        hist_data = {}
        for r in hist_query:
            sym = r.ticker_symb
            dt = r.trade_date
            if sym not in hist_data:
                hist_data[sym] = {}
            if dt not in hist_data[sym]:
                # first record is near expiry (FUT 1) due to order by expiry asc
                hist_data[sym][dt] = {
                    "price": float(r.close_price) if r.close_price else 0.0,
                    "oi": int(r.open_interest) if r.open_interest else 0,
                    "total_oi": 0
                }
            hist_data[sym][dt]["total_oi"] += (int(r.open_interest) if r.open_interest else 0)

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

            # History
            hist_arr = []
            oi_chg_pct = 0
            price_chg_pct = 0

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
                    if prev_h and prev_h["price"] > 0 and prev_h["total_oi"] > 0:
                        h_price_chg = ((curr_h["price"] - prev_h["price"]) / prev_h["price"]) * 100
                        h_oi_chg = ((curr_h["total_oi"] - prev_h["total_oi"]) / prev_h["total_oi"]) * 100

                        if i == 0:
                            oi_chg_pct = h_oi_chg
                            price_chg_pct = h_price_chg

                    if dt in target_dates[:10]:
                        hist_arr.append({
                            "date": str(dt),
                            "price": curr_h["price"],
                            "oi": curr_h["total_oi"],
                            "price_chg_pct": round(h_price_chg, 2),
                            "oi_chg_pct": round(h_oi_chg, 2)
                        })

            results.append({
                "symbol": sym,
                "sector": sector_map.get(sym, "Unknown"),
                "rollover_pct": round(rollover_pct, 2),
                "rollover_cost": round(spread, 2),
                "rollover_cost_pct": round(spread_pct, 2),
                "near_oi": near_oi,
                "total_oi": total_oi,
                "near_price": near_price,
                "next_price": next_price,
                "price": near_price,
                "oi_chg_pct": round(oi_chg_pct, 2),
                "price_chg_pct": round(price_chg_pct, 2),
                "history": hist_arr[:10]
            })

        return {"date": str(latest_date), "data": results}"""

content = content[:start_idx] + replacement + content[end_idx:]

with open("backend/web/api/data/derivatives_routes.py", "w") as f:
    f.write(content)
