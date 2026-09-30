import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from backend.infrastructure.db import SessionLocal
from backend.ingest.nse_models import CronJobConfig
import traceback

logger = logging.getLogger(__name__)

# Track last run times in memory to avoid constant DB writes if interval is short
_last_run_times = {}

async def trigger_corporate_announcements():
    from backend.ingest.tasks import process_corporate_announcements_task
    process_corporate_announcements_task.delay()

async def trigger_live_actions():
    from backend.ingest.tasks import process_live_corporate_actions_task
    process_live_corporate_actions_task.delay()

async def trigger_mwpl():
    from backend.ingest.tasks import import_mwpl_task
    import_mwpl_task.delay()

async def trigger_eod_bhavcopy_eq():
    from backend.ingest.tasks import import_nse_latest
    import_nse_latest.delay(modules=["bhavcopy_eq"])

async def trigger_eod_bhavcopy_fo():
    from backend.ingest.tasks import import_nse_latest
    import_nse_latest.delay(modules=["bhavcopy_fo"])

async def trigger_eod_board_meetings():
    from backend.ingest.tasks import import_nse_latest
    import_nse_latest.delay(modules=["board_meetings"])

async def trigger_eod_fii():
    from backend.ingest.tasks import import_fii_stats_task
    import_fii_stats_task.delay()

JOB_HANDLERS = {
    "Corporate Announcements": trigger_corporate_announcements,
    "Live Corporate Actions": trigger_live_actions,
    "MWPL Import": trigger_mwpl,
    "EOD Bhavcopy EQ": trigger_eod_bhavcopy_eq,
    "EOD Bhavcopy FO": trigger_eod_bhavcopy_fo,
    "EOD Board Meetings": trigger_eod_board_meetings,
    "EOD FII Stats": trigger_eod_fii
}

def fetch_configs():
    db = SessionLocal()
    try:
        return db.query(CronJobConfig).filter(CronJobConfig.is_active == True).all()
    finally:
        db.close()

def update_last_run_db(job_name, run_time):
    db = SessionLocal()
    try:
        config = db.query(CronJobConfig).filter(CronJobConfig.job_name == job_name).first()
        if config:
            config.last_run = run_time
            db.commit()
    except Exception as e:
        logger.error(f"Error updating last_run for {job_name}: {e}")
        db.rollback()
    finally:
        db.close()

def _init_default_jobs():
    db = SessionLocal()
    try:
        default_jobs = [
            {"job_name": "Corporate Announcements", "is_active": False, "interval_seconds": 30, "run_time": None},
            {"job_name": "Live Corporate Actions", "is_active": False, "interval_seconds": 30, "run_time": None},
            {"job_name": "MWPL Import", "is_active": False, "interval_seconds": None, "run_time": "11:00"},
            {"job_name": "EOD Bhavcopy EQ", "is_active": False, "interval_seconds": None, "run_time": "19:00"},
            {"job_name": "EOD Bhavcopy FO", "is_active": False, "interval_seconds": None, "run_time": "19:00"},
            {"job_name": "EOD Board Meetings", "is_active": False, "interval_seconds": None, "run_time": "19:00"},
            {"job_name": "EOD FII Stats", "is_active": False, "interval_seconds": None, "run_time": "19:00"}
        ]

        for job in default_jobs:
            existing = db.query(CronJobConfig).filter(CronJobConfig.job_name == job["job_name"]).first()
            if not existing:
                db.add(CronJobConfig(**job))

        db.commit()
    except Exception as e:
        logger.error(f"Error initializing cron jobs: {e}")
        db.rollback()
    finally:
        db.close()

async def start_cron_manager():
    logger.info("Starting Cron Manager Loop...")

    # Initialize default jobs if not present safely in a thread
    await asyncio.to_thread(_init_default_jobs)

    while True:
        try:
            # We use a non-blocking asyncio loop to monitor configurations.
            # This is lightweight and avoids complex Celery Beat setups just for dynamic UI-controlled intervals.
            # Run DB queries safely using to_thread to prevent blocking the event loop
            configs = await asyncio.to_thread(fetch_configs)

            now = datetime.now()

            for config in configs:
                job_name = config.job_name

                # Check interval-based execution
                if config.interval_seconds:
                    # Enforce quiet hours (8:00 PM to 8:00 AM) for 24x7 corporate data streams
                    if job_name in ["Corporate Announcements", "Live Corporate Actions"]:
                        current_hour = now.hour
                        # If time is >= 20:00 (8 PM) or < 8:00 (8 AM), skip execution
                        if current_hour >= 20 or current_hour < 8:
                            continue

                    last_run = _last_run_times.get(job_name, datetime.min)

                    if (now - last_run).total_seconds() >= config.interval_seconds:
                        _last_run_times[job_name] = now
                        await asyncio.to_thread(update_last_run_db, job_name, now)
                        if job_name in JOB_HANDLERS:
                            # Fire and forget
                            asyncio.create_task(JOB_HANDLERS[job_name]())

                # Check time-based execution
                elif config.run_time:
                    try:
                        target_time = datetime.strptime(config.run_time, "%H:%M").time()
                        last_run = _last_run_times.get(job_name)

                        if now.time() >= target_time:
                            if not last_run or last_run.date() < now.date():
                                _last_run_times[job_name] = now
                                await asyncio.to_thread(update_last_run_db, job_name, now)
                                if job_name in JOB_HANDLERS:
                                    asyncio.create_task(JOB_HANDLERS[job_name]())
                    except ValueError:
                        logger.error(f"Invalid run_time format for {job_name}: {config.run_time}. Expects HH:MM")

        except Exception as e:
            logger.error(f"Error in cron manager loop: {e}\n{traceback.format_exc()}")

        await asyncio.sleep(5)
