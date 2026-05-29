import sys

with open('backend/web/api/data/derivatives_routes.py', 'r') as f:
    content = f.read()

# 1. Fix the days limit for MoM history in get_aggregated_rollover_analysis
search1 = """
        if is_expiry_only:
            # Get historical expiry dates
            expiries = db.query(BhavcopyFO.expiry_date).filter(
                BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK'])
            ).distinct().order_by(desc(BhavcopyFO.expiry_date)).all()
            expiry_dates = [e[0] for e in expiries]

            # Fetch the closest trade dates that match the expiries, plus the latest date
            # Limit the search to the required 'days' points (which essentially represents 'months' here)
            dates_query = db.query(RolloverAnalysisMetrics.trade_date)\\
                      .distinct()\\
                      .order_by(RolloverAnalysisMetrics.trade_date.desc())\\
                      .limit(300).all()
            all_trade_dates = [d[0] for d in dates_query]

            hist_dates.append(latest_date) # Always include latest

            seen_expiries = set()
            for e_date in expiry_dates:
                if len(hist_dates) >= days + 1:
                    break
"""

replace1 = """
        if is_expiry_only:
            target_months = 24
            # Get historical expiry dates
            expiries = db.query(BhavcopyFO.expiry_date).filter(
                BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK'])
            ).distinct().order_by(desc(BhavcopyFO.expiry_date)).all()
            expiry_dates = [e[0] for e in expiries]

            # Fetch the closest trade dates that match the expiries, plus the latest date
            dates_query = db.query(RolloverAnalysisMetrics.trade_date)\\
                      .distinct()\\
                      .order_by(RolloverAnalysisMetrics.trade_date.desc())\\
                      .limit(600).all()
            all_trade_dates = [d[0] for d in dates_query]

            hist_dates.append(latest_date) # Always include latest

            seen_expiries = set()
            for e_date in expiry_dates:
                if len(hist_dates) >= target_months + 1:
                    break
"""

content = content.replace(search1.strip("\n"), replace1.strip("\n"))

# 2. Fix the loop constraint target_len
search2 = """
                if i < days and dt in hist_dates[:days]:
                    history_arr.append({
"""

replace2 = """
                target_len = 24 if is_expiry_only else days

                if len(history_arr) < target_len and dt in hist_dates:
                    history_arr.append({
"""
content = content.replace(search2.strip("\n"), replace2.strip("\n"))

# 3. Fix the single symbol history limit
search3 = """
        # For simplicity, if we query the last 300 days of rollover metrics, we can just filter in memory
        records = db.query(RolloverAnalysisMetrics).filter(
            RolloverAnalysisMetrics.symbol == symbol
        ).order_by(desc(RolloverAnalysisMetrics.trade_date)).limit(300).all()

        results = []
        seen_expiries = set()

        # We need exactly 12 expiry points
        for e_date in expiry_dates:
            if len(results) >= 12:
                break
"""

replace3 = """
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
"""

content = content.replace(search3.strip("\n"), replace3.strip("\n"))

with open('backend/web/api/data/derivatives_routes.py', 'w') as f:
    f.write(content)

print("Backend patched")
