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
            logging.error(f"Max retries exceeded for date import: {err_msg}")
            self.update_state(state='FAILURE', meta={"exc_type": "Exception", "exc_message": f"Date Import Failed: {err_msg}"})
            raise Exception(f"Date Import Failed: {err_msg}")

        logging.error(f"Import failed: {exc}. Retrying... ({self.request.retries}/3)")
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
            logging.error(f"Max retries exceeded for retry failed imports: {err_msg}")
            self.update_state(state='FAILURE', meta={"exc_type": "Exception", "exc_message": f"Retry Failed: {err_msg}"})
            raise Exception(f"Retry Failed: {err_msg}")

        logging.error(f"Retry failed: {exc}. Retrying... ({self.request.retries}/3)")
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
                    logging.error(f"Error importing {current_date}: {e}")
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
        logging.error(f"Error in range import: {e}")
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
            logging.error(f"Max retries exceeded for latest import: {err_msg}")
            self.update_state(state='FAILURE', meta={"exc_type": "Exception", "exc_message": f"Latest Import Failed: {err_msg}"})
            raise Exception(f"Latest Import Failed: {err_msg}")

        logging.error(f"Latest import failed: {exc}. Retrying... ({self.request.retries}/3)")
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
        logging.error(f"Morning Report Preparation Failed: {err_msg}")
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
        logging.error(f"Morning Report Generation Failed: {err_msg}")
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
                CorporateAction.dividend_type.in_(['Bonus', 'Split', 'Demerger']),
                CorporateAction.purpose.ilike('%bonus%'),
                CorporateAction.purpose.ilike('%split%'),
                CorporateAction.purpose.ilike('%dividend%'),
                CorporateAction.purpose.ilike('%intdiv%'),
                CorporateAction.purpose.ilike('%int div%'),
                CorporateAction.purpose.ilike('%findiv%'),
                CorporateAction.purpose.ilike('%fin div%'),
                CorporateAction.purpose.ilike('%special%'),
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
                BoardMeeting.purpose.ilike('%fin div%'),
                BoardMeeting.purpose.ilike('%special%'),
                BoardMeeting.purpose.ilike('%agm%'),
                BoardMeeting.purpose.ilike('%annual general meeting%'),
                BoardMeeting.extracted_dividend_amount != None
            )
        )

        if not force:
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

        ca_by_symbol = defaultdict(list)
        bm_by_symbol = defaultdict(list)

        for r in ca_records:
            ca_by_symbol[r.symbol.upper()].append(r)

        for bm in bm_records:
            bm_by_symbol[bm.symbol.upper()].append(bm)

        fin_records = db.query(FinancialResult).all()
        fin_by_symbol = defaultdict(list)
        for fin in fin_records:
            fin_by_symbol[fin.symbol.upper()].append(fin)

        db.commit() # commit reparsed CA amounts if any were updated in previous versions

        event_symbols = set(ca_by_symbol.keys()).union(set(bm_by_symbol.keys()))

        def safe_date(d):
            if hasattr(d, 'date'): return d.date()
            if isinstance(d, datetime.datetime): return d.date()
            if isinstance(d, datetime.date): return d
            return datetime.date.min

        def get_amount_from_purpose(purpose_lower):
            match = re.search(r'(?:rs\.?|rupees?|re\.?)\s*([0-9]+(?:\.[0-9]+)?)|([0-9]+(?:\.[0-9]+)?)\s*\/\-|dividend\s+of\s+([0-9]+(?:\.[0-9]+)?)|dividend.*?\s+([0-9]+(?:\.[0-9]+)?)\s+per|dividend\s*-\s*(?:rs\.?|rupees?|re\.?)\s*([0-9]+(?:\.[0-9]+)?)', purpose_lower)
            if match:
                return next((g for g in match.groups() if g is not None), None)
            return None

        def extract_agm_date(purpose_lower):
            date_match = re.search(r'(?:agm|annual general meeting).*?(?:on|dated|scheduled for|-)?\s*(\d{1,2}(?:st|nd|rd|th)?\s+[a-zA-Z]{3,9}\s+\d{4}|\d{1,2}-[a-zA-Z]{3}-\d{4}|\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})', purpose_lower)
            if not date_match:
                date_match = re.search(r'(\d{1,2}-[a-zA-Z]{3}-\d{4}|\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})', purpose_lower)
            if date_match:
                try:
                    from dateutil.parser import parse
                    return parse(date_match.group(1).replace('st ', ' ').replace('nd ', ' ').replace('rd ', ' ').replace('th ', ' ')).date()
                except:
                    pass
            return None

        final_rows_by_symbol = defaultdict(list)

        for sym in event_symbols:
            cas = ca_by_symbol.get(sym, [])
            bms = bm_by_symbol.get(sym, [])

            # Phase 1: Corporate Actions as source of truth for announced dividends
            processed_bm_ids = set()
            consolidated_events = []

            for ca in cas:
                parsed_amount = ca.parsed_dividend_amount
                if parsed_amount is None and ca.purpose:
                    reparsed_amt, _ = FieldMapper._parse_dividend(ca.purpose, ca.face_value if hasattr(ca, 'face_value') else None)
                    if reparsed_amt is not None:
                         parsed_amount = reparsed_amt

                ca_date = safe_date(ca.ex_date or ca.record_date or ca.broadcast_date or ca.date)

                # Setup event dictionary
                event = {
                    "symbol": sym,
                    "ex_date_obj": safe_date(ca.ex_date) if safe_date(ca.ex_date) != datetime.date.min else None,
                    "ex_date": ca.ex_date.strftime("%Y-%m-%d") if ca.ex_date else None,
                    "record_date": ca.record_date,
                    "broadcast_date": None,
                    "announcement_date_obj": safe_date(ca.broadcast_date or ca.date),
                    "board_meeting_date": None,
                    "dividend_type": ca.dividend_type,
                    "amount": parsed_amount,
                    "raw_amount": parsed_amount,
                    "face_value": ca.face_value if hasattr(ca, 'face_value') else None,
                    "purpose": ca.purpose,
                    "is_synthetic": False,
                    "agm_date": None,
                    "is_awaited": False,
                    "ca_ref": ca,
                    "matched_bms": []
                }

                # Ex-date T+1 logic India
                if event['ex_date_obj'] is None and event['record_date'] is not None:
                    rec_date = event['record_date']
                    if isinstance(rec_date, str):
                        try:
                            event['ex_date_obj'] = datetime.datetime.strptime(rec_date, "%d-%b-%Y").date()
                        except ValueError:
                            event['ex_date_obj'] = rec_date
                    else:
                        event['ex_date_obj'] = rec_date
                    event['ex_date'] = rec_date
                    ca_date = safe_date(event['ex_date_obj'])

                # Find ALL compatible Board Meetings (Original Declaration, Later Updates, etc)
                # We sort bms chronologically to get the EARLIEST meeting as the primary broadcast/meeting date
                bms.sort(key=lambda x: safe_date(x.meeting_date or x.broadcast_date or x.date))

                for bm in bms:
                    if bm.id in processed_bm_ids: continue

                    bm_date = safe_date(bm.meeting_date or bm.broadcast_date or bm.date)
                    if bm_date == datetime.date.min: continue

                    diff_days = abs((ca_date - bm_date).days)
                    div_type_lower = (event['dividend_type'] or bm.extracted_dividend_type or '').lower()
                    window = 180 if any(x in div_type_lower for x in ['final', 'bonus', 'split']) else 45

                    if diff_days <= window:
                        bm_type = bm.extracted_dividend_type or ''
                        ca_type = event['dividend_type'] or ''

                        # Strict type check
                        type_conflict = False
                        if bm_type and ca_type and bm_type not in ['-', 'Dividend'] and ca_type not in ['-', 'Dividend']:
                            if bm_type != ca_type:
                                type_conflict = True

                        # Amount check
                        amount_conflict = False
                        bm_amount = bm.extracted_dividend_amount
                        if bm_amount is None:
                            bm_amount = get_amount_from_purpose((bm.purpose or '').lower())

                        if bm_amount is not None and event['amount'] is not None:
                            try:
                                if abs(float(bm_amount) - float(event['amount'])) > 0.01:
                                    amount_conflict = True
                            except:
                                pass

                        if not type_conflict and not amount_conflict:
                            # Found a matching BM for this CA!
                            event['matched_bms'].append(bm)
                            processed_bm_ids.add(bm.id)

                            # Inherit properties if missing
                            if event['amount'] is None and bm_amount is not None:
                                event['amount'] = bm_amount
                                event['raw_amount'] = bm_amount
                            if not event['dividend_type'] or event['dividend_type'] in ['-', 'Dividend']:
                                event['dividend_type'] = bm_type or event['dividend_type']

                            agm_d = extract_agm_date((bm.purpose or '').lower())
                            if agm_d and not event['agm_date']:
                                event['agm_date'] = agm_d

                # Set Broadcast Date and Board Meeting Date from the EARLIEST matched BM
                if event['matched_bms']:
                    earliest_bm = event['matched_bms'][0]
                    event['board_meeting_date'] = earliest_bm.meeting_date if hasattr(earliest_bm, 'meeting_date') else None
                    event['broadcast_date'] = earliest_bm.broadcast_date or earliest_bm.date
                    event['announcement_date_obj'] = earliest_bm.broadcast_date or earliest_bm.date
                else:
                    event['broadcast_date'] = ca.broadcast_date or ca.date
                    event['announcement_date_obj'] = ca.broadcast_date or ca.date

                consolidated_events.append(event)


            # Phase 2: Process Unmapped Board Meetings (Awaited Dividends and AGMs)
            unmapped_bms = [bm for bm in bms if bm.id not in processed_bm_ids]

            awaited_events = []

            for bm in unmapped_bms:
                purpose_lower = (bm.purpose or '').lower()
                has_amount = bm.extracted_dividend_amount is not None
                is_agm = 'agm' in purpose_lower or 'annual general meeting' in purpose_lower or re.search(r'\bagm\b', purpose_lower)

                amount = bm.extracted_dividend_amount
                if amount is None: amount = getattr(bm, 'parsed_dividend_amount', None)
                if amount is None: amount = get_amount_from_purpose(purpose_lower)

                div_type = '-'
                if 'dividend' in purpose_lower or has_amount:
                    div_type = 'Dividend'
                    if 'interim' in purpose_lower: div_type = 'Interim'
                    if 'special' in purpose_lower: div_type = 'Special'
                    if 'final' in purpose_lower: div_type = 'Final'
                elif 'bonus' in purpose_lower: div_type = 'Bonus'
                elif 'split' in purpose_lower or 'sub-division' in purpose_lower: div_type = 'Split'
                elif is_agm and not has_amount: div_type = 'AGM'

                agm_date = None
                if is_agm:
                    agm_date = extract_agm_date(purpose_lower)

                if div_type != '-' or has_amount or is_agm:
                    extracted_record_date = None
                    if hasattr(bm, 'extracted_record_date') and bm.extracted_record_date:
                        extracted_record_date = bm.extracted_record_date
                    elif hasattr(bm, 'record_date') and bm.record_date:
                        extracted_record_date = bm.record_date

                    event = {
                        "symbol": sym,
                        "ex_date_obj": extracted_record_date,
                        "ex_date": extracted_record_date.strftime("%Y-%m-%d") if extracted_record_date and hasattr(extracted_record_date, 'strftime') else extracted_record_date,
                        "record_date": extracted_record_date,
                        "broadcast_date": bm.broadcast_date or bm.date,
                        "announcement_date_obj": bm.broadcast_date or bm.date,
                        "board_meeting_date": bm.meeting_date if hasattr(bm, 'meeting_date') else None,
                        "dividend_type": div_type,
                        "amount": amount,
                        "raw_amount": amount,
                        "face_value": None,
                        "purpose": bm.purpose,
                        "is_synthetic": True,
                        "agm_date": agm_date,
                        "is_awaited": True if div_type != 'AGM' and not extracted_record_date else False,
                        "bm_ref": bm
                    }

                    # Deduplicate awaited events against each other
                    is_duplicate = False
                    for existing in awaited_events:
                        if existing['dividend_type'] == event['dividend_type'] or existing['dividend_type'] in ['-', 'Dividend'] or event['dividend_type'] in ['-', 'Dividend']:
                            d1 = safe_date(existing['board_meeting_date'] or existing['broadcast_date'])
                            d2 = safe_date(event['board_meeting_date'] or event['broadcast_date'])
                            if d1 != datetime.date.min and d2 != datetime.date.min:
                                diff = abs((d1 - d2).days)
                                window = 180 if any(x in (existing['dividend_type'] or '').lower() for x in ['final', 'bonus', 'split']) else 45

                                if diff <= window:
                                    # amount check
                                    amount_conflict = False
                                    if existing['amount'] is not None and event['amount'] is not None:
                                        try:
                                            if abs(float(existing['amount']) - float(event['amount'])) > 0.01:
                                                amount_conflict = True
                                        except:
                                            pass

                                    if not amount_conflict:
                                        is_duplicate = True
                                        # upgrade type
                                        if existing['dividend_type'] in ['-', 'Dividend', 'AGM'] and event['dividend_type'] not in ['-', 'Dividend', 'AGM']:
                                            existing['dividend_type'] = event['dividend_type']
                                        if existing['amount'] is None:
                                            existing['amount'] = event['amount']
                                            existing['raw_amount'] = event['raw_amount']
                                        if not existing['agm_date']:
                                            existing['agm_date'] = event['agm_date']

                                        # Use the earliest date
                                        if d2 < d1:
                                            existing['broadcast_date'] = event['broadcast_date']
                                            existing['board_meeting_date'] = event['board_meeting_date']
                                            existing['announcement_date_obj'] = event['announcement_date_obj']

                                        break
                    if not is_duplicate:
                        awaited_events.append(event)

            # Phase 3: Post-processing AGM linkage to Final Dividends
            all_events = consolidated_events + awaited_events

            # Map AGM dates to Final dividends within the same ~year
            for agm_event in all_events:
                if agm_event['dividend_type'] == 'AGM' and agm_event['agm_date']:
                    agm_ann_date = safe_date(agm_event['broadcast_date'])
                    for fin_event in all_events:
                        if (fin_event['dividend_type'] or '').lower() == 'final':
                            fin_date = safe_date(fin_event['ex_date_obj'] or fin_event['board_meeting_date'] or fin_event['broadcast_date'])
                            if agm_ann_date != datetime.date.min and fin_date != datetime.date.min:
                                # If AGM is announced within 180 days after the final dividend
                                diff = (agm_ann_date - fin_date).days
                                if -30 <= diff <= 180:
                                    if not fin_event['agm_date']:
                                        fin_event['agm_date'] = agm_event['agm_date']
                                    # We keep the AGM standalone event as requested, but also link the date

            final_rows_by_symbol[sym] = all_events

        # Final Database UPSERT phase
        if force:
            db.query(DividendDatabank).delete()
            db.commit()

        added_count = 0
        updated_count = 0

        for sym, history in final_rows_by_symbol.items():
            sym_fins = fin_by_symbol.get(sym, [])
            sym_fins.sort(key=lambda x: x.date, reverse=True)
            existing_rows = db.query(DividendDatabank).filter(DividendDatabank.symbol == sym).all()

            for h in history:
                ex_date_val = h.get('ex_date_obj')
                is_awaited = h.get('is_awaited', False)
                if ex_date_val is None and h.get('dividend_type') != 'AGM':
                    is_awaited = True
                elif ex_date_val is not None:
                    is_awaited = False

                sort_dt = ex_date_val or h.get('announcement_date_obj') or datetime.date.min
                if hasattr(sort_dt, 'date'): sort_dt = sort_dt.date()
                final_date = sort_dt if sort_dt != datetime.date.min else datetime.date(1900, 1, 1)

                match = None
                for row in existing_rows:
                    if row.dividend_type == h.get('dividend_type'):
                        if row.ex_date and ex_date_val and row.ex_date == ex_date_val:
                            match = row
                            break
                        if row.announcement_date and h.get('announcement_date_obj') and row.announcement_date == h.get('announcement_date_obj'):
                            match = row
                            break

                        div_type_lower = (row.dividend_type or '').lower()
                        window = 180 if any(x in div_type_lower for x in ['final', 'bonus', 'split']) else 45

                        # Match awaited records if they are logically the same event
                        if row.is_awaited and abs((row.date - final_date).days) <= window:
                            amount_conflict = False
                            if row.amount is not None and h.get('amount') is not None:
                                try:
                                    if abs(float(row.amount) - float(h.get('amount'))) > 0.01:
                                        amount_conflict = True
                                except: pass
                            if not amount_conflict:
                                match = row
                                break

                        # Specific exception for AGM: match if broadcast dates are very close
                        if h.get('dividend_type') == 'AGM':
                             d1 = safe_date(row.broadcast_date or row.date)
                             d2 = safe_date(h.get('broadcast_date'))
                             if d1 != datetime.date.min and d2 != datetime.date.min and abs((d1-d2).days) <= 10:
                                 match = row
                                 break

                if match:
                    match.date = final_date
                    match.ex_date = ex_date_val
                    if h.get('announcement_date_obj'): match.announcement_date = h.get('announcement_date_obj')
                    if h.get('broadcast_date'): match.broadcast_date = h.get('broadcast_date')
                    if h.get('board_meeting_date'): match.board_meeting_date = h.get('board_meeting_date')
                    if h.get('is_synthetic') is not None: match.is_synthetic = h.get('is_synthetic')
                    if h.get('amount') is not None:
                        match.amount = h.get('amount')
                        match.raw_amount = h.get('raw_amount')

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
                            break

                    if latest_fin:
                        if latest_fin.basic_eps is not None:
                            match.eps = latest_fin.basic_eps
                            if match.amount:
                                match.payout_ratio = (match.amount / match.eps) * 100 if match.eps != 0 else None
                        if latest_fin.net_profit is not None:
                            match.net_profit = latest_fin.net_profit

                    match.dps = match.amount

                    if h.get('agm_date') and h.get('dividend_type') and 'final' in h.get('dividend_type').lower():
                        match.agm_date = h.get('agm_date')
                        match.agm_announcement_date = h.get('broadcast_date')
                    elif h.get('dividend_type') == 'AGM' and h.get('agm_date'):
                         match.agm_date = h.get('agm_date')

                    if h.get('face_value') is not None: match.face_value = h.get('face_value')
                    if h.get('purpose'): match.purpose = h.get('purpose')
                    if h.get('record_date'):
                        match.record_date = h.get('record_date')
                        if not match.ex_date:
                            match.ex_date = h.get('record_date')

                    match.is_awaited = is_awaited
                    updated_count += 1
                else:
                    new_item = DividendDatabank(
                        date=final_date,
                        symbol=sym.upper(),
                        ex_date=ex_date_val or h.get('record_date'),
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
                        agm_announcement_date=h.get('broadcast_date') if h.get('agm_date') else None
                    )

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
                            break

                    if latest_fin:
                        if latest_fin.basic_eps is not None:
                            new_item.eps = latest_fin.basic_eps
                            if new_item.amount:
                                new_item.payout_ratio = (new_item.amount / new_item.eps) * 100 if new_item.eps != 0 else None
                        if latest_fin.net_profit is not None:
                            new_item.net_profit = latest_fin.net_profit

                    new_item.dps = new_item.amount

                    db.add(new_item)
                    existing_rows.append(new_item)
                    added_count += 1

        db.commit()
        return f"Successfully rebuilt databank. Added: {added_count}, Updated: {updated_count} records."
    except Exception as e:
        logging.error(f"Error rebuilding dividend databank: {e}")
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
        logging.error(f"Error in MWPL analysis task: {e}")
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
        logging.error(f"Error in OI analysis task: {e}")
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
        logging.error(f"Error in rollover analysis task: {e}")
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
        logging.error(f"Error in volatility analysis task: {e}")
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
