"""Celery Tasks for NSE Import"""
from datetime import datetime, date, timedelta
from typing import Any
from celery import shared_task
from celery.utils.log import get_task_logger

from backend.ingest.nse_importer import NSEDataImporter

logger = get_task_logger(__name__)

@shared_task(bind=True, max_retries=3)
def import_nse_date(self, date_str: str, patterns: list[str] | None = None,
                   force: bool = False) -> dict[str, Any]:
    """Import NSE data for a specific date."""

    def progress_callback(progress_dict: dict[str, Any]):
        """Update Celery task state"""
        self.update_state(state='PROGRESS', meta=progress_dict)
        logger.info(f"Progress: {progress_dict.get('percent', 0)}% - {progress_dict.get('current_file', '')}")

    try:
        trade_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        importer = NSEDataImporter()

        logger.info(f"Starting import task for {trade_date}")
        return importer.import_date(trade_date, patterns=patterns, force=force, progress_callback=progress_callback)
    except Exception as exc:
        logger.error(f"Import task failed: {exc}")
        if isinstance(exc, (ConnectionError, TimeoutError)):
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        raise


@shared_task(bind=True, max_retries=3)
def import_nse_range(self, start_date: str, end_date: str,
                    patterns: list[str] | None = None) -> dict[str, Any]:
    """Import NSE data for a date range."""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        importer = NSEDataImporter()

        results = []
        current = start

        # Helper for overall progress
        total_days = (end - start).days + 1
        days_processed = 0

        logger.info(f"Starting range import from {start} to {end} ({total_days} days)")

        while current <= end:
            if importer.holidays.is_trading_day(current):
                percent = int((days_processed / total_days) * 100)

                # Update task state for day start
                meta = {
                    'current_file': f"Processing date: {current}",
                    'progress': percent,
                    'files_completed': [r['date'] for r in results],
                    'status': 'in_progress'
                }
                self.update_state(state='PROGRESS', meta=meta)
                logger.info(f"Range Progress: {percent}% - Processing {current}")

                # We don't pass callback here to avoid spamming updates for every file in every day
                result = importer.import_date(current, patterns=patterns)
                results.append({'date': current.isoformat(), **result})

            current += timedelta(days=1)
            days_processed += 1

        return {'range': {'start': start_date, 'end': end_date}, 'results': results}
    except Exception as exc:
        logger.error(f"Range import failed: {exc}")
        if isinstance(exc, (ConnectionError, TimeoutError)):
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        raise


@shared_task(bind=True)
def import_nse_latest(self, patterns: list[str] | None = None) -> dict[str, Any]:
    """Import data for the most recent trading day."""

    def progress_callback(progress_dict: dict[str, Any]):
        """Update Celery task state"""
        self.update_state(state='PROGRESS', meta=progress_dict)
        logger.info(f"Latest Import Progress: {progress_dict.get('percent', 0)}%")

    try:
        importer = NSEDataImporter()
        yesterday = date.today() - timedelta(days=1)
        trade_date = importer.holidays.get_previous_trading_day(yesterday)

        logger.info(f"Starting latest import for {trade_date}")
        return importer.import_date(trade_date, patterns=patterns, progress_callback=progress_callback)
    except Exception as e:
        logger.error(f"Latest import failed: {e}")
        return {'status': 'ERROR', 'error': str(e)}


@shared_task
def setup_timescale_policies() -> dict[str, Any]:
    """Initialize TimescaleDB hypertables and policies."""
    try:
        importer = NSEDataImporter()
        return importer.setup_timescale()
    except Exception as e:
        return {'status': 'ERROR', 'error': str(e)}
