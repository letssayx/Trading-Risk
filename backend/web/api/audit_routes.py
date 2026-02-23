from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional, Any
from datetime import datetime

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
        query = query.filter(SystemLog.timestamp <= end_date)

    logs = query.limit(limit).all()

    return [
        {
            "timestamp": l.timestamp.isoformat(),
            "level": l.level,
            "source": l.source,
            "message": l.message
        }
        for l in logs
    ]
