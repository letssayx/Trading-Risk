from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from fastapi.concurrency import run_in_threadpool

from backend.infrastructure.db import get_db
from backend.models.audit import SystemLog
from backend.web.live.logs import LOG_BUFFER

router = APIRouter()

@router.post("/log")
async def log_client_event(
    event: dict = Body(...)
):
    """
    Endpoint for frontend to send logs/audit events.
    event = { level, source, message, event_type, meta_data }
    """
    # Enriched with server time
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "level": event.get("level", "INFO"),
        "source": event.get("source", "Frontend"),
        "event_type": event.get("event_type", "User_Action"),
        "message": event.get("message", ""),
        "meta_data": event.get("meta_data", {})
    }

    # Add to buffer for persistence
    LOG_BUFFER.append(log_entry)

    return {"status": "queued"}

@router.get("/history")
async def get_log_history(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    level: Optional[str] = None,
    limit: int = 500,
    db: Session = Depends(get_db)
):
    """
    Fetch historical logs.
    """
    query = db.query(SystemLog).order_by(SystemLog.timestamp.desc())

    if start_date:
        query = query.filter(SystemLog.timestamp >= start_date)
    if end_date:
        # Include the whole end day
        query = query.filter(SystemLog.timestamp <= f"{end_date} 23:59:59")
    if level and level.upper() != 'ALL':
        query = query.filter(SystemLog.level == level.upper())

    # Wrap sync db call in threadpool to prevent blocking the async event loop
    logs = await run_in_threadpool(lambda: query.limit(limit).all())

    return [
        {
            "timestamp": l.timestamp.isoformat(),
            "level": l.level,
            "source": l.source,
            "message": l.message
        }
        for l in logs
    ]
