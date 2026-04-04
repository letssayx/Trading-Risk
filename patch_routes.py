import re

with open("backend/web/api/data/derivatives_routes.py", "r") as f:
    content = f.read()

# Add func import
content = content.replace("from sqlalchemy import desc, text", "from sqlalchemy import desc, text, func")

# Change date query in get_aggregated_oi_analysis to use BhavcopyFO
content = re.sub(
    r"# 1\. Get the latest two trading dates\n\s+from backend\.ingest\.nse_models import BhavcopyEQ\n\s+dates_query = db\.query\(BhavcopyEQ\.trade_date\)\\\n\s+\.filter\(BhavcopyEQ\.series == 'EQ'\)\\\n\s+\.distinct\(\)\\\n\s+\.order_by\(BhavcopyEQ\.trade_date\.desc\(\)\)\\\n\s+\.limit\(2\)\.all\(\)",
    """# 1. Get the latest two trading dates
        from backend.ingest.nse_models import BhavcopyFO
        dates_query = db.query(BhavcopyFO.trade_date)\\
                  .filter(BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK', 'FUTIVX', 'FUTIRC']))\\
                  .distinct()\\
                  .order_by(BhavcopyFO.trade_date.desc())\\
                  .limit(2).all()""",
    content
)

content = content.replace("db.func.sum(BhavcopyFO.open_interest).label('total_opt_oi')", "func.sum(BhavcopyFO.open_interest).label('total_opt_oi')")

# also for the extended advanced filters (500 dates) in get_aggregated_oi_analysis
content = re.sub(
    r"# Get last 500 dates for extended advanced filters\n\s+from backend\.ingest\.nse_models import BhavcopyEQ\n\s+all_hist_dates_query = db\.query\(BhavcopyEQ\.trade_date\)\\\n\s+\.filter\(BhavcopyEQ\.series == 'EQ'\)\\\n\s+\.distinct\(\)\\\n\s+\.order_by\(BhavcopyEQ\.trade_date\.desc\(\)\)\\\n\s+\.limit\(500\)\.all\(\)",
    """# Get last 500 dates for extended advanced filters
        from backend.ingest.nse_models import BhavcopyFO
        all_hist_dates_query = db.query(BhavcopyFO.trade_date)\\
                  .filter(BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK', 'FUTIVX', 'FUTIRC']))\\
                  .distinct()\\
                  .order_by(BhavcopyFO.trade_date.desc())\\
                  .limit(500).all()""",
    content
)

with open("backend/web/api/data/derivatives_routes.py", "w") as f:
    f.write(content)
