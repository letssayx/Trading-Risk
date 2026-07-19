from celery import shared_task
from celery.utils.log import get_task_logger
from datetime import datetime, timedelta
from typing import List, Optional

from backend.ingest.nse_importer import NSEDataImporter
from backend.ingest.date_utils import NSEHolidayCalendar
from backend.ingest.nse_models import ImportLog, CorporateAction, BoardMeeting, DividendDatabank
from sqlalchemy import desc
from collections import defaultdict
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
            db.query(DividendDatabank).delete()
            db.commit()

            # Since it's a force rebuild, we should run the query without filtering by `parsed_dividend_amount != None`
            # because the old parsed amounts were corrupted (stuck as NULL).
            # We want to pull ALL corporate actions that look like dividends and reparse them entirely.

            force_ca_query = db.query(CorporateAction).filter(
                or_(
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

            force_bm_query = db.query(BoardMeeting).filter(
                or_(
                    BoardMeeting.purpose.ilike('%dividend%'),
                    BoardMeeting.purpose.ilike('%intdiv%'),
                    BoardMeeting.purpose.ilike('%int div%'),
                    BoardMeeting.purpose.ilike('%findiv%'),
                    BoardMeeting.purpose.ilike('%fin div%'), BoardMeeting.purpose.ilike('%special%'),
                )
            )

            ca_records = force_ca_query.order_by(desc(CorporateAction.date)).all()
            bm_records = force_bm_query.order_by(desc(BoardMeeting.date)).all()

        # Group by symbol
        ca_by_symbol = defaultdict(list)
        from backend.ingest.field_mapper import FieldMapper

        for r in ca_records:
            sym = r.symbol.upper()

            # Dynamically heal and reparse the amount on the fly
            dynamic_amt, dynamic_type = FieldMapper._parse_dividend(r.purpose, r.face_value if hasattr(r, 'face_value') else None)

            # Heal the DB cache if we found a better/new amount
            if dynamic_amt is not None and r.parsed_dividend_amount != dynamic_amt:
                r.parsed_dividend_amount = dynamic_amt

            use_amount = r.parsed_dividend_amount

            if r.dividend_type in ['Bonus', 'Split', 'Demerger'] and not (use_amount is not None):
                # Still append splits/bonuses to the UI history so they show in the timeline
                ann_date = r.broadcast_date or r.date
                if hasattr(ann_date, 'date'):
                    ann_date = ann_date.date()

                ca_by_symbol[sym].append({
                    "ex_date": r.ex_date.strftime("%Y-%m-%d") if r.ex_date else None,
                    "ex_date_obj": r.ex_date,
                    "announcement_date_obj": ann_date,
                    "broadcast_date": r.broadcast_date if hasattr(r, 'broadcast_date') else None,
                    "dividend_type": r.dividend_type,
                    "purpose": r.purpose,
                    "amount": None,
                    "raw_amount": None,
                    "face_value": r.face_value if hasattr(r, 'face_value') else None,
                    "record_date": r.record_date if hasattr(r, 'record_date') else None
                })

            elif use_amount is not None or (r.purpose and ('dividend' in r.purpose.lower() or 'special' in r.purpose.lower() or 'bonus' in r.purpose.lower() or 'split' in r.purpose.lower())):
                ann_date = r.broadcast_date or r.date
                if hasattr(ann_date, 'date'):
                    ann_date = ann_date.date()

                ca_by_symbol[sym].append({
                    "ex_date": r.ex_date.strftime("%Y-%m-%d") if r.ex_date else None,
                    "ex_date_obj": r.ex_date,
                    "announcement_date_obj": ann_date,
                    "broadcast_date": r.broadcast_date if hasattr(r, 'broadcast_date') else None,
                    "dividend_type": r.dividend_type,
                    "purpose": r.purpose,
                    "amount": use_amount,
                    "raw_amount": use_amount,
                    "face_value": r.face_value if hasattr(r, 'face_value') else None,
                    "record_date": r.record_date if hasattr(r, 'record_date') else None
                })

        bm_by_symbol = defaultdict(list)
        for bm in bm_records:
            # Dynamically heal BM amounts
            bm_amt, bm_type = FieldMapper._parse_dividend(bm.purpose, None)
            if bm_amt is not None and bm.extracted_dividend_amount != bm_amt:
                bm.extracted_dividend_amount = bm_amt

            bm_by_symbol[bm.symbol.upper()].append(bm)

        event_symbols = set(ca_by_symbol.keys()).union(set(bm_by_symbol.keys()))
        target_symbols = event_symbols

        for sym in target_symbols:
            history = ca_by_symbol.get(sym, [])
            bms = bm_by_symbol.get(sym, [])
            chained_history = []

            for h in history:
                if h.get('dividend_type') in ['Bonus', 'Split', 'Demerger']:
                     if not h.get('purpose') or h.get('dividend_type') not in h.get('purpose', ''):
                          h['purpose'] = h.get('purpose', '') + f" ({h.get('dividend_type')} action)"
                else:
                    ca_date = h['ex_date_obj'] or h.get('announcement_date_obj')
                    if ca_date:
                        best_bm = None
                        min_diff = float('inf')
                        for bm in bms:
                            if bm.extracted_dividend_type == h['dividend_type'] or not bm.extracted_dividend_type:
                                if bm.date:
                                    diff = (ca_date - bm.date).days
                                    if -10 <= diff <= 60 and abs(diff) < min_diff:
                                        if h.get('amount') is not None and bm.extracted_dividend_amount is not None:
                                            if float(h['amount']) != float(bm.extracted_dividend_amount):
                                                continue
                                        min_diff = abs(diff)
                                        best_bm = bm
                        if best_bm:
                            h['broadcast_date'] = best_bm.broadcast_date
                            best_ann_date = best_bm.meeting_date or best_bm.broadcast_date or best_bm.date
                            if hasattr(best_ann_date, 'date'):
                                best_ann_date = best_ann_date.date()
                            h['announcement_date_obj'] = best_ann_date
                            if not h.get('amount') and best_bm.extracted_dividend_amount:
                                h['amount'] = best_bm.extracted_dividend_amount
                                h['raw_amount'] = best_bm.extracted_dividend_amount
                            bms.remove(best_bm)
                chained_history.append(h)

            def safe_date_sort(x):
                d = x.meeting_date or x.broadcast_date or x.date
                if d is None:
                    return datetime.date.min
                if hasattr(d, 'date'):
                    return d.date()
                return d

            bms.sort(key=safe_date_sort, reverse=True)

            deduplicated_bms = []
            for bm in bms:
                is_duplicate = False
                bm_date = safe_date_sort(bm)

                for existing in deduplicated_bms:
                    existing_date = existing['sort_date']

                    if bm_date and existing_date and bm_date != datetime.date.min and existing_date != datetime.date.min:
                        diff_days = abs((bm_date - existing_date).days)
                        if diff_days == 0 or (diff_days <= 180 and bm.extracted_dividend_type == existing['bm'].extracted_dividend_type):
                            is_duplicate = True
                            if not existing['extracted_dividend_amount'] and bm.extracted_dividend_amount:
                                existing['extracted_dividend_amount'] = bm.extracted_dividend_amount
                            break

                if not is_duplicate:
                    deduplicated_bms.append({
                        'bm': bm,
                        'sort_date': bm_date,
                        'extracted_dividend_amount': bm.extracted_dividend_amount
                    })

            for dedup_item in deduplicated_bms:
                bm = dedup_item['bm']
                amt = dedup_item['extracted_dividend_amount']
                if bm.date and bm.date < today - datetime.timedelta(days=180):
                    continue
                purpose_lower = (bm.purpose or '').lower()

                is_valid_standalone = False
                if amt is not None:
                    is_valid_standalone = True
                elif bm.date and bm.date >= today:
                    is_valid_standalone = True
                elif 'dividend' in purpose_lower:
                    is_valid_standalone = True

                if is_valid_standalone:
                    bm_ann_date = bm.meeting_date or bm.broadcast_date or bm.date
                    if hasattr(bm_ann_date, 'date'):
                        bm_ann_date = bm_ann_date.date()

                    is_history_duplicate = False
                    if amt is not None:
                        for h in chained_history:
                            # If the amounts match exactly and it's within 300 days OR if they don't have amounts but are within 60 days
                            h_date = h.get('announcement_date_obj') or h.get('ex_date_obj')
                            if h_date:
                                if hasattr(h_date, 'date'): h_date = h_date.date()
                            if h_date and bm_ann_date:
                                if h.get('amount') == amt and h.get('dividend_type') == (bm.extracted_dividend_type or 'Interim'):
                                    if abs((h_date - bm_ann_date).days) <= 300:
                                        is_history_duplicate = True
                                        break
                                elif h.get('dividend_type') == (bm.extracted_dividend_type or 'Interim') and abs((h_date - bm_ann_date).days) <= 60:
                                    is_history_duplicate = True
                                    # Update the historical one if it doesn't have an amount
                                    if h.get('amount') is None:
                                        h['amount'] = amt
                                        h['raw_amount'] = amt
                                        h['announcement_date_obj'] = bm_ann_date
                                    break

                    if not is_history_duplicate:
                        chained_history.append({
                            "ex_date": 'Record date not yet declared',
                            "ex_date_obj": None,
                            "broadcast_date": bm.broadcast_date,
                            "announcement_date_obj": bm_ann_date,
                            "dividend_type": bm.extracted_dividend_type or 'Interim',
                            "purpose": bm.purpose or "Dividend Declared in Board Meeting",
                            "amount": amt,
                            "raw_amount": amt,
                            "face_value": None,
                            "record_date": None
                        })

            def get_sort_key(x):
                if x.get('ex_date_obj'): return x['ex_date_obj']
                ann_dt = x.get('announcement_date_obj')
                if ann_dt is None:
                    return datetime.date.min
                if hasattr(ann_dt, 'date'):
                    return ann_dt.date()
                return ann_dt

            chained_history.sort(key=get_sort_key, reverse=True)
            ca_by_symbol[sym] = chained_history

        # We purposely do not alter the amounts with ratios here. The Dividend Databank MUST reflect the pure, raw amounts.
        # Downstream routes (like /api/special-sit/dividends) should handle the split/bonus math dynamically if needed.

        # When force is false, we want to UPSERT instead of delete all history.
        # This solves the "takes a hell lot of time" issue and properly updates rows.

        added_count = 0
        updated_count = 0

        for sym, history in ca_by_symbol.items():
            # If we are not forcing, let's fetch existing rows for this symbol to avoid blind inserts
            existing_rows = []

            # Fetch existing rows for both force and not force, but if force we insert all anyway.
            # Wait, if force, the table is empty!
            if not force:
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
                if not force:
                    for row in existing_rows:
                        # Match by identical ex-date OR identical announcement date OR same type within recent window
                        if row.dividend_type == h.get('dividend_type'):
                            if row.ex_date and ex_date_val and row.ex_date == ex_date_val:
                                match = row
                                break
                            if row.announcement_date and h.get('announcement_date_obj') and row.announcement_date == h.get('announcement_date_obj'):
                                match = row
                                break

                            # If no exact date match, check if it's an awaited record we are updating
                            if row.is_awaited and abs((row.date - final_date).days) < 60:
                                match = row
                                break

                if match:
                    # UPDATE existing row
                    match.date = final_date
                    match.ex_date = ex_date_val
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

                    if h.get('face_value') is not None:
                        match.face_value = h.get('face_value')

                    if h.get('purpose'):
                        match.purpose = h.get('purpose')
                    if h.get('record_date'):
                        match.record_date = h.get('record_date')
                    match.is_awaited = is_awaited
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
                        is_synthetic=h.get('is_synthetic', False)
                    )
                    db.add(new_item)
                    if not force:
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
    from backend.infrastructure.db import SessionLocal
    from backend.ingest.nse_models import CorporateAction, BoardMeeting, DividendDatabank
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
                ann_date = r.broadcast_date or r.date
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
                ann_date = r.broadcast_date or r.date
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

        event_symbols = set(ca_by_symbol.keys()).union(set(bm_by_symbol.keys()))
        target_symbols = event_symbols

        for sym in target_symbols:
            ca_history = ca_by_symbol.get(sym, [])
            bms = bm_by_symbol.get(sym, [])

            combined_actions = list(ca_history)

            # 1. Synthesize Board Meetings into Actions if they don't have one
            for m in bms:
                purpose_lower = (m.purpose or '').lower()
                has_amount = m.extracted_dividend_amount is not None
                is_agm = 'agm' in purpose_lower or 'annual general meeting' in purpose_lower or re.search(r'\bagm\b', purpose_lower)

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
                                    if diff_days <= 180:
                                        has_linked_action = True
                                        if (a.get('amount') is None or a.get('amount') == "-") and m.extracted_dividend_amount:
                                            a['amount'] = m.extracted_dividend_amount
                                            a['raw_amount'] = m.extracted_dividend_amount
                                        if not a.get('dividend_type') or a.get('dividend_type') == '-':
                                            a['dividend_type'] = m.extracted_dividend_type or 'Final'
                                        a['_matchedMeeting'] = m
                                        break

                                a_purpose = (a.get('purpose') or '').lower()
                                if not a_date and (a_purpose.find('not yet declared') != -1 or a_purpose.find('dividend (') != -1 or a_purpose.find('dividend') != -1):
                                    is_time_match = True
                                    if a.get('broadcast_date') and m.meeting_date:
                                        b_date = a.get('broadcast_date')
                                        if hasattr(b_date, 'date'): b_date = b_date.date()
                                        meet_date = m.meeting_date
                                        if hasattr(meet_date, 'date'): meet_date = meet_date.date()
                                        diff_days = abs((b_date - meet_date).days)
                                        if diff_days > 30: is_time_match = False

                                    if is_time_match:
                                        if (a.get('amount') is None or a.get('amount') == "-") and m.extracted_dividend_amount:
                                            a['amount'] = m.extracted_dividend_amount
                                            a['raw_amount'] = m.extracted_dividend_amount
                                        if not a.get('dividend_type') or a.get('dividend_type') == '-':
                                            a['dividend_type'] = m.extracted_dividend_type or 'Final'
                                        has_linked_action = True
                                        a['_matchedMeeting'] = m
                                        break

                    if not has_linked_action:
                        # Create Synthetic
                        amount = m.extracted_dividend_amount if m.extracted_dividend_amount is not None else None
                        if amount is None and getattr(m, 'parsed_dividend_amount', None) is not None:
                             amount = m.parsed_dividend_amount

                        div_type = '-'
                        if 'dividend' in purpose_lower or has_amount:
                            div_type = 'Dividend'
                            if 'interim' in purpose_lower: div_type = 'Interim'
                            if 'special' in purpose_lower: div_type = 'Special'
                            if 'final' in purpose_lower: div_type = 'Final'

                            if amount is None:
                                match = re.search(r'(?:rs\.?|rupees?|re\.?)\s*([0-9]+(?:\.[0-9]+)?)|([0-9]+(?:\.[0-9]+)?)\s*\/\-|dividend\s+of\s+([0-9]+(?:\.[0-9]+)?)|dividend.*?\s+([0-9]+(?:\.[0-9]+)?)\s+per|dividend\s*-\s*(?:rs\.?|rupees?|re\.?)\s*([0-9]+(?:\.[0-9]+)?)', purpose_lower)
                                if match:
                                    amount = next((g for g in match.groups() if g is not None), None)

                        elif is_agm and 'dividend' not in purpose_lower and not has_amount:
                            div_type = 'AGM'
                        elif 'bonus' in purpose_lower:
                            div_type = 'Bonus'
                        elif 'split' in purpose_lower or 'sub-division' in purpose_lower:
                            div_type = 'Split'

                        combined_actions.append({
                            "symbol": sym,
                            "purpose": m.purpose,
                            "dividend_type": div_type,
                            "ex_date": None,
                            "ex_date_obj": None,
                            "broadcast_date": m.broadcast_date or m.date,
                            "amount": amount,
                            "raw_amount": amount,
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

            def get_sort_date_syn(x):
                m = x.get('_matchedMeeting')
                d = m.broadcast_date or m.date if m else x.get('broadcast_date')
                return safe_date(d)

            group_synthetics.sort(key=get_sort_date_syn, reverse=True)

            dedup_syns = []
            for syn in group_synthetics:
                is_duplicate = False
                syn_m = syn.get('_matchedMeeting')
                syn_date = safe_date(syn_m.meeting_date if syn_m else None)

                for ex in dedup_syns:
                    ex_m = ex.get('_matchedMeeting')
                    ex_date = safe_date(ex_m.meeting_date if ex_m else None)

                    if syn_date != datetime.date.min and ex_date != datetime.date.min:
                        diff = abs((syn_date - ex_date).days)
                        if diff <= 60 and syn.get('dividend_type') == ex.get('dividend_type'):
                            is_duplicate = True
                            if syn_m and (not ex_m or safe_date(syn_m.meeting_date) > safe_date(ex_m.meeting_date)):
                                ex['_matchedMeeting'] = syn_m
                            if (ex.get('amount') is None or ex.get('amount') == "-") and syn.get('amount') is not None:
                                ex['amount'] = syn.get('amount')
                                ex['raw_amount'] = syn.get('raw_amount')
                            break
                if not is_duplicate:
                    dedup_syns.append(syn)

            final_actions = []
            for syn in dedup_syns:
                matched = False
                syn_date_val = safe_date(syn.get('broadcast_date') or syn.get('date'))

                group_officials.sort(key=lambda x: abs((safe_date(x.get('ex_date_obj') or x.get('broadcast_date') or x.get('date')) - syn_date_val).days) if syn_date_val != datetime.date.min else 9999)

                for off in group_officials:
                    off_date_val = safe_date(off.get('ex_date_obj') or off.get('broadcast_date') or off.get('date'))
                    if syn_date_val != datetime.date.min and off_date_val != datetime.date.min:
                        diff_days = (off_date_val - syn_date_val).days
                        if -10 <= diff_days <= 180 and (syn.get('dividend_type') == off.get('dividend_type') or syn.get('dividend_type') == '-' or off.get('dividend_type') == '-'):
                            if off.get('amount') is None or off.get('amount') == "-":
                                off['amount'] = syn.get('amount')
                                off['raw_amount'] = syn.get('raw_amount')

                            syn_m = syn.get('_matchedMeeting')
                            off_m = off.get('_matchedMeeting')
                            if not off_m or (syn_m and safe_date(syn_m.meeting_date) > safe_date(off_m.meeting_date)):
                                off['_matchedMeeting'] = syn_m

                            matched = True
                            break
                if not matched:
                    final_actions.append(syn)

            for off in group_officials:
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
                    "announcement_date_obj": action.get('announcement_date_obj') or action.get('broadcast_date'),
                    "broadcast_date": action.get('broadcast_date'),
                    "board_meeting_date": bm_date,
                    "dividend_type": action.get('dividend_type'),
                    "purpose": action.get('purpose'),
                    "amount": action.get('amount'),
                    "raw_amount": action.get('raw_amount'),
                    "face_value": action.get('face_value'),
                    "is_synthetic": action.get('is_synthetic', False),
                    "record_date": action.get('record_date')
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
                        if row.dividend_type == h.get('dividend_type'):
                            if row.ex_date and ex_date_val and row.ex_date == ex_date_val:
                                match = row
                                break
                            if row.announcement_date and h.get('announcement_date_obj') and row.announcement_date == h.get('announcement_date_obj'):
                                match = row
                                break

                            # If no exact date match, check if it's an awaited record we are updating
                            if row.is_awaited and abs((row.date - final_date).days) < 60:
                                match = row
                                break

                if match:
                    # UPDATE existing row
                    match.date = final_date
                    match.ex_date = ex_date_val
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

                    if h.get('face_value') is not None:
                        match.face_value = h.get('face_value')

                    if h.get('purpose'):
                        match.purpose = h.get('purpose')
                    elif match.purpose is None:
                        match.purpose = h.get('purpose')
                    if h.get('record_date'):
                        match.record_date = h.get('record_date')
                    match.is_awaited = is_awaited
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
                        is_synthetic=h.get('is_synthetic', False)
                    )
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
