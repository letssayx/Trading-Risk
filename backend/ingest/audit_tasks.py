from celery import shared_task
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict, Any

from backend.infrastructure.db import SessionLocal
from backend.models.audit import SystemLog

@shared_task
def persist_log_batch(logs: List[Dict[str, Any]]):
    """
    Bulk insert logs into the database.
    logs = [{level, source, message, event_type, meta_data, timestamp}, ...]
    """
    if not logs:
        return

    db: Session = SessionLocal()
    try:
        log_objects = []
        for log in logs:
            # Parse timestamp if string
            ts = log.get('timestamp')
            if isinstance(ts, str):
                try:
                    ts = datetime.fromisoformat(ts)
                except:
                    ts = datetime.now()

            log_objects.append(SystemLog(
                timestamp=ts or datetime.now(),
                level=log.get('level', 'INFO'),
                source=log.get('source', 'System'),
                event_type=log.get('event_type', 'Log'),
                message=log.get('message', ''),
                user_id=log.get('user_id'),
                meta_data=log.get('meta_data')
            ))

        db.bulk_save_objects(log_objects)
        db.commit()
    except Exception as e:
        print(f"Failed to persist logs: {e}")
        db.rollback()
    finally:
        db.close()
