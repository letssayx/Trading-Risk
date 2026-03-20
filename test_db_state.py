import logging
from backend.infrastructure.db import SessionLocal
from backend.ingest.nse_models import CorporateAction, BoardMeeting, ImportLog
from sqlalchemy import func

logging.basicConfig(level=logging.INFO)
db = SessionLocal()

try:
    ca_count = db.query(CorporateAction).count()
    print("Total Corporate Actions:", ca_count)
    bm_count = db.query(BoardMeeting).count()
    print("Total Board Meetings:", bm_count)

    logs = db.query(ImportLog).filter(ImportLog.table_name.in_(['corporate_actions', 'board_meetings'])).order_by(ImportLog.id.desc()).limit(10).all()
    print("Recent Import Logs:")
    for log in logs:
        print(f"{log.import_date} | {log.table_name} | {log.status} | In: {log.rows_inserted} | Err: {log.error_msg}")

except Exception as e:
    print("DB Error:", e)
