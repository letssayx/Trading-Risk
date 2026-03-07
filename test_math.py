from datetime import datetime
from backend.infrastructure.db import SessionLocal
from backend.analysis.toolbox.reports.morning_report import MorningReportCalculator

db = SessionLocal()
calc = MorningReportCalculator(db)
try:
    res = calc.calculate_for_date(datetime(2024, 2, 28).date())
    print(res)
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    db.close()
