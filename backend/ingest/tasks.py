"""Celery Tasks for NSE Import"""
from datetime import datetime, date, timedelta
from typing import Optional, List
from celery import shared_task

from backend.ingest.nse_importer import NSEDataImporter


@shared_task(bind=True, max_retries=3)
def import_nse_date(self, date_str: str, patterns: Optional[List[str]] = None,
                   force: bool = False) -> dict:
    """Import NSE data for a specific date."""
    try:
        trade_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        importer = NSEDataImporter()
        return importer.import_date(trade_date, patterns=patterns, force=force)
    except Exception as exc:
        if isinstance(exc, (ConnectionError, TimeoutError)):
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        raise


@shared_task(bind=True, max_retries=3)
def import_nse_range(self, start_date: str, end_date: str,
                    patterns: Optional[List[str]] = None) -> dict:
    """Import NSE data for a date range."""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        importer = NSEDataImporter()

        results = []
        current = start
        while current <= end:
            if importer.holidays.is_trading_day(current):
                result = importer.import_date(current, patterns=patterns)
                results.append({'date': current.isoformat(), **result})
            current += timedelta(days=1)

        return {'range': {'start': start_date, 'end': end_date}, 'results': results}
    except Exception as exc:
        if isinstance(exc, (ConnectionError, TimeoutError)):
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        raise


@shared_task
def import_nse_latest(patterns: Optional[List[str]] = None) -> dict:
    """Import data for the most recent trading day."""
    try:
        importer = NSEDataImporter()
        yesterday = date.today() - timedelta(days=1)
        trade_date = importer.holidays.get_previous_trading_day(yesterday)
        return importer.import_date(trade_date, patterns=patterns)
    except Exception as e:
        return {'status': 'ERROR', 'error': str(e)}


@shared_task
def setup_timescale_policies() -> dict:
    """Initialize TimescaleDB hypertables and policies."""
    try:
        importer = NSEDataImporter()
        return importer.setup_timescale()
    except Exception as e:
        return {'status': 'ERROR', 'error': str(e)}
