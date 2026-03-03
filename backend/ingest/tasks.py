from celery import Celery, shared_task
from celery.utils.log import get_task_logger
from datetime import datetime, date, timedelta
from typing import Any, List, Optional
import time

from backend.ingest.nse_importer import NSEDataImporter
from backend.ingest.date_utils import NSEHolidayCalendar
from backend.ingest.nse_models import ImportLog
from backend.infrastructure.db import SessionLocal

logger = get_task_logger(__name__)

# Use shared_task decorator for integration with main Celery app
@shared_task(bind=True, name='backend.ingest.tasks.import_nse_date')
def import_nse_date(self, date_str: str, patterns: Optional[List[str]] = None, force: bool = False):
    """Import NSE data for a specific date."""

    # Progress callback to update Celery state
    def progress_callback(progress_dict: dict):
        self.update_state(state='PROGRESS', meta=progress_dict)
        logger.info(f"Task Progress: {progress_dict}")

    try:
        if isinstance(date_str, str):
            trade_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            trade_date = date_str

        logger.info(f"Starting import for {trade_date}")
        importer = NSEDataImporter()
        result = importer.import_date(
            trade_date,
            patterns=patterns,
            force=force,
            progress_callback=progress_callback
        )
        return result

    except Exception as exc:
        logger.error(f"Import failed: {exc}")
        self.retry(exc=exc, countdown=60)  # Retry after 1 min on failure

from celery import shared_task

@shared_task(bind=True, name="evaluate_ai_predictions")
def evaluate_ai_predictions(self):
    """
    Background worker that runs (e.g., at 9:15 AM) to evaluate all pending AI predictions
    by fetching the latest actual opening price and calculating accuracy.
    """
    from backend.infrastructure.db import SessionLocal
    from backend.ingest.nse_models import AIPrediction, BhavcopyEQ
    from sqlalchemy import select, desc

    db = SessionLocal()
    try:
        # Find all predictions without an actual_price
        pending = db.query(AIPrediction).filter(AIPrediction.actual_price.is_(None)).all()
        updated_count = 0

        for pred in pending:
            # Look up the latest open price for the ticker
            latest_eq = db.execute(
                select(BhavcopyEQ.open_price)
                .filter(BhavcopyEQ.symbol == pred.ticker)
                .order_by(desc(BhavcopyEQ.trade_date))
                .limit(1)
            ).scalar_one_or_none()

            if latest_eq:
                pred.actual_price = latest_eq
                updated_count += 1

        if updated_count > 0:
            db.commit()

        return {"status": "SUCCESS", "evaluated_count": updated_count}
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


@shared_task(bind=True, name='backend.ingest.tasks.import_nse_range')
def import_nse_range(self, start_date_str: str, end_date_str: str, patterns: Optional[List[str]] = None):
    """Import NSE data for a range of dates. Optimized to skip fully completed dates."""
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

        importer = NSEDataImporter()
        current_date = start_date
        results = []

        total_days = (end_date - start_date).days + 1
        processed_days = 0

        # Define default patterns if none provided (must match what import_date uses)
        default_patterns = [
            'bhavcopy_eq', 'bhavcopy_fo', 'fao_participant_oi', 'fo_volatility',
            'block_deals', 'bulk_deals', 'fii_derivatives_stats', 'mto', 'mwpl_cli'
        ]
        target_patterns = patterns if patterns else default_patterns

        # Pre-check database for completed dates to optimize range import
        # We can do this efficiently by querying the ImportLog table
        db = SessionLocal()
        from sqlalchemy import or_
        try:
             # Find all successful imports in range for requested tables that ACTUALLY have data
             completed_logs = db.query(ImportLog.import_date, ImportLog.table_name).filter(
                 ImportLog.import_date >= start_date,
                 ImportLog.import_date <= end_date,
                 ImportLog.table_name.in_(target_patterns),
                 ImportLog.status == 'SUCCESS',
                 or_(ImportLog.rows_inserted > 0, ImportLog.rows_updated > 0)
             ).all()

             # Map date -> set of completed tables
             completed_map = {}
             for d, t in completed_logs:
                 if d not in completed_map: completed_map[d] = set()
                 completed_map[d].add(t)

        except Exception as e:
            logger.warning(f"Optimization check failed: {e}. Proceeding with standard check.")
            completed_map = {}
        finally:
            db.close()

        while current_date <= end_date:
            if NSEHolidayCalendar.is_trading_day(current_date):

                # OPTIMIZATION: Check if all requested patterns are already done for this date
                is_fully_done = False
                if current_date in completed_map:
                    done_tables = completed_map[current_date]
                    # Check if all target patterns are in done_tables
                    # Note: Using set subset check
                    if set(target_patterns).issubset(done_tables):
                        is_fully_done = True

                if is_fully_done:
                    logger.info(f"Skipping {current_date} (All requested files already imported)")
                    # Mock a skipped result for consistency
                    results.append({
                        'status': 'SKIPPED',
                        'date': current_date.isoformat(),
                        'reason': 'Fully completed previously'
                    })

                    # Update progress even if skipping
                    self.update_state(state='PROGRESS', meta={
                        'current_date': current_date.isoformat(),
                        'percent': int((processed_days / total_days) * 100),
                        'status': f'Skipping {current_date} (Done)'
                    })
                else:
                    # Update task state for range progress
                    self.update_state(state='PROGRESS', meta={
                        'current_date': current_date.isoformat(),
                        'percent': int((processed_days / total_days) * 100),
                        'status': f'Processing {current_date}'
                    })

                    # Import for this day (importer will still do file-level checks, but we saved task overhead if fully done)
                    day_result = importer.import_date(current_date, patterns=patterns)
                    results.append(day_result)

            current_date += timedelta(days=1)
            processed_days += 1

        return {'range': f"{start_date_str} to {end_date_str}", 'results': results}

    except Exception as exc:
        logger.error(f"Range import failed: {exc}")
        self.retry(exc=exc, countdown=60)

@shared_task(bind=True, name='backend.ingest.tasks.import_nse_latest')
def import_nse_latest(self, patterns: Optional[List[str]] = None):
    """Import data for the most recent trading day."""

    def progress_callback(progress_dict: dict):
        self.update_state(state='PROGRESS', meta=progress_dict)

    try:
        importer = NSEDataImporter()
        # Find last trading day using IST
        utc_now = datetime.utcnow()
        ist_now = utc_now + timedelta(hours=5, minutes=30)
        today = ist_now.date()

        # If after 18:00 IST, consider today as potential trading day (data usually available)
        # Else consider previous day
        cutoff_time = 18  # 6 PM IST

        if ist_now.hour >= cutoff_time:
            # Check if today is trading day
            if NSEHolidayCalendar.is_trading_day(today):
                target_date = today
            else:
                target_date = NSEHolidayCalendar.get_previous_trading_day(today)
        else:
            # Before 6 PM, today's data not ready, so look for previous trading day
            target_date = NSEHolidayCalendar.get_previous_trading_day(today)

        logger.info(f"Auto-importing for latest trading day: {target_date} (IST: {ist_now})")
        return importer.import_date(target_date, patterns=patterns, progress_callback=progress_callback)

    except Exception as exc:
        logger.error(f"Latest import failed: {exc}")
        self.retry(exc=exc, countdown=300)
