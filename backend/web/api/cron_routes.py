from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from backend.infrastructure.db import get_db
from backend.ingest.nse_models import CronJobConfig, CorporateAnnouncement
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/cron", tags=["Cron Jobs"])

@router.get("/configs")
def get_cron_configs(db: Session = Depends(get_db)):
    """Fetch all cron job configurations"""
    configs = db.query(CronJobConfig).all()
    return [{"id": c.id, "job_name": c.job_name, "is_active": c.is_active,
             "interval_seconds": c.interval_seconds, "run_time": c.run_time,
             "last_run": c.last_run} for c in configs]

@router.put("/configs/{job_name}")
def update_cron_config(job_name: str, payload: dict = Body(...), db: Session = Depends(get_db)):
    """Update a specific cron job configuration"""
    config = db.query(CronJobConfig).filter(CronJobConfig.job_name == job_name).first()
    if not config:
        raise HTTPException(status_code=404, detail="Job not found")

    if "is_active" in payload:
        config.is_active = payload["is_active"]
    if "interval_seconds" in payload:
        config.interval_seconds = payload["interval_seconds"]
    if "run_time" in payload:
        config.run_time = payload["run_time"]

    db.commit()
    return {"status": "success", "message": f"Updated config for {job_name}"}

@router.get("/corporate-announcements")
def get_corporate_announcements(limit: int = 50, db: Session = Depends(get_db)):
    """Fetch the latest corporate announcements from the database"""
    announcements = db.query(CorporateAnnouncement).order_by(CorporateAnnouncement.broadcast_date.desc()).limit(limit).all()
    return [{
        "id": a.id,
        "seq_id": a.seq_id,
        "symbol": a.symbol,
        "broadcast_date": a.broadcast_date.strftime("%Y-%m-%d %H:%M:%S") if a.broadcast_date else None,
        "import_time": a.import_time.strftime("%Y-%m-%d %H:%M:%S") if a.import_time else None,
        "subject": a.subject,
        "purpose": a.purpose,
        "pdf_link": a.pdf_link,
        "xbrl_link": a.xbrl_link,
        "ai_interpretation": a.ai_interpretation,
        "radio_status": a.radio_status
    } for a in announcements]

@router.get("/corporate-actions-live")
def get_corporate_actions_live(limit: int = 50, db: Session = Depends(get_db)):
    """Fetch the latest live corporate actions from the database"""
    from backend.ingest.nse_models import CorporateActionLive
    actions = db.query(CorporateActionLive).order_by(CorporateActionLive.import_time.desc()).limit(limit).all()
    return [{
        "id": a.id,
        "symbol": a.symbol,
        "series": a.series,
        "company": a.company,
        "purpose": a.purpose,
        "ex_date": a.ex_date,
        "record_date": a.record_date,
        "bc_start_date": a.bc_start_date,
        "bc_end_date": a.bc_end_date,
        "nd_start_date": a.nd_start_date,
        "nd_end_date": a.nd_end_date,
        "import_time": a.import_time.strftime("%Y-%m-%d %H:%M:%S") if a.import_time else None
    } for a in actions]

@router.post("/force-fetch/{job_name}")
async def force_fetch_job(job_name: str):
    """Force execution of a specific cron job immediately, bypassing schedule"""
    from backend.ingest.cron_manager import JOB_HANDLERS
    import asyncio

    if job_name in JOB_HANDLERS:
        try:
            # Safely create task in the running loop since the function is now async
            loop = asyncio.get_running_loop()
            loop.create_task(JOB_HANDLERS[job_name]())
            return {"status": "success", "message": f"Force triggered {job_name}"}
        except Exception as e:
            logger.error(f"Failed to force fetch {job_name}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=404, detail="Job handler not found")
