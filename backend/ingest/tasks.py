from celery import shared_task
from celery.utils.log import get_task_logger
from datetime import datetime, timedelta
from typing import List, Optional

from backend.ingest.nse_importer import NSEDataImporter
from backend.ingest.date_utils import NSEHolidayCalendar
from backend.ingest.nse_models import ImportLog
from backend.infrastructure.db import SessionLocal
import redis
import os

logger = get_task_logger(__name__)


def check_pause_flag(task_id: str) -> bool:
    import redis
    import os
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url)
        return r.exists(f"pause_task_{task_id}") > 0
    except Exception:
        return False


def set_active_task(task_id: str):
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url)
        r.set("active_import_task_id", task_id)
    except Exception:
        pass

def clear_active_task(task_id: str):
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url)
        # Only delete if it's the current task
        curr = r.get("active_import_task_id")
        if curr and curr.decode('utf-8') == task_id:
            r.delete("active_import_task_id")
    except Exception:
        pass

def check_cancel_flag(task_id: str) -> bool:
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url)
        return r.exists(f"cancel_task_{task_id}") > 0
    except Exception:
        return False

# Use shared_task decorator for integration with main Celery app
@shared_task(bind=True, max_retries=3, acks_late=True, name='backend.ingest.tasks.import_nse_date')
def import_nse_date(self, date_str: str, patterns: Optional[List[str]] = None, force: bool = False, include_non_fo: bool = False, specific_symbol: Optional[str] = None):
    """Import NSE data for a specific date."""
    set_active_task(self.request.id)

    # Progress callback to update Celery state
    def progress_callback(progress_dict: dict):
        self.update_state(state='PROGRESS', meta=progress_dict)
        handle_pause()
        logger.info(f"Task Progress: {progress_dict}")
        handle_pause()

    def is_cancelled():
        return check_cancel_flag(self.request.id)

    def handle_pause():
        import time
        if check_pause_flag(self.request.id):
            self.update_state(state='PROGRESS', meta={'status': 'PAUSED', 'message': 'Task is paused. Waiting to resume...'})
            while check_pause_flag(self.request.id):
                if is_cancelled():
                    break
                time.sleep(5)
            self.update_state(state='PROGRESS', meta={'status': 'RESUMED', 'message': 'Task resumed.'})

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
            progress_callback=progress_callback,
            check_cancel=is_cancelled,
            include_non_fo=include_non_fo,
            specific_symbol=specific_symbol
        )
        if result.get('status') == 'ABORTED':
            self.update_state(state='REVOKED', meta={'exc_type': 'Abort', 'exc_message': 'Aborted by user'})
            return {"status": "ABORTED"}
        clear_active_task(self.request.id)
        return result

    except Exception as exc:
        if self.request.retries >= self.max_retries:
            err_msg = str(exc)
            logger.error(f"Max retries exceeded for date import: {err_msg}")
            self.update_state(state='FAILURE', meta={"exc_type": "Exception", "exc_message": f"Date Import Failed: {err_msg}"})
            raise Exception(f"Date Import Failed: {err_msg}")

        logger.error(f"Import failed: {exc}. Retrying... ({self.request.retries}/3)")
        self.retry(exc=Exception(str(exc)), countdown=60)  # Convert complex exceptions to string explicitly before retry

from celery import shared_task

@shared_task(bind=True, acks_late=True, name="evaluate_ai_predictions")
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


@shared_task(bind=True, max_retries=3, acks_late=True, name='backend.ingest.tasks.retry_failed_imports')
def retry_failed_imports(self, pattern: str):
    """Retry all failed dates for a specific table pattern."""
    set_active_task(self.request.id)

    def is_cancelled():
        return check_cancel_flag(self.request.id)

    def handle_pause():
        import time
        if check_pause_flag(self.request.id):
            self.update_state(state='PROGRESS', meta={'status': 'PAUSED', 'message': 'Task is paused. Waiting to resume...'})
            while check_pause_flag(self.request.id):
                if is_cancelled():
                    break
                time.sleep(5)
            self.update_state(state='PROGRESS', meta={'status': 'RESUMED', 'message': 'Task resumed.'})

    try:
        from backend.infrastructure.db import SessionLocal
        from backend.models.audit import SystemLog

        db = SessionLocal()

        # In the audit logs, successful jobs record "Imported <pattern> for <date>"
        # Failed jobs record "Failed to import <pattern> for <date>" or similar,
        # but in our frontend stats endpoint we use the fact that they have level='ERROR'.
        # However, a cleaner way is just to rely on the backend stats query logic or query the DB directly.
        # But for robustness, we can just fetch all dates that have an ERROR for this pattern
        # and do NOT have a subsequent SUCCESS.

        from sqlalchemy import text
        # Simplest approach: Query the exact same `get_import_stats` SQL logic, or just a custom SQL
        sql = text("""
            SELECT DISTINCT (meta_data->>'date')::date AS error_date
            FROM system_logs
            WHERE source = 'Importer'
            AND level = 'ERROR'
            AND meta_data->>'pattern' = :pattern
            AND (meta_data->>'date') IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM system_logs success_logs
                WHERE success_logs.source = 'Importer'
                AND success_logs.level = 'INFO'
                AND success_logs.meta_data->>'pattern' = :pattern
                AND success_logs.meta_data->>'date' = system_logs.meta_data->>'date'
                AND success_logs.timestamp > system_logs.timestamp
            )
            ORDER BY error_date ASC;
        """)

        failed_dates_rows = db.execute(sql, {'pattern': pattern}).fetchall()
        failed_dates = [row[0] for row in failed_dates_rows]
        db.close()

        if not failed_dates:
            clear_active_task(self.request.id)
            return {'status': 'SUCCESS', 'message': f'No failed dates found for {pattern}'}

        total_days = len(failed_dates)
        processed_days = 0
        results = []

        importer = NSEDataImporter()

        for current_date in failed_dates:
            if is_cancelled():
                self.update_state(state='REVOKED', meta={'exc_type': 'Abort', 'exc_message': 'Aborted by user'})
                return {"status": "ABORTED", 'range': f"Retrying {pattern}", 'results': results}

            handle_pause()

            self.update_state(state='PROGRESS', meta={
                'current_date': current_date.isoformat(),
                'percent': int((processed_days / total_days) * 100),
                'status': f'Retrying {current_date}'
            })

            day_result = importer.import_date(current_date, patterns=[pattern], force=True, check_cancel=is_cancelled)
            if day_result.get('status') == 'ABORTED':
                self.update_state(state='REVOKED', meta={'exc_type': 'Abort', 'exc_message': 'Aborted by user'})
                return {"status": "ABORTED", 'range': f"Retrying {pattern}", 'results': results}

            results.append(day_result)
            processed_days += 1

        clear_active_task(self.request.id)
        return {'range': f"Retried {total_days} failed dates for {pattern}", 'results': results}

    except Exception as exc:
        if self.request.retries >= self.max_retries:
            err_msg = str(exc)
            logger.error(f"Max retries exceeded for retry failed imports: {err_msg}")
            self.update_state(state='FAILURE', meta={"exc_type": "Exception", "exc_message": f"Retry Failed: {err_msg}"})
            raise Exception(f"Retry Failed: {err_msg}")

        logger.error(f"Retry failed: {exc}. Retrying... ({self.request.retries}/3)")
        self.retry(exc=Exception(str(exc)), countdown=60)


@shared_task(bind=True, max_retries=3, acks_late=True, name='backend.ingest.tasks.import_agms_range')
def import_agms_range(self, start_date_str: str, end_date_str: str):
    """Import standalone historical AGMs"""
    set_active_task(self.request.id)
    try:
        from backend.ingest.fetch_historical_agm import fetch_historical_agm_range
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

        self.update_state(state='PROGRESS', meta={'status': 'FETCHING_AGMS', 'message': f'Fetching AGMs from {start_date} to {end_date}...'})
        fetch_historical_agm_range(start_date, end_date)

        # Then sync databank
        build_dividend_databank_task.delay(force=False)
        return "AGM Import complete"
    except Exception as exc:
        logger.error(f"Error in AGM import: {exc}")
        self.retry(exc=Exception(str(exc)), countdown=60)

@shared_task(bind=True, max_retries=3, acks_late=True, name='backend.ingest.tasks.import_nse_range')
def import_nse_range(self, start_date_str: str, end_date_str: str, patterns: Optional[List[str]] = None, force: bool = False, include_non_fo: bool = False, specific_symbol: Optional[str] = None):
    """Import NSE data for a range of dates. Optimized to skip fully completed dates."""
    set_active_task(self.request.id)
    def is_cancelled():
        return check_cancel_flag(self.request.id)

    def handle_pause():
        import time
        if check_pause_flag(self.request.id):
            self.update_state(state='PROGRESS', meta={'status': 'PAUSED', 'message': 'Task is paused. Waiting to resume...'})
            while check_pause_flag(self.request.id):
                if is_cancelled():
                    break
                time.sleep(5)
            self.update_state(state='PROGRESS', meta={'status': 'RESUMED', 'message': 'Task resumed.'})

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
        completed_map = {}
        try:
            from backend.ingest.nse_models import ImportLog
            from sqlalchemy import and_

            logs = db.query(ImportLog).filter(
                and_(
                    ImportLog.import_date >= start_date,
                    ImportLog.import_date <= end_date,
                    ImportLog.status == 'SUCCESS'
                )
            ).all()

            for log in logs:
                if log.import_date not in completed_map:
                    completed_map[log.import_date] = set()
                completed_map[log.import_date].add(log.table_name)
        except Exception as e:
            logger.warning(f"Could not pre-fetch import logs: {e}")
        finally:
            db.close()

        from datetime import timedelta

        while current_date <= end_date:
            handle_pause()
            if is_cancelled():
                results.append(f"Task cancelled at date {current_date}")
                break

            # Skip weekends (NSE is closed, except for rare special sessions which we'll ignore for bulk)
            if current_date.weekday() >= 5 and not force:
                logger.info(f"Skipping weekend: {current_date}")
                current_date += timedelta(days=1)
                processed_days += 1
                self.update_state(state='PROGRESS', meta={
                    'current_date': current_date.strftime("%Y-%m-%d"),
                    'progress': int((processed_days / total_days) * 100),
                    'message': f"Skipped weekend {current_date - timedelta(days=1)}"
                })
                continue

            patterns_to_run = []
            if force:
                patterns_to_run = target_patterns
            else:
                completed_for_date = completed_map.get(current_date, set())
                for pat in target_patterns:
                    if pat not in completed_for_date:
                        patterns_to_run.append(pat)

            if not patterns_to_run:
                logger.info(f"All requested patterns already completed for {current_date}. Skipping.")
                results.append(f"{current_date}: Already completed")
            else:
                self.update_state(state='PROGRESS', meta={
                    'current_date': current_date.strftime("%Y-%m-%d"),
                    'progress': int((processed_days / total_days) * 100),
                    'message': f"Importing {current_date} ({len(patterns_to_run)} patterns)..."
                })

                try:
                    res = importer.import_date(current_date, patterns_to_run, force=force)
                    results.append(f"{current_date}: {res}")
                except Exception as e:
                    logger.error(f"Error importing {current_date}: {e}")
                    results.append(f"{current_date}: ERROR - {str(e)}")

            current_date += timedelta(days=1)
            processed_days += 1

            self.update_state(state='PROGRESS', meta={
                'current_date': current_date.strftime("%Y-%m-%d"),
                'progress': int((processed_days / total_days) * 100),
                'message': f"Completed {current_date - timedelta(days=1)}"
            })

        # Clear Active Task
        clear_active_task(self.request.id)

        # Trigger databank rebuild now that import is done
        build_dividend_databank_task.delay(force=True)

        return f"Range import finished: {start_date} to {end_date}. Details: {len(results)} days processed."
    except Exception as e:
        logger.error(f"Error in range import: {e}")
        clear_active_task(self.request.id)
        raise


@shared_task(bind=True, max_retries=3, acks_late=True, name='backend.ingest.tasks.import_nse_latest')
def import_nse_latest(self, patterns: Optional[List[str]] = None, force: bool = False, include_non_fo: bool = False, specific_symbol: Optional[str] = None):
    """Import data for the most recent trading day."""
    set_active_task(self.request.id)

    def progress_callback(progress_dict: dict):
        self.update_state(state='PROGRESS', meta=progress_dict)
        handle_pause()

    def is_cancelled():
        return check_cancel_flag(self.request.id)

    def handle_pause():
        import time
        if check_pause_flag(self.request.id):
            self.update_state(state='PROGRESS', meta={'status': 'PAUSED', 'message': 'Task is paused. Waiting to resume...'})
            while check_pause_flag(self.request.id):
                if is_cancelled():
                    break
                time.sleep(5)
            self.update_state(state='PROGRESS', meta={'status': 'RESUMED', 'message': 'Task resumed.'})

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
        result = importer.import_date(target_date, patterns=patterns, force=force, progress_callback=progress_callback, check_cancel=is_cancelled, include_non_fo=include_non_fo, specific_symbol=specific_symbol)
        if result.get('status') == 'ABORTED':
            self.update_state(state='REVOKED', meta={'exc_type': 'Abort', 'exc_message': 'Aborted by user'})
            return {"status": "ABORTED"}
        clear_active_task(self.request.id)
        return result

    except Exception as exc:
        if self.request.retries >= self.max_retries:
            err_msg = str(exc)
            logger.error(f"Max retries exceeded for latest import: {err_msg}")
            self.update_state(state='FAILURE', meta={"exc_type": "Exception", "exc_message": f"Latest Import Failed: {err_msg}"})
            raise Exception(f"Latest Import Failed: {err_msg}")

        logger.error(f"Latest import failed: {exc}. Retrying... ({self.request.retries}/3)")
        self.retry(exc=Exception(str(exc)), countdown=300)

@shared_task(bind=True, acks_late=True, name="prepare_morning_data_task")
def prepare_morning_data_task(self, target_date_str: str, end_date_str: str = None):
    """
    Celery task to STRICTLY compute the DailyDerivativesAnalysis table.
    If end_date_str is provided, computes for the range [target_date_str, end_date_str].
    """
    from datetime import datetime
    from backend.infrastructure.db import SessionLocal
    from backend.analysis.toolbox.reports.morning_report import MorningReportCalculator

    start_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()

    results = []
    try:
        with SessionLocal() as db:
            calc = MorningReportCalculator(db)

            if end_date_str:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                from backend.ingest.nse_models import BhavcopyFO
                trading_dates = [d[0] for d in db.query(BhavcopyFO.trade_date).filter(
                    BhavcopyFO.trade_date >= start_date,
                    BhavcopyFO.trade_date <= end_date
                ).distinct().order_by(BhavcopyFO.trade_date.asc()).all()]

                for d in trading_dates:
                    res = calc.calculate_for_date(d)
                    results.append({"date": str(d), "result": res})
            else:
                calc_result = calc.calculate_for_date(start_date)
                results.append({"date": str(start_date), "result": calc_result})

        return {
            "status": "SUCCESS",
            "message": "Data preparation completed for range" if end_date_str else f"Data preparation completed for {target_date_str}",
            "metrics": results[-1] if not end_date_str else {"batch_processed": len(results)}
        }
    except Exception as e:
        err_msg = str(e)
        logger.error(f"Morning Report Preparation Failed: {err_msg}")
        import traceback
        traceback.print_exc()
        # Updating state explicitly with exc_type so it isn't swallowed and prevents Celery ValueError
        self.update_state(state='FAILURE', meta={"error": err_msg, "exc_type": "Exception", "exc_message": err_msg})
        raise Exception(f"Morning Report Preparation Failed: {err_msg}")

@shared_task(bind=True, acks_late=True, name="generate_morning_report_task")
def generate_morning_report_task(self, target_date_str: str, author: str = "System", logo_path: str = None):
    """
    Celery task to STRICTLY generate the PDF report (after prepare_morning_data_task is done).
    """
    import asyncio
    from datetime import datetime
    from backend.infrastructure.db import SessionLocal
    from backend.analysis.toolbox.reports.generator import MorningReportGenerator

    target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()

    # Run async function in sync context since Celery workers are synchronous
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we are already inside a running async event loop (e.g. FastAPI fallback),
            # we need to create a nested task rather than run_until_complete which crashes.
            import threading
            with SessionLocal() as db:
                generator = MorningReportGenerator(db, target_date)

                # Run the async generator inside a separate thread's new loop
                def run_in_thread(result_list, error_list):
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        result_list.append(new_loop.run_until_complete(generator.generate_report()))
                    except Exception as e:
                        error_list.append(e)
                    finally:
                        new_loop.close()

                results = []
                errors = []
                t = threading.Thread(target=run_in_thread, args=(results, errors))
                t.start()
                t.join()
                if errors:
                    raise errors[0]
                pdf_path = results[0] if results else None
        else:
            with SessionLocal() as db:
                generator = MorningReportGenerator(db, target_date)
                pdf_path = loop.run_until_complete(generator.generate_report())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        with SessionLocal() as db:
            generator = MorningReportGenerator(db, target_date)
            pdf_path = loop.run_until_complete(generator.generate_report())
    except Exception as e:
        err_msg = str(e)
        logger.error(f"Morning Report Generation Failed: {err_msg}")
        import traceback
        traceback.print_exc()
        self.update_state(state='FAILURE', meta={"error": err_msg, "exc_type": "Exception", "exc_message": err_msg})
        raise Exception(f"Morning Report Generation Failed: {err_msg}")

    return {
        "status": "SUCCESS",
        "message": f"Report generated at {pdf_path}",
        "url": f"/api/morning-report/download/{target_date_str}"
    }


@shared_task(bind=True, max_retries=3, acks_late=True, reject_on_worker_lost=True)
def build_dividend_databank_task(self, force: bool = False):
    from sqlalchemy import func, or_, desc
    import datetime
    from collections import defaultdict
    import re
    import logging

    from backend.infrastructure.db import SessionLocal
    from backend.ingest.nse_models import CorporateAction, BoardMeeting, DividendDatabank, FinancialResult
    from backend.ingest.field_mapper import FieldMapper

    db = SessionLocal()
    try:
        today = datetime.date.today()

        ca_query = db.query(CorporateAction).filter(
            or_(
                CorporateAction.parsed_dividend_amount != None,
                CorporateAction.dividend_type.in_(['Bonus', 'Split', 'Demerger']), CorporateAction.purpose.ilike('%bonus%'), CorporateAction.purpose.ilike('%split%'),
                CorporateAction.purpose.ilike('%dividend%'),
                CorporateAction.purpose.ilike('%intdiv%'),
                CorporateAction.purpose.ilike('%int div%'),
                CorporateAction.purpose.ilike('%findiv%'),
                CorporateAction.purpose.ilike('%fin div%'), CorporateAction.purpose.ilike('%special%'),
                CorporateAction.purpose.ilike('%div-%'),
                CorporateAction.purpose.ilike('%div -%'),
                CorporateAction.purpose.ilike('% div %')
            )
        )

        bm_query = db.query(BoardMeeting).filter(
            or_(
                BoardMeeting.purpose.ilike('%dividend%'),
                BoardMeeting.purpose.ilike('%intdiv%'),
                BoardMeeting.purpose.ilike('%int div%'),
                BoardMeeting.purpose.ilike('%findiv%'),
                BoardMeeting.purpose.ilike('%fin div%'), BoardMeeting.purpose.ilike('%special%'),
                BoardMeeting.purpose.ilike('%agm%'),
                BoardMeeting.purpose.ilike('%annual general meeting%'),
                BoardMeeting.extracted_dividend_amount != None
            )
        )

        if not force:
            # Only fetch CA and BM from the last 7 days for incremental updates,
            # then find all unique symbols involved, and fetch full history ONLY for those symbols
            recent_cutoff = today - datetime.timedelta(days=7)
            recent_cas = ca_query.filter(CorporateAction.date >= recent_cutoff).all()
            recent_bms = bm_query.filter(BoardMeeting.date >= recent_cutoff).all()

            affected_symbols = set([r.symbol for r in recent_cas]).union(set([r.symbol for r in recent_bms]))

            if not affected_symbols:
                return "No recent dividend actions found. Databank is up to date."

            ca_records = ca_query.filter(CorporateAction.symbol.in_(affected_symbols)).order_by(desc(CorporateAction.date)).all()
            bm_records = bm_query.filter(BoardMeeting.symbol.in_(affected_symbols)).order_by(desc(BoardMeeting.date)).all()
        else:
            ca_records = ca_query.order_by(desc(CorporateAction.date)).all()
            bm_records = bm_query.order_by(desc(BoardMeeting.date)).all()

        # Group by symbol
        ca_by_symbol = defaultdict(list)
        adjustments_by_symbol = defaultdict(list)
        for r in ca_records:
            sym = r.symbol.upper()

            # Attempt to reparse any missing dividend amounts first for all corporate actions
            parsed_amount = r.parsed_dividend_amount
            if parsed_amount is None and r.purpose:
                reparsed_amt, _ = FieldMapper._parse_dividend(r.purpose, r.face_value if hasattr(r, 'face_value') else None)
                if reparsed_amt is not None:
                    parsed_amount = reparsed_amt
                    r.parsed_dividend_amount = reparsed_amt
                    db.add(r)

            if r.dividend_type in ['Bonus', 'Split', 'Demerger']:
                # Extract ratio from purpose
                ratio = 1.0
                purpose_lower = (r.purpose or "").lower()
                if r.dividend_type == 'Bonus':
                    match = re.search(r'(\d+)\s*:\s*(\d+)', purpose_lower)
                    if match:
                        bonus_shares = float(match.group(1))
                        held_shares = float(match.group(2))
                        if held_shares > 0:
                            ratio = held_shares / (held_shares + bonus_shares)
                elif r.dividend_type == 'Split':
                    match = re.search(r'from\s*(?:rs\.?|re\.?|rupees?)?\s*(\d+(?:\.\d+)?).*?to\s*(?:rs\.?|re\.?|rupees?)?\s*(\d+(?:\.\d+)?)', purpose_lower)
                    if match:
                        old_fv = float(match.group(1))
                        new_fv = float(match.group(2))
                        if old_fv > 0:
                            ratio = new_fv / old_fv
                    else:
                        match2 = re.search(r'(\d+)\s*:\s*(\d+)', purpose_lower)
                        if match2:
                            new_shares = float(match2.group(1))
                            old_shares = float(match2.group(2))
                            if old_shares > 0 and new_shares > 0:
                                if new_shares > old_shares:
                                    ratio = old_shares / new_shares
                                else:
                                    ratio = new_shares / old_shares
                elif r.dividend_type == 'Demerger':
                    match3 = re.search(r'(\d+)\s*:\s*(\d+)', purpose_lower)
                    if match3:
                        new_shares = float(match3.group(1))
                        old_shares = float(match3.group(2))
                        if old_shares > 0 and new_shares > 0:
                            ratio = old_shares / (old_shares + new_shares)
                    else:
                        ratio = 0.5

                if ratio != 1.0 and r.date:
                    adjustments_by_symbol[sym].append({
                        "date": r.date,
                        "ratio": ratio
                    })

                # Still append splits/bonuses to the UI history so they show in the timeline
                ann_date = getattr(r, 'broadcast_date', None)
                if hasattr(ann_date, 'date'):
                    ann_date = ann_date.date()

                ca_by_symbol[sym].append({
                    "ex_date": r.ex_date.strftime("%Y-%m-%d") if r.ex_date else None,
                    "ex_date_obj": r.ex_date,
                    "announcement_date_obj": ann_date,
                    "broadcast_date": r.broadcast_date if hasattr(r, 'broadcast_date') else None,
                    "dividend_type": r.dividend_type,
                    "purpose": r.purpose,
                    "amount": parsed_amount,
                    "raw_amount": parsed_amount,
                    "face_value": r.face_value if hasattr(r, 'face_value') else None,
                    "record_date": r.record_date if hasattr(r, 'record_date') else None
                })

            elif parsed_amount is not None or (r.purpose and ('dividend' in r.purpose.lower() or 'special' in r.purpose.lower() or 'bonus' in r.purpose.lower() or 'split' in r.purpose.lower())):
                ann_date = getattr(r, 'broadcast_date', None)
                if hasattr(ann_date, 'date'):
                    ann_date = ann_date.date()

                ca_by_symbol[sym].append({
                    "ex_date": r.ex_date.strftime("%Y-%m-%d") if r.ex_date else None,
                    "ex_date_obj": r.ex_date,
                    "announcement_date_obj": ann_date,
                    "broadcast_date": r.broadcast_date if hasattr(r, 'broadcast_date') else None,
                    "dividend_type": r.dividend_type,
                    "purpose": r.purpose,
                    "amount": parsed_amount,
                    "raw_amount": parsed_amount,
                    "face_value": r.face_value if hasattr(r, 'face_value') else None,
                    "record_date": r.record_date if hasattr(r, 'record_date') else None
                })

        bm_by_symbol = defaultdict(list)
        for bm in bm_records:
            bm_by_symbol[bm.symbol.upper()].append(bm)

        # Commit newly parsed CA amounts before we do anything else
        db.commit()

        # Also fetch financials to enrich the databank
        fin_records = db.query(FinancialResult).all()
        fin_by_symbol = defaultdict(list)
        for fin in fin_records:
            fin_by_symbol[fin.symbol.upper()].append(fin)

        event_symbols = set(ca_by_symbol.keys()).union(set(bm_by_symbol.keys()))
        target_symbols = event_symbols

        for sym in target_symbols:
            ca_history = ca_by_symbol.get(sym, [])
            bms = bm_by_symbol.get(sym, [])
            fins = fin_by_symbol.get(sym, [])

            # Sort financials by date descending
            fins.sort(key=lambda x: x.date, reverse=True)

            combined_actions = list(ca_history)

            # 1. Synthesize Board Meetings into Actions if they don't have one
            for m in bms:
                purpose_lower = (m.purpose or '').lower()
                has_amount = m.extracted_dividend_amount is not None
                is_agm = False

                if 'dividend' in purpose_lower or 'bonus' in purpose_lower or 'split' in purpose_lower or 'sub-division' in purpose_lower or has_amount or is_agm:
                    m_date = m.meeting_date if hasattr(m, 'meeting_date') and m.meeting_date else m.date
                    if hasattr(m_date, 'date'): m_date = m_date.date()

                    has_linked_action = False
                    if m_date:
                        for a in combined_actions:
                            if not a.get('is_synthetic'):
                                a_date = a.get('ex_date_obj')
                                if hasattr(a_date, 'date'): a_date = a_date.date()

                                if a_date and a_date >= m_date:
                                    diff_days = abs((a_date - m_date).days)
                                    div_type_lower = (a.get('dividend_type') or m.extracted_dividend_type or '').lower()
                                    window = 180 if any(x in div_type_lower for x in ['final', 'bonus', 'split']) else 45
                                    if diff_days <= window:
                                        has_linked_action = True
                                        if (a.get('amount') is None or a.get('amount') == "-") and m.extracted_dividend_amount:
                                            a['amount'] = m.extracted_dividend_amount
                                            a['raw_amount'] = m.extracted_dividend_amount
                                        if not a.get('dividend_type') or a.get('dividend_type') == '-' or a.get('dividend_type') == 'Dividend':
                                            a['dividend_type'] = m.extracted_dividend_type or 'Final'

                                        # Overwrite Corporate Action broadcast date with true Board Meeting Announcement Date
                                        if getattr(m, 'broadcast_date', None):
                                            a['broadcast_date'] = m.broadcast_date
                                            a['announcement_date_obj'] = m.broadcast_date
                                        a['_matchedMeeting'] = m
                                        break

                                a_purpose = (a.get('purpose') or '').lower()
                                if not a_date and (a_purpose.find('not yet declared') != -1 or a_purpose.find('dividend (') != -1 or a_purpose.find('dividend') != -1):
                                    is_time_match = False
                                    b_date = a.get('broadcast_date')
                                    meet_date = m.meeting_date
                                    if b_date and meet_date:
                                        if hasattr(b_date, 'date'): b_date = b_date.date()
                                        if hasattr(meet_date, 'date'): meet_date = meet_date.date()
                                        diff_days = (b_date - meet_date).days
                                        # Only link if the CA broadcast is on or AFTER the BM date, within the window
                                        if diff_days >= -10:
                                            div_type_lower = (a.get('dividend_type') or m.extracted_dividend_type or '').lower()
                                            window = 180 if any(x in div_type_lower for x in ['final', 'bonus', 'split']) else 45
                                            if diff_days <= window:
                                                is_time_match = True

                                    if is_time_match:
                                        if (a.get('amount') is None or a.get('amount') == "-") and m.extracted_dividend_amount:
                                            a['amount'] = m.extracted_dividend_amount
                                            a['raw_amount'] = m.extracted_dividend_amount
                                        if not a.get('dividend_type') or a.get('dividend_type') == '-' or a.get('dividend_type') == 'Dividend':
                                            a['dividend_type'] = m.extracted_dividend_type or 'Final'

                                        # Overwrite Corporate Action broadcast date with true Board Meeting Announcement Date
                                        if getattr(m, 'broadcast_date', None):
                                            a['broadcast_date'] = m.broadcast_date
                                            a['announcement_date_obj'] = m.broadcast_date

                                        has_linked_action = True
                                        a['_matchedMeeting'] = m
                                        break

                    if not has_linked_action:
                        # Create Synthetic
                        amount = m.extracted_dividend_amount if m.extracted_dividend_amount is not None else None
                        if amount is None and getattr(m, 'parsed_dividend_amount', None) is not None:
                             amount = m.parsed_dividend_amount

                        div_type = '-'
                        agm_date = None
                        if 'dividend' in purpose_lower or has_amount:
                            div_type = m.extracted_dividend_type or 'Dividend'
                            if div_type == 'Dividend' or div_type == '-':
                                if 'interim' in purpose_lower: div_type = 'Interim'
                                elif 'special' in purpose_lower: div_type = 'Special'
                                elif 'final' in purpose_lower: div_type = 'Final'

                            if amount is None:
                                match = re.search(r'(?:rs\.?|rupees?|re\.?)\s*([0-9]+(?:\.[0-9]+)?)|([0-9]+(?:\.[0-9]+)?)\s*\/\-|dividend\s+of\s+([0-9]+(?:\.[0-9]+)?)|dividend.*?\s+([0-9]+(?:\.[0-9]+)?)\s+per|dividend\s*-\s*(?:rs\.?|rupees?|re\.?)\s*([0-9]+(?:\.[0-9]+)?)', purpose_lower)
                                if match:
                                    amount = next((g for g in match.groups() if g is not None), None)


                        elif 'bonus' in purpose_lower:
                            div_type = 'Bonus'
                        elif 'split' in purpose_lower or 'sub-division' in purpose_lower:
                            div_type = 'Split'

                        if is_agm:
                             # Try to find a date in the purpose like 'AGM - 15-Jul-2026'
                             date_match = re.search(r'(?:agm|annual general meeting).*?(?:on|dated|scheduled for|-)?\s*(\d{1,2}(?:st|nd|rd|th)?\s+[a-zA-Z]{3,9}\s+\d{4}|\d{1,2}-[a-zA-Z]{3}-\d{4}|\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})', purpose_lower)
                             if not date_match:
                                 date_match = re.search(r'(\d{1,2}-[a-zA-Z]{3}-\d{4}|\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})', purpose_lower)
                             if date_match:
                                 try:
                                     from dateutil.parser import parse
                                     agm_date = parse(date_match.group(1).replace('st ', ' ').replace('nd ', ' ').replace('rd ', ' ').replace('th ', ' ')).date()
                                 except:
                                     pass

                        # If AGM date is still missing, try to fetch it from the model if we patched it directly to the model earlier
                        if agm_date is None:
                            if hasattr(m, 'agm_date') and m.agm_date:
                                agm_date = m.agm_date
                            # also extract from extracted_agm_date if present in json
                            # Since it was parsed as EXTRACTED_AGM_DATE, let's see if we added it as a column
                            # It actually gets appended to bm_purpose in nse_lib.py: `bm_purpose += f" - AGM - {agm_date}"`
                            # Which the regex above should catch, but let's be safe.

                        combined_actions.append({
                            "symbol": sym,
                            "purpose": m.purpose,
                            "dividend_type": div_type,
                            "ex_date": None,
                            "ex_date_obj": None,
                            "agm_date": agm_date,
                            "announcement_date_obj": getattr(m, "broadcast_date", None),
                            "broadcast_date": m.broadcast_date if hasattr(m, "broadcast_date") else None,
                            "amount": amount if div_type != "AGM" else None,
                            "raw_amount": amount if div_type != "AGM" else None,
                            "face_value": None,
                            "is_synthetic": True,
                            "_matchedMeeting": m
                        })

# 2. Timeline Linkage & Merge
            group_officials = [a for a in combined_actions if not a.get('is_synthetic')]
            group_synthetics = [a for a in combined_actions if a.get('is_synthetic')]

            def safe_date(d):
                if hasattr(d, 'date'): return d.date()
                if isinstance(d, datetime.datetime): return d.date()
                if isinstance(d, datetime.date): return d
                return datetime.date.min

            # PHASE 1: Merge Announcements and Outcomes
            # Strictly group by meeting_date so we don't leave orphaned announcements.

            dedup_syns = []

            # Group by safe meeting date
            meeting_groups = defaultdict(list)
            for syn in group_synthetics:
                syn_m = syn.get('_matchedMeeting')
                m_date = safe_date(syn_m.meeting_date if syn_m and syn_m.meeting_date else syn.get('broadcast_date'))
                meeting_groups[m_date].append(syn)

            for m_date, items in meeting_groups.items():
                if not items: continue
                if len(items) == 1:
                    dedup_syns.append(items[0])
                    continue

                # We have multiple board meeting records for the same day (e.g., an Announcement and an Outcome).
                # We need to fold them into one. But if they are distinct events (Interim AND Final on same day), preserve them.

                merged_items = []
                for item in items:
                    merged = False
                    for existing in merged_items:
                        # Check if they can be merged
                        s_type = item.get('dividend_type')
                        e_type = existing.get('dividend_type')

                        s_amt = item.get('amount')
                        e_amt = existing.get('amount')

                        types_conflict = (s_type in ['Interim', 'Final', 'Special'] and e_type in ['Interim', 'Final', 'Special'] and s_type != e_type)
                        amounts_conflict = False
                        if s_amt is not None and str(s_amt) != '-' and e_amt is not None and str(e_amt) != '-':
                            try:
                                if float(s_amt) != float(e_amt):
                                    amounts_conflict = True
                            except ValueError:
                                if s_amt != e_amt:
                                    amounts_conflict = True

                        if not types_conflict and not amounts_conflict:
                            # Merge them
                            if (existing.get('amount') is None or existing.get('amount') == "-") and s_amt is not None:
                                existing['amount'] = s_amt
                                existing['raw_amount'] = item.get('raw_amount')

                            if existing.get('dividend_type') in ['-', 'Dividend'] and s_type not in ['-', 'Dividend']:
                                existing['dividend_type'] = s_type

                            # Keep the earliest broadcast date (the announcement)
                            b1 = safe_date(item.get('broadcast_date'))
                            b2 = safe_date(existing.get('broadcast_date'))
                            if b1 != datetime.date.min and b2 != datetime.date.min and b1 < b2:
                                existing['broadcast_date'] = item.get('broadcast_date')

                            merged = True
                            break

                    if not merged:
                        merged_items.append(item)

                dedup_syns.extend(merged_items)

            # PHASE 2: Link Corporate Actions (Ex-Dates) to Unified Meetings
            final_actions = []

            # We want to match Corporate Actions backwards to their originating Board Meeting.
            # A Corporate Action Ex-Date should generally be *after* or *on* the Board Meeting date.

            # Universal T+1 Ex-Date Logic (India Market)
            # Run this BEFORE linkage so that off_date_val has a valid ex_date_obj for linkage calculations
            for item in group_officials + dedup_syns:
                if item.get('ex_date_obj') is None and item.get('record_date') is not None:
                    rec_date = item.get('record_date')
                    if isinstance(rec_date, str):
                        import datetime
                        try:
                            item['ex_date_obj'] = datetime.datetime.strptime(rec_date, "%d-%b-%Y").date()
                        except ValueError:
                            item['ex_date_obj'] = rec_date
                    else:
                        item['ex_date_obj'] = rec_date
                    item['ex_date'] = rec_date

            group_officials.sort(key=lambda x: safe_date(x.get('ex_date_obj') or x.get('broadcast_date') or x.get('announcement_date_obj') or x.get('date')), reverse=True)

            for syn in dedup_syns:
                matched = False
                syn_m = syn.get('_matchedMeeting')
                syn_meeting_date = safe_date(syn_m.meeting_date if syn_m and syn_m.meeting_date else syn.get('broadcast_date'))

                for off in group_officials:
                    off_date_val = safe_date(off.get('announcement_date_obj') or off.get('broadcast_date') or off.get('ex_date_obj') or off.get('date'))

                    if syn_meeting_date != datetime.date.min and off_date_val != datetime.date.min:
                        # Diff is (Corporate Action Ex-Date) - (Board Meeting Date)
                        diff_days = (off_date_val - syn_meeting_date).days

                        div_type_lower = (syn.get('dividend_type') or off.get('dividend_type') or '').lower()
                        window = 180 if any(x in div_type_lower for x in ['final', 'bonus', 'split']) else 45

                        syn_t = syn.get('dividend_type')
                        off_t = off.get('dividend_type')

                        types_compatible = (syn_t == off_t or syn_t in ['-', 'Dividend'] or off_t in ['-', 'Dividend'])
                        if syn_t in ['Interim', 'Final', 'Special'] and off_t in ['Interim', 'Final', 'Special'] and syn_t != off_t:
                            types_compatible = False

                        # Check amount conflicts during synthesis merge
                        s_amt = syn.get('amount')
                        o_amt = off.get('amount')
                        amt_compatible = True
                        if s_amt is not None and str(s_amt) != '-' and o_amt is not None and str(o_amt) != '-':
                            try:
                                if float(s_amt) != float(o_amt):
                                    amt_compatible = False
                            except ValueError:
                                if s_amt != o_amt:
                                    amt_compatible = False

                        # Valid link: Corporate action is within the forward window and compatible
                        if -10 <= diff_days <= window and types_compatible and amt_compatible:
                            if off.get('amount') is None or off.get('amount') == "-":
                                off['amount'] = syn.get('amount')
                                off['raw_amount'] = syn.get('raw_amount')

                            off_m = off.get('_matchedMeeting')

                            # Unify Ex-Date logic: Board Meeting row inherits Ex-Date from Corporate Action
                            if off.get('ex_date_obj'):
                                syn['ex_date_obj'] = off.get('ex_date_obj')
                                syn['ex_date'] = off.get('ex_date')
                            if off.get('record_date'):
                                syn['record_date'] = off.get('record_date')
                                if not syn.get('ex_date_obj'):
                                    syn['ex_date_obj'] = off.get('record_date')
                                    syn['ex_date'] = off.get('record_date').strftime('%Y-%m-%d') if hasattr(off.get('record_date'), 'strftime') else off.get('record_date')

                            if syn.get('dividend_type') and off.get('dividend_type') in ['Dividend', '-', '']:
                                off['dividend_type'] = syn.get('dividend_type')
                            elif off.get('dividend_type') and syn.get('dividend_type') in ['Dividend', '-', '']:
                                syn['dividend_type'] = off.get('dividend_type')

                            if not off_m or (syn_m and safe_date(syn_m.meeting_date) > safe_date(off_m.meeting_date)):
                                off['_matchedMeeting'] = syn_m

                            # The Board Meeting's broadcast date is the true announcement date of the event.
                            # Corporate Actions often just reflect the date the CA was filed on the exchange.
                            # We must explicitly overwrite the CA's broadcast date with the BM's broadcast date.
                            if syn.get('broadcast_date'):
                                off['broadcast_date'] = syn.get('broadcast_date')
                            if syn.get('announcement_date_obj'):
                                off['announcement_date_obj'] = syn.get('announcement_date_obj')

                            matched = True
                            break

                if not matched:
                    # An upcoming board meeting, or an outcome whose corporate action hasn't been declared yet
                    final_actions.append(syn)

            for off in group_officials:
                # 'off' absorbed the matched 'syn' data in the loop above.
                # So we simply append all officials.
                final_actions.append(off)

            # Sort chronologically
            def final_sort_key(x):
                t = safe_date(x.get('ex_date_obj'))
                if t != datetime.date.min: return t
                t = safe_date(x.get('announcement_date_obj') or x.get('broadcast_date'))
                if t != datetime.date.min: return t
                m = x.get('_matchedMeeting')
                if m:
                    t = safe_date(m.meeting_date)
                    if t != datetime.date.min: return t
                t = safe_date(x.get('date'))
                return t


            final_actions.sort(key=final_sort_key, reverse=True)

            ca_by_symbol[sym] = []
            for action in final_actions:
                m = action.get('_matchedMeeting')
                bm_date = m.meeting_date if m else None
                ca_by_symbol[sym].append({
                    "ex_date": action.get('ex_date') if action.get('ex_date') else None,
                    "ex_date_obj": action.get('ex_date_obj'),
                    "announcement_date_obj": action.get("announcement_date_obj"),
                    "broadcast_date": action.get('broadcast_date'),
                    "board_meeting_date": bm_date,
                    "dividend_type": action.get('dividend_type'),
                    "purpose": action.get('purpose'),
                    "amount": action.get('amount'),
                    "raw_amount": action.get('raw_amount'),
                    "face_value": action.get('face_value'),
                    "is_synthetic": action.get('is_synthetic', False),
                    "record_date": action.get('record_date'),
                    "agm_date": action.get('agm_date')
                })
        # When force is false, we want to UPSERT instead of delete all history.
        # This solves the "takes a hell lot of time" issue and properly updates rows.

        if force:
            db.query(DividendDatabank).delete()
            db.commit()

        added_count = 0
        updated_count = 0

        for sym, history in ca_by_symbol.items():
            # If we are not forcing, let's fetch existing rows for this symbol to avoid blind inserts
            existing_rows = []

            sym_fins = fin_by_symbol.get(sym, [])

            existing_rows = db.query(DividendDatabank).filter(DividendDatabank.symbol == sym).all()


            for h in history:
                ex_date_val = h.get('ex_date_obj')
                is_awaited = False
                if ex_date_val is None:
                    is_awaited = True

                sort_dt = ex_date_val or h.get('announcement_date_obj') or datetime.date.min
                if hasattr(sort_dt, 'date'):
                    sort_dt = sort_dt.date()

                final_date = sort_dt if sort_dt != datetime.date.min else datetime.date(1900, 1, 1)

                # UPSERT logic: Try to find a matching existing row
                match = None
                for row in existing_rows:
                        # Match by identical ex-date OR identical announcement date OR same type within recent window
                        t1 = row.dividend_type
                        t2 = h.get('dividend_type')
                        types_match = (t1 == t2 or t1 in ['-', 'Dividend'] or t2 in ['-', 'Dividend'])
                        if t1 in ['Interim', 'Final', 'Special'] and t2 in ['Interim', 'Final', 'Special'] and t1 != t2:
                            types_match = False

                        if types_match:
                            if row.ex_date and ex_date_val and row.ex_date == ex_date_val:
                                match = row
                                break
                            if row.announcement_date and h.get('announcement_date_obj') and row.announcement_date == h.get('announcement_date_obj'):
                                match = row
                                break

                            # Strict match for awaited records: ensure they belong to the same event cycle, not just any future event.
                            div_type_lower = (row.dividend_type or '').lower()
                            window = 180 if any(x in div_type_lower for x in ['final', 'bonus', 'split']) else 45
                            if row.is_awaited and abs((row.date - final_date).days) <= window:
                                # Don't cross-contaminate if both have explicit but differing amounts
                                r_amt = getattr(row, 'amount', None)
                                h_amt = h.get('amount')
                                if r_amt is not None and str(r_amt) != '-' and h_amt is not None and str(h_amt) != '-':
                                    try:
                                        if float(r_amt) != float(h_amt):
                                            continue
                                    except ValueError:
                                        if r_amt != h_amt:
                                            continue
                                match = row
                                break

                if match:
                    # UPDATE existing row
                    # DO NOT blindly overwrite ex-date if it's currently valid and new one is None
                    if ex_date_val:
                        match.ex_date = ex_date_val
                        # If ex_date_val is provided, this record is NO LONGER awaited
                        match.is_awaited = False
                    if h.get('announcement_date_obj'):
                        match.announcement_date = h.get('announcement_date_obj')
                    if h.get('broadcast_date'):
                        match.broadcast_date = h.get('broadcast_date')
                    if h.get('board_meeting_date'):
                        match.board_meeting_date = h.get('board_meeting_date')
                    if h.get('is_synthetic') is not None:
                        match.is_synthetic = h.get('is_synthetic')
                    # If we found an amount in history and DB has none (or they differ), update it
                    if h.get('amount') is not None:
                        match.amount = h.get('amount')
                        match.raw_amount = h.get('raw_amount')

                    if h.get('dividend_type') and h.get('dividend_type') not in ['-', 'Dividend', '']:
                        match.dividend_type = h.get('dividend_type')

                    # 1. EPS & Net Profit: Link by Board Meeting Date
                    # Find the most recent FinancialResult available ON or BEFORE the board meeting date (or final_date)
                    ref_date = match.board_meeting_date or final_date
                    if hasattr(ref_date, 'date'): ref_date = ref_date.date()
                    elif isinstance(ref_date, datetime.datetime): ref_date = ref_date.date()

                    latest_fin = None
                    for fin in sym_fins:
                        f_date = fin.date
                        if hasattr(f_date, 'date'): f_date = f_date.date()
                        elif isinstance(f_date, datetime.datetime): f_date = f_date.date()

                        if f_date and f_date <= ref_date:
                            latest_fin = fin
                            break  # sym_fins is already sorted descending by date

                    if latest_fin:
                        if latest_fin.basic_eps is not None:
                            match.eps = latest_fin.basic_eps
                            if match.amount:
                                match.payout_ratio = (match.amount / match.eps) * 100 if match.eps != 0 else None
                        if latest_fin.net_profit is not None:
                            match.net_profit = latest_fin.net_profit

                    match.dps = match.amount

                    if h.get('agm_date'):
                        # Relax the 'final' only constraint so AGM dates are saved even if event type is AGM or Special
                        if match.agm_date is None:
                            match.agm_date = h.get('agm_date')
                        match.agm_announcement_date = final_date

                    if h.get('face_value') is not None:
                        match.face_value = h.get('face_value')

                    if h.get('purpose'):
                        match.purpose = h.get('purpose')
                    elif match.purpose is None:
                        match.purpose = h.get('purpose')
                    if h.get('record_date'):
                        match.record_date = h.get('record_date')
                        # Ensure Ex-Date gets populated from Record Date at the DB level too
                        if not match.ex_date:
                            match.ex_date = h.get('record_date')

                    # Only mark as awaited if both incoming and existing have no ex-date
                    match.is_awaited = True if match.ex_date is None else False
                    updated_count += 1
                else:
                    # INSERT new row
                    new_item = DividendDatabank(
                        date=final_date,
                        symbol=sym.upper(),
                        ex_date=ex_date_val,
                        announcement_date=h.get('announcement_date_obj'),
                        broadcast_date=h.get('broadcast_date'),
                        dividend_type=h.get('dividend_type'),
                        amount=h.get('amount'),
                        raw_amount=h.get('raw_amount'),
                        face_value=h.get('face_value'),
                        purpose=h.get('purpose'),
                        is_awaited=is_awaited,
                        record_date=h.get('record_date'),
                        board_meeting_date=h.get('board_meeting_date'),
                        is_synthetic=h.get('is_synthetic', False),
                        agm_date=h.get('agm_date'),
                        agm_announcement_date=final_date if h.get('agm_date') else None
                    )

                    # 1. EPS & Net Profit: Link by Board Meeting Date
                    # Find the most recent FinancialResult available ON or BEFORE the board meeting date (or final_date)
                    ref_date = new_item.board_meeting_date or final_date
                    if hasattr(ref_date, 'date'): ref_date = ref_date.date()
                    elif isinstance(ref_date, datetime.datetime): ref_date = ref_date.date()

                    latest_fin = None
                    for fin in sym_fins:
                        f_date = fin.date
                        if hasattr(f_date, 'date'): f_date = f_date.date()
                        elif isinstance(f_date, datetime.datetime): f_date = f_date.date()

                        if f_date and f_date <= ref_date:
                            latest_fin = fin
                            break  # sym_fins is already sorted descending by date

                    if latest_fin:
                        if latest_fin.basic_eps is not None:
                            new_item.eps = latest_fin.basic_eps
                            if new_item.amount:
                                new_item.payout_ratio = (new_item.amount / new_item.eps) * 100 if new_item.eps != 0 else None
                        if latest_fin.net_profit is not None:
                            new_item.net_profit = latest_fin.net_profit

                    new_item.dps = new_item.amount

                    db.add(new_item)
                    existing_rows.append(new_item) # Add to existing to prevent dupes in the same loop
                    added_count += 1

        db.commit()
        return f"Successfully rebuilt databank. Added: {added_count}, Updated: {updated_count} records."
    except Exception as e:
        logger.error(f"Error rebuilding dividend databank: {e}")
        db.rollback()
        raise
    finally:
        db.close()

@shared_task(bind=True, acks_late=True)
def run_mwpl_analysis_task(self, latest_metric_date: Optional[str] = None):
    try:
        from backend.infrastructure.db import SessionLocal
        from backend.web.api.data.derivatives_routes import compute_mwpl_analysis
        db = SessionLocal()
        try:
            return compute_mwpl_analysis(db=db, latest_metric_date=latest_metric_date)
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error in MWPL analysis task: {e}")
        return {"status": "error", "message": str(e)}

@shared_task(bind=True, acks_late=True)
def run_oi_analysis_task(self, latest_metric_date: Optional[str] = None):
    try:
        from backend.infrastructure.db import SessionLocal
        from backend.web.api.data.derivatives_routes import compute_aggregated_oi_analysis
        db = SessionLocal()
        try:
            return compute_aggregated_oi_analysis(db=db, latest_metric_date=latest_metric_date)
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error in OI analysis task: {e}")
        return {"status": "error", "message": str(e)}

@shared_task(bind=True, acks_late=True)
def run_rollover_analysis_task(self, latest_metric_date: Optional[str] = None):
    try:
        from backend.infrastructure.db import SessionLocal
        from backend.web.api.data.derivatives_routes import compute_rollover_analysis
        db = SessionLocal()
        try:
            return compute_rollover_analysis(db=db, latest_metric_date=latest_metric_date)
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error in rollover analysis task: {e}")
        return {"status": "error", "message": str(e)}

@shared_task(bind=True, acks_late=True)
def run_volatility_analysis_task(self, latest_metric_date: Optional[str] = None):
    try:
        from backend.infrastructure.db import SessionLocal
        from backend.web.api.data.volatility_routes import compute_volatility_analysis
        db = SessionLocal()
        try:
            return compute_volatility_analysis(db=db, latest_metric_date=latest_metric_date)
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error in volatility analysis task: {e}")
        return {"status": "error", "message": str(e)}



@shared_task(bind=True, acks_late=True)
def patch_historical_eps_agm_task(self):
    from sqlalchemy import func
    import datetime
    import re
    import logging

    from backend.infrastructure.db import SessionLocal
    from backend.ingest.nse_models import CorporateAction, BoardMeeting, DividendDatabank, FinancialResult

    db = SessionLocal()
    try:
        symbols = db.query(DividendDatabank.symbol).distinct().all()
        symbols = [s[0] for s in symbols]

        updated_count = 0
        logger = logging.getLogger(__name__)

        for sym in symbols:
            # 1. Fetch EPS and Net Profit natively from FinancialResult table
            fin_records = db.query(FinancialResult).filter(FinancialResult.symbol == sym).order_by(FinancialResult.date.desc()).all()

            # 2. Fetch all databank rows for this symbol
            rows = db.query(DividendDatabank).filter(DividendDatabank.symbol == sym).all()
            for row in rows:
                row_date = row.date
                if not row_date: continue

                # Apply EPS, Net Profit, and Payout Ratio based on Board Meeting Date
                ref_date = row.board_meeting_date or row_date
                if hasattr(ref_date, 'date'): ref_date = ref_date.date()
                elif isinstance(ref_date, datetime.datetime): ref_date = ref_date.date()

                latest_fin = None
                for fin in fin_records:
                    f_date = fin.date
                    if hasattr(f_date, 'date'): f_date = f_date.date()
                    elif isinstance(f_date, datetime.datetime): f_date = f_date.date()

                    if f_date and f_date <= ref_date:
                        latest_fin = fin
                        break

                if latest_fin:
                     if latest_fin.basic_eps is not None:
                         row.eps = latest_fin.basic_eps
                         if row.amount:
                              row.payout_ratio = (row.amount / row.eps) * 100 if row.eps != 0 else None
                     if latest_fin.net_profit is not None:
                         row.net_profit = latest_fin.net_profit

                row.dps = row.amount

                # 3. Patch AGM Dates
                # AGM Dates only apply to Final dividends.
                # Look for an AGM announcement that happens *after* the dividend event (up to 6 months / ~180 days).
                # Meaning the AGM event date > dividend row_date, but within 180 days.
                if not row.agm_date and row.dividend_type and 'final' in row.dividend_type.lower():
                    bm = db.query(BoardMeeting).filter(
                        BoardMeeting.symbol == sym,
                        BoardMeeting.purpose.ilike('%annual general meeting%'),
                        BoardMeeting.date >= row_date,
                        func.extract('epoch', BoardMeeting.date) - func.extract('epoch', row_date) < 15552000 # ~180 days
                    ).order_by(BoardMeeting.date.asc()).first()

                    if bm:
                        row.agm_announcement_date = bm.date
                        date_match = re.search(r'(\d{1,2}-[a-zA-Z]{3}-\d{4}|\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})', (bm.purpose or '').lower())
                        if date_match:
                             try:
                                 from dateutil.parser import parse
                                 row.agm_date = parse(date_match.group(1)).date()
                             except:
                                 pass

                    # Or check corporate actions
                    if not row.agm_date:
                        ca = db.query(CorporateAction).filter(
                            CorporateAction.symbol == sym,
                            CorporateAction.purpose.ilike('%annual general meeting%'),
                            CorporateAction.date >= row_date,
                            func.extract('epoch', CorporateAction.date) - func.extract('epoch', row_date) < 15552000
                        ).order_by(CorporateAction.date.asc()).first()

                        if ca:
                            row.agm_announcement_date = ca.date
                            date_match = re.search(r'(\d{1,2}-[a-zA-Z]{3}-\d{4}|\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})', (ca.purpose or '').lower())
                            if date_match:
                                 try:
                                     from dateutil.parser import parse
                                     row.agm_date = parse(date_match.group(1)).date()
                                 except:
                                     pass

                updated_count += 1

            db.commit() # Commit per symbol to avoid massive transaction blocks

        return f"Successfully patched historical EPS and AGM for {updated_count} rows."
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()
