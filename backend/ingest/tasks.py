"""Celery Tasks for NSE Import"""
from datetime import datetime, date, timedelta
from typing import Any
from celery import shared_task

from backend.ingest.nse_importer import NSEDataImporter


@shared_task(bind=True, max_retries=3)
def import_nse_date(self, date_str: str, patterns: list[str] | None = None,
                   force: bool = False) -> dict[str, Any]:
    """Import NSE data for a specific date."""
    try:
        trade_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        importer = NSEDataImporter()

        # Define progress callback
        def progress_callback(progress_data: dict[str, Any]):
            self.update_state(state='PROGRESS', meta=progress_data)

        return importer.import_date(trade_date, patterns=patterns, force=force, progress_callback=progress_callback)
    except Exception as exc:
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

        while current <= end:
            if importer.holidays.is_trading_day(current):
                # Update task state for day start
                self.update_state(state='PROGRESS', meta={
                    'current_file': f"Processing date: {current}",
                    'progress': int((days_processed / total_days) * 100),
                    'files_completed': [r['date'] for r in results]
                })

                # We don't pass callback here to avoid spamming updates for every file in every day
                # Or we could, but let's stick to daily granularity for range import to reduce message load
                result = importer.import_date(current, patterns=patterns)
                results.append({'date': current.isoformat(), **result})

            current += timedelta(days=1)
            days_processed += 1

        return {'range': {'start': start_date, 'end': end_date}, 'results': results}
    except Exception as exc:
        if isinstance(exc, (ConnectionError, TimeoutError)):
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        raise


@shared_task(bind=True)
def import_nse_latest(self, patterns: list[str] | None = None) -> dict[str, Any]:
    """Import data for the most recent trading day."""
    try:
        importer = NSEDataImporter()
        yesterday = date.today() - timedelta(days=1)
        trade_date = importer.holidays.get_previous_trading_day(yesterday)

        # Define progress callback
        def progress_callback(progress_data: dict[str, Any]):
            self.update_state(state='PROGRESS', meta=progress_data)

        return importer.import_date(trade_date, patterns=patterns, progress_callback=progress_callback)
    except Exception as e:
        return {'status': 'ERROR', 'error': str(e)}


@shared_task
def setup_timescale_policies() -> dict[str, Any]:
    """Initialize TimescaleDB hypertables and policies."""
    try:
        importer = NSEDataImporter()
        return importer.setup_timescale()
    except Exception as e:
        return {'status': 'ERROR', 'error': str(e)}
