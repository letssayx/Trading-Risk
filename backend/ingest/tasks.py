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

        if force:
            db.query(DividendDatabank).delete()
            db.commit()

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

                if match and not force:
                    # UPDATE existing row
                    match.date = final_date
                    match.ex_date = ex_date_val
                    if h.get('announcement_date_obj'):
                        match.announcement_date = h.get('announcement_date_obj')
                    if h.get('broadcast_date'):
                        match.broadcast_date = h.get('broadcast_date')
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
                        record_date=h.get('record_date')
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
