from celery import Celery, shared_task
from celery.utils.log import get_task_logger
from datetime import datetime, date, timedelta
from typing import Any, List, Optional
import time

from backend.ingest.nse_importer import NSEDataImporter
from backend.ingest.date_utils import NSEHolidayCalendar

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

@shared_task(bind=True, name='backend.ingest.tasks.import_nse_range')
def import_nse_range(self, start_date_str: str, end_date_str: str, patterns: Optional[List[str]] = None):
    """Import NSE data for a range of dates."""
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

        importer = NSEDataImporter()
        current_date = start_date
        results = []

        total_days = (end_date - start_date).days + 1
        processed_days = 0

        while current_date <= end_date:
            if NSEHolidayCalendar.is_trading_day(current_date):
                # Update task state for range progress
                self.update_state(state='PROGRESS', meta={
                    'current_date': current_date.isoformat(),
                    'percent': int((processed_days / total_days) * 100),
                    'status': f'Processing {current_date}'
                })

                # Import for this day
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

        logger.info(f"Auto-importing for latest trading day: {target_date}")
        return importer.import_date(target_date, patterns=patterns, progress_callback=progress_callback)

    except Exception as exc:
        logger.error(f"Latest import failed: {exc}")
        self.retry(exc=exc, countdown=300)
