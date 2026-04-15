import re

file_path = "backend/web/api/data/derivatives_routes.py"
with open(file_path, "r") as f:
    content = f.read()

# Modify get_aggregated_oi_analysis to accept target_date

search = """def get_aggregated_oi_analysis(days: int = Query(30), db: Session = Depends(get_db)):
    \"\"\"
    Retrieves OI vs Price Quadrant Analysis.
    \"\"\"
    try:
        from backend.ingest.nse_models import OiAnalysisMetrics, SymbolMaster
        from sqlalchemy import desc

        limit_days = min(days + 1, 60) # Limit to a max to be safe, get days+1 for calculations if needed
        dates_query = db.query(OiAnalysisMetrics.trade_date)\\
            .distinct()\\
            .order_by(desc(OiAnalysisMetrics.trade_date))\\
            .limit(limit_days).all()"""

replace = """def get_aggregated_oi_analysis(days: int = Query(30), target_date: str = None, db: Session = Depends(get_db)):
    \"\"\"
    Retrieves OI vs Price Quadrant Analysis.
    \"\"\"
    try:
        from backend.ingest.nse_models import OiAnalysisMetrics, SymbolMaster
        from sqlalchemy import desc

        limit_days = min(days + 1, 60) # Limit to a max to be safe, get days+1 for calculations if needed

        dq = db.query(OiAnalysisMetrics.trade_date).distinct()
        if target_date:
            dq = dq.filter(OiAnalysisMetrics.trade_date <= target_date)

        dates_query = dq.order_by(desc(OiAnalysisMetrics.trade_date)).limit(limit_days).all()"""

content = content.replace(search, replace)

with open(file_path, "w") as f:
    f.write(content)
