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
_last_sleep_log_times = {}

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
    import_nse_latest.delay(patterns=["bhavcopy_eq"])

async def trigger_eod_bhavcopy_fo():
    from backend.ingest.tasks import import_nse_latest
    import_nse_latest.delay(patterns=["bhavcopy_fo"])

async def trigger_eod_board_meetings():
    from backend.ingest.tasks import import_nse_latest
    import_nse_latest.delay(patterns=["board_meetings"])

async def trigger_eod_fii():
    from backend.ingest.tasks import import_fii_stats_task
    import_fii_stats_task.delay()

async def trigger_eod_fao_participant_oi():
    from backend.ingest.tasks import import_nse_latest
    import_nse_latest.delay(patterns=["fao_participant_oi"])

async def trigger_eod_fo_volatility():
    from backend.ingest.tasks import import_nse_latest
    import_nse_latest.delay(patterns=["fo_volatility"])

async def trigger_eod_block_deals():
    from backend.ingest.tasks import import_nse_latest
    import_nse_latest.delay(patterns=["block_deals"])

async def trigger_eod_bulk_deals():
    from backend.ingest.tasks import import_nse_latest
    import_nse_latest.delay(patterns=["bulk_deals"])

async def trigger_eod_fii_derivatives_stats():
    from backend.ingest.tasks import import_nse_latest
    import_nse_latest.delay(patterns=["fii_derivatives_stats"])

async def trigger_eod_mto():
    from backend.ingest.tasks import import_nse_latest
    import_nse_latest.delay(patterns=["mto"])

async def trigger_eod_mwpl_cli():
    from backend.ingest.tasks import import_nse_latest
    import_nse_latest.delay(patterns=["mwpl_cli"])

async def trigger_eod_pe_ratio():
    from backend.ingest.tasks import import_nse_latest
    import_nse_latest.delay(patterns=["pe_ratio"])

async def trigger_eod_pe_ratio_idx():
    from backend.ingest.tasks import import_nse_latest
    import_nse_latest.delay(patterns=["pe_ratio_idx"])

async def trigger_eod_india_vix():
    from backend.ingest.tasks import import_nse_latest
    import_nse_latest.delay(patterns=["india_vix"])

async def trigger_eod_var_stats():
    from backend.ingest.tasks import import_nse_latest
    import_nse_latest.delay(patterns=["var_stats"])

async def trigger_eod_contract_delta():
    from backend.ingest.tasks import import_nse_latest
    import_nse_latest.delay(patterns=["contract_delta"])

async def trigger_eod_margin_trading():
    from backend.ingest.tasks import import_nse_latest
    import_nse_latest.delay(patterns=["margin_trading"])

async def trigger_eod_corporate_actions():
    from backend.ingest.tasks import import_nse_latest
    import_nse_latest.delay(patterns=["corporate_actions"])

async def trigger_eod_nse_security():
    from backend.ingest.tasks import import_nse_latest
    import_nse_latest.delay(patterns=["nse_security"])

async def trigger_eod_fii_dii_cash():
    from backend.ingest.tasks import import_nse_latest
    import_nse_latest.delay(patterns=["fii_dii_cash"])

async def trigger_eod_historical_index_data():
    from backend.ingest.tasks import import_nse_latest
    import_nse_latest.delay(patterns=["historical_index_data"])

async def trigger_eod_financial_results():
    from backend.ingest.tasks import import_nse_latest
    import_nse_latest.delay(patterns=["financial_results"])


JOB_HANDLERS = {
    "Corporate Announcements": trigger_corporate_announcements,
    "Live Corporate Actions": trigger_live_actions,
    "MWPL Import": trigger_mwpl,
    "EOD Bhavcopy EQ": trigger_eod_bhavcopy_eq,
    "EOD Bhavcopy FO": trigger_eod_bhavcopy_fo,
    "EOD Board Meetings": trigger_eod_board_meetings,
    "EOD FII Stats": trigger_eod_fii,
    "EOD FAO Participant OI": trigger_eod_fao_participant_oi,
    "EOD FO Volatility": trigger_eod_fo_volatility,
    "EOD Block Deals": trigger_eod_block_deals,
    "EOD Bulk Deals": trigger_eod_bulk_deals,
    "EOD FII Derivatives Stats": trigger_eod_fii_derivatives_stats,
    "EOD MTO": trigger_eod_mto,
    "EOD MWPL CLI": trigger_eod_mwpl_cli,
    "EOD PE Ratio": trigger_eod_pe_ratio,
    "EOD PE Ratio Index": trigger_eod_pe_ratio_idx,
    "EOD India VIX": trigger_eod_india_vix,
    "EOD VAR Stats": trigger_eod_var_stats,
    "EOD Contract Delta": trigger_eod_contract_delta,
    "EOD Margin Trading": trigger_eod_margin_trading,
    "EOD Corporate Actions": trigger_eod_corporate_actions,
    "EOD NSE Security": trigger_eod_nse_security,
    "EOD FII DII Cash": trigger_eod_fii_dii_cash,
    "EOD Historical Index Data": trigger_eod_historical_index_data,
    "EOD Financial Results": trigger_eod_financial_results
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
            {"job_name": "EOD FII Stats", "is_active": False, "interval_seconds": None, "run_time": "19:00"},
            {"job_name": "EOD FAO Participant OI", "is_active": False, "interval_seconds": None, "run_time": "19:00"},
            {"job_name": "EOD FO Volatility", "is_active": False, "interval_seconds": None, "run_time": "19:00"},
            {"job_name": "EOD Block Deals", "is_active": False, "interval_seconds": None, "run_time": "19:00"},
            {"job_name": "EOD Bulk Deals", "is_active": False, "interval_seconds": None, "run_time": "19:00"},
            {"job_name": "EOD FII Derivatives Stats", "is_active": False, "interval_seconds": None, "run_time": "19:00"},
            {"job_name": "EOD MTO", "is_active": False, "interval_seconds": None, "run_time": "19:00"},
            {"job_name": "EOD MWPL CLI", "is_active": False, "interval_seconds": None, "run_time": "19:00"},
            {"job_name": "EOD PE Ratio", "is_active": False, "interval_seconds": None, "run_time": "19:00"},
            {"job_name": "EOD PE Ratio Index", "is_active": False, "interval_seconds": None, "run_time": "19:00"},
            {"job_name": "EOD India VIX", "is_active": False, "interval_seconds": None, "run_time": "19:00"},
            {"job_name": "EOD VAR Stats", "is_active": False, "interval_seconds": None, "run_time": "19:00"},
            {"job_name": "EOD Contract Delta", "is_active": False, "interval_seconds": None, "run_time": "19:00"},
            {"job_name": "EOD Margin Trading", "is_active": False, "interval_seconds": None, "run_time": "19:00"},
            {"job_name": "EOD Corporate Actions", "is_active": False, "interval_seconds": None, "run_time": "19:00"},
            {"job_name": "EOD NSE Security", "is_active": False, "interval_seconds": None, "run_time": "19:00"},
            {"job_name": "EOD FII DII Cash", "is_active": False, "interval_seconds": None, "run_time": "19:00"},
            {"job_name": "EOD Historical Index Data", "is_active": False, "interval_seconds": None, "run_time": "19:00"},
            {"job_name": "EOD Financial Results", "is_active": False, "interval_seconds": None, "run_time": "19:00"}
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

    # Check for missing days (Option A: Automatically check database on boot)
    # By doing this in start_cron_manager, we avoid the FastAPI multi-worker duplicate trigger problem.
    try:
        from backend.infrastructure.db import SessionLocal
        from backend.ingest.nse_models import ImportLog
        from sqlalchemy import func
        from datetime import datetime, timedelta
        import pytz

        db = SessionLocal()
        ist = pytz.timezone('Asia/Kolkata')
        today = datetime.now(ist).date()

        # Check last successful import for core EOD table
        last_log = db.query(func.max(ImportLog.import_date)).filter(
            ImportLog.table_name == 'bhavcopy_fo',
            ImportLog.status == 'SUCCESS'
        ).scalar()

        db.close()

        if last_log and last_log < today - timedelta(days=1):
            logger.info(f"Missed days detected! Last import was {last_log}. Dispatching backfill task...")
            from backend.ingest.tasks import import_nse_latest
            import_nse_latest.delay()
    except Exception as e:
        logger.error(f"Failed to check for missed days on startup: {e}")


    while True:
        try:
            # We use a non-blocking asyncio loop to monitor configurations.
            # This is lightweight and avoids complex Celery Beat setups just for dynamic UI-controlled intervals.
            # Run DB queries safely using to_thread to prevent blocking the event loop
            configs = await asyncio.to_thread(fetch_configs)

            utc_now = datetime.utcnow()
            now = utc_now + __import__('datetime').timedelta(hours=5, minutes=30)

            for config in configs:
                job_name = config.job_name

                # Check interval-based execution
                if config.interval_seconds:
                    # Enforce configurable quiet hours for continuous streams
                    if config.pause_start and config.pause_end:
                        try:
                            start_time = datetime.strptime(config.pause_start, "%H:%M").time()
                            end_time = datetime.strptime(config.pause_end, "%H:%M").time()
                            current_time = now.time()

                            if start_time < end_time:
                                # Pause window is within the same day
                                if start_time <= current_time <= end_time:
                                    if job_name not in _last_sleep_log_times or (now - _last_sleep_log_times[job_name]).total_seconds() > 3600:
                                        logger.info(f"System is in sleep mode for {job_name}. Outside cron/market hours.")
                                        _last_sleep_log_times[job_name] = now
                                    continue
                            else:
                                # Pause window crosses midnight (e.g. 20:00 to 08:00)
                                if current_time >= start_time or current_time <= end_time:
                                    if job_name not in _last_sleep_log_times or (now - _last_sleep_log_times[job_name]).total_seconds() > 3600:
                                        logger.info(f"System is in sleep mode for {job_name}. Outside cron/market hours.")
                                        _last_sleep_log_times[job_name] = now
                                    continue
                        except ValueError:
                            pass # Fallback if invalid time format

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
