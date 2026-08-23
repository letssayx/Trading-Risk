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
    import datetime as dt_mod
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
    import datetime as dt_mod
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
    from sqlalchemy import func, or_, desc, and_
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
        logger = logging.getLogger(__name__)

        # 1. Fetch ALL relevant Corporate Actions (CA)
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

        # 2. Fetch ALL relevant Board Meetings (BM)
        bm_query = db.query(BoardMeeting).filter(
            or_(
                BoardMeeting.extracted_dividend_amount != None,
                BoardMeeting.purpose.ilike('%agm%'),
                BoardMeeting.purpose.ilike('%annual general meeting%'),
                BoardMeeting.purpose.ilike('%dividend%'),
                BoardMeeting.purpose.ilike('%bonus%'),
                BoardMeeting.purpose.ilike('%split%'),
                BoardMeeting.purpose.ilike('%demerger%')
            )
        )

        # 3. Filter by force flag or recent updates
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

        # 4. Group records by symbol
        ca_by_symbol = defaultdict(list)
        for r in ca_records:
            sym = r.symbol.upper()
            parsed_amount = r.parsed_dividend_amount
            if parsed_amount is None and r.purpose:
                reparsed_amt, _ = FieldMapper._parse_dividend(r.purpose, r.face_value if hasattr(r, 'face_value') else None)
                if reparsed_amt is not None:
                    parsed_amount = reparsed_amt
                    r.parsed_dividend_amount = reparsed_amt
                    db.add(r)

            ann_date = r.broadcast_date or r.date
            if hasattr(ann_date, 'date'):
                ann_date = ann_date.date()

            # Create a unique key to prevent duplicate CAs from NSE
            ca_key = f"{r.ex_date}_{r.dividend_type}_{parsed_amount}"

            # Only add if we haven't seen this exact CA key for this symbol
            if not any(c.get('ca_key') == ca_key for c in ca_by_symbol[sym]):
                ca_by_symbol[sym].append({
                    "id": r.id,
                    "ca_key": ca_key, # Store for deduplication
                    "ex_date": r.ex_date.strftime("%Y-%m-%d") if r.ex_date else None,
                    "ex_date_obj": r.ex_date,
                    "announcement_date_obj": ann_date,
                    "broadcast_date": r.broadcast_date if hasattr(r, 'broadcast_date') else None,
                    "dividend_type": r.dividend_type,
                    "purpose": r.purpose,
                    "amount": parsed_amount,
                    "raw_amount": parsed_amount,
                    "face_value": r.face_value if hasattr(r, 'face_value') else None,
                    "record_date": r.record_date if hasattr(r, 'record_date') else None,
                    "source": "CA"
                })

        bm_by_symbol = defaultdict(list)
        for bm in bm_records:
            bm_by_symbol[bm.symbol.upper()].append(bm)

        db.commit()

        # Financial Records Fetching
        fin_records = db.query(FinancialResult).all()
        fin_by_symbol = defaultdict(list)
        for fin in fin_records:
            fin_by_symbol[fin.symbol.upper()].append(fin)

        # 5. Build dividend events per symbol
        event_symbols = set(ca_by_symbol.keys()).union(set(bm_by_symbol.keys()))

        if force:
            logger.info("FORCE REBUILD: Wiping DividendDatabank table...")
            from sqlalchemy import text
            db.execute(text("TRUNCATE TABLE dividend_databank RESTART IDENTITY CASCADE"))
            db.commit()

        # 6. Process each symbol's dividend events
        for sym in event_symbols:
            ca_history = ca_by_symbol.get(sym, [])
            bms = bm_by_symbol.get(sym, [])
            fins = fin_by_symbol.get(sym, [])
            fins.sort(key=lambda x: x.date, reverse=True)

            # Sort CAs by ex_date
            ca_history.sort(key=lambda x: x.get('ex_date_obj') or datetime.date(1900, 1, 1))
            # Sort BMs chronologically
            bms.sort(key=lambda x: x.date if x.date else datetime.date(1900, 1, 1))

            final_actions = []
            processed_ca_keys = set()

            # --- PHASE 1: Process Corporate Actions (Source of Truth) ---
            for ca in ca_history:
                ca_type = ca.get('dividend_type')
                ca_amt = ca.get('amount')
                ca_ex_date = ca.get('ex_date_obj')
                if hasattr(ca_ex_date, 'date'):
                    ca_ex_date = ca_ex_date.date()

                # FIX: Use CA's OWN dates - NEVER overwrite with BM dates
                broad_date = ca.get('broadcast_date')
                ann_date = ca.get('announcement_date_obj')

                final_actions.append({
                    "ex_date": ca.get('ex_date'),
                    "ex_date_obj": ca_ex_date,
                    "announcement_date_obj": ann_date,
                    "broadcast_date": broad_date,
                    "dividend_type": ca_type,
                    "purpose": ca.get('purpose'),
                    "amount": ca_amt,
                    "raw_amount": ca.get('raw_amount'),
                    "face_value": ca.get('face_value'),
                    "record_date": ca.get('record_date'),
                    "source": "CA",
                    "is_awaited": False
                })

                # Register this CA so BMs can check against it
                ca_key = f"{ca_type}_{ca_amt}_{ca_ex_date}"
                processed_ca_keys.add(ca_key)

            # --- PHASE 2: Process Board Meetings (Only for Awaited/Pending Dividends) ---
            for bm in bms:
                purpose_lower = (bm.purpose or '').lower()

                # Handle AGMs separately
                if 'agm' in purpose_lower or 'annual general meeting' in purpose_lower:
                    agm_exists = any(a.get('dividend_type') == 'AGM' and a.get('source') == 'CA' for a in final_actions)
                    if not agm_exists:
                        agm_date = None
                        date_match = re.search(r'(\d{1,2}-[a-zA-Z]{3}-\d{4}|\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})', purpose_lower)
                        if date_match:
                            try:
                                from datetime import datetime as dt_internal
                                for fmt in ['%d-%b-%Y', '%d/%m/%Y', '%Y-%m-%d']:
                                    try:
                                        agm_date = dt_internal.strptime(date_match.group(1), fmt).date()
                                        break
                                    except ValueError: continue
                            except: pass

                        final_actions.append({
                            "dividend_type": 'AGM',
                            "purpose": bm.purpose,
                            "ex_date": None, "ex_date_obj": None,
                            "broadcast_date": bm.broadcast_date or bm.date,
                            "announcement_date_obj": bm.date,
                            "amount": None, "raw_amount": None, "face_value": None,
                            "agm_date": agm_date, "source": "BM_AGM", "is_awaited": True
                        })
                    continue

                # Process potential awaited dividends
                has_div_keyword = any(k in purpose_lower for k in ['bonus', 'split', 'demerger', 'dividend', 'div-'])
                if bm.extracted_dividend_amount is not None or has_div_keyword:
                    ext_type = bm.extracted_dividend_type
                    ext_amt = bm.extracted_dividend_amount

                    if not ext_type:
                        if 'interim' in purpose_lower or 'intdiv' in purpose_lower: ext_type = 'Interim'
                        elif 'final' in purpose_lower or 'findiv' in purpose_lower or 'yearly audited' in purpose_lower: ext_type = 'Final'
                        elif 'special' in purpose_lower: ext_type = 'Special'
                        else: ext_type = '-'

                    # CRITICAL CHECK: Does this BM event already exist in the processed CAs?
                    bm_date = bm.date
                    if hasattr(bm_date, 'date'): bm_date = bm_date.date()

                    is_covered_by_ca = False
                    for ca_key in processed_ca_keys:
                        parts = ca_key.split('_')
                        if len(parts) == 3:
                            ca_type_check, ca_amt_check, ca_ex_check = parts

                            # 1. Type Match
                            if ca_type_check != str(ext_type): continue

                            # 2. Amount Match
                            amt_match = True
                            if ext_amt is not None and ca_amt_check != 'None':
                                try:
                                    if abs(float(ext_amt) - float(ca_amt_check)) > 0.01:
                                        amt_match = False
                                except: amt_match = False
                            elif ext_amt is None and ca_amt_check != 'None':
                                amt_match = False

                            if not amt_match: continue

                            # 3. Date Proximity (within 180 days)
                            if ca_ex_check != 'None' and bm_date:
                                try:
                                    ca_ex_date_check = datetime.datetime.strptime(ca_ex_check, '%Y-%m-%d').date()
                                    if abs((ca_ex_date_check - bm_date).days) <= 180:
                                        is_covered_by_ca = True
                                        break
                                except: pass

                    # If NOT covered by a CA, add it as an awaited dividend
                    if not is_covered_by_ca and (ext_amt is not None or ext_type in ['Bonus', 'Split', 'Demerger']):
                        final_actions.append({
                            "dividend_type": ext_type,
                            "purpose": bm.purpose,
                            "ex_date": None, "ex_date_obj": None,
                            "broadcast_date": bm.broadcast_date or bm.date,
                            "announcement_date_obj": bm.date,
                            "amount": ext_amt, "raw_amount": ext_amt, "face_value": None,
                            "agm_date": None, "source": "BM_AWAITED", "is_awaited": True
                        })

            # --- UPSERT into DividendDatabank ---
            for act in final_actions:
                ex_date_val = act.get('ex_date_obj')
                if not ex_date_val: ex_date_val = act.get('record_date')

                amount_val = act.get('amount')
                broad_date = act.get('broadcast_date')
                ann_d = act.get('announcement_date_obj')
                is_awaited = act.get('is_awaited', False)

                # Link Financials
                eps = None
                net_profit = None
                fin_link_date = broad_date or ann_d or ex_date_val
                if hasattr(fin_link_date, 'date'): fin_link_date = fin_link_date.date()

                if fin_link_date:
                    for fin in fins:
                        f_date = fin.date
                        if hasattr(f_date, 'date'):
                            f_date = f_date.date()
                        if f_date and f_date <= fin_link_date:
                            eps = fin.basic_eps
                            net_profit = fin.net_profit
                            break

                dividend_type_val = act.get('dividend_type')
                if ex_date_val is None and dividend_type_val != 'AGM':
                    is_awaited = True
                    ex_date_val = datetime.date(1900, 1, 1)

                # Check for existing row to update
                matched_row = None
                # Since we wiped the table if force=True, this query will be empty on force rebuild
                existing_rows = db.query(DividendDatabank).filter(DividendDatabank.symbol == sym).all()

                for row in existing_rows:
                    r_ex = row.ex_date if row.ex_date else datetime.date(1900, 1, 1)
                    r_ex_val = ex_date_val if ex_date_val else datetime.date(1900, 1, 1)

                    is_ex_date_match = (r_ex == r_ex_val) or (row.is_awaited and r_ex == datetime.date(1900, 1, 1) and r_ex_val != datetime.date(1900, 1, 1))

                    if is_ex_date_match and row.dividend_type == dividend_type_val:
                        if row.amount is not None and amount_val is not None:
                            try:
                                if abs(float(row.amount) - float(amount_val)) < 0.01:
                                    matched_row = row
                                    break
                            except: pass
                        elif row.amount is None and amount_val is None:
                            matched_row = row
                            break

                if matched_row:
                    # Update existing row
                    if ex_date_val and ex_date_val != datetime.date(1900, 1, 1):
                        matched_row.ex_date = ex_date_val
                        matched_row.is_awaited = False
                    if broad_date: matched_row.broadcast_date = broad_date
                    if ann_d: matched_row.announcement_date = ann_d
                    if amount_val is not None: matched_row.amount = amount_val
                    if act.get('raw_amount') is not None: matched_row.raw_amount = act.get('raw_amount')
                    if act.get('face_value') is not None: matched_row.face_value = act.get('face_value')
                    if act.get('agm_date') and not matched_row.agm_date: matched_row.agm_date = act.get('agm_date')
                    if eps is not None: matched_row.eps = eps
                    if net_profit is not None: matched_row.net_profit = net_profit
                else:
                    # Insert new row
                    ex_d = ex_date_val if ex_date_val != datetime.date(1900, 1, 1) else None
                    new_row = DividendDatabank(
                        symbol=sym,
                        date=ex_d or ann_d or datetime.date.today(),
                        amount=amount_val,
                        raw_amount=act.get('raw_amount'),
                        dividend_type=dividend_type_val,
                        ex_date=ex_d,
                        purpose=act.get('purpose'),
                        face_value=act.get('face_value'),
                        is_awaited=is_awaited,
                        broadcast_date=broad_date,
                        announcement_date=ann_d,
                        agm_date=act.get('agm_date'),
                        eps=eps,
                        net_profit=net_profit,
                    )
                    db.add(new_row)

            # Commit per symbol to save progress
            db.commit()

        return "Dividend databank updated successfully!"
    except Exception as e:
        db.rollback()
        logging.error(f"Error building dividend databank: {e}", exc_info=True)
        return f"Error building dividend databank: {str(e)}"
    finally:
        db.close()
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
    import datetime as dt_mod
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
