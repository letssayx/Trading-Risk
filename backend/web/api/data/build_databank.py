from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc
import datetime
from collections import defaultdict
import re

from backend.infrastructure.db import get_db, SessionLocal
from backend.ingest.nse_models import CorporateAction, BoardMeeting, DividendDatabank

router = APIRouter()

def _run_build_databank(force: bool):
    db = SessionLocal()
    try:
        if force:
            db.query(DividendDatabank).delete()
            db.commit()

        today = datetime.date.today()

        ca_query = db.query(CorporateAction).filter(
            or_(
                CorporateAction.parsed_dividend_amount != None,
                CorporateAction.dividend_type.in_(['Bonus', 'Split', 'Demerger']),
                CorporateAction.purpose.ilike('%dividend%'),
                CorporateAction.purpose.ilike('%intdiv%'),
                CorporateAction.purpose.ilike('%int div%'),
                CorporateAction.purpose.ilike('%findiv%'),
                CorporateAction.purpose.ilike('%fin div%')
            )
        )

        bm_query = db.query(BoardMeeting).filter(
            or_(
                BoardMeeting.purpose.ilike('%dividend%'),
                BoardMeeting.purpose.ilike('%intdiv%'),
                BoardMeeting.purpose.ilike('%int div%'),
                BoardMeeting.purpose.ilike('%findiv%'),
                BoardMeeting.purpose.ilike('%fin div%'),
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
                return # Nothing to do

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

            if r.dividend_type in ['Bonus', 'Split', 'Demerger']:
                # Extract ratio from purpose
                ratio = 1.0
                purpose_lower = (r.purpose or "").lower()
                if r.dividend_type == 'Bonus':
                    # e.g., "Bonus 1:2" means for every 2 shares held, 1 bonus is given -> factor is (2+1)/2 = 1.5
                    match = re.search(r'(\d+)\s*:\s*(\d+)', purpose_lower)
                    if match:
                        bonus_shares = float(match.group(1))
                        held_shares = float(match.group(2))
                        if held_shares > 0:
                            ratio = held_shares / (held_shares + bonus_shares)
                elif r.dividend_type == 'Split':
                    # e.g., "Face Value Split from Rs.10 to Rs.5" or "From Rs 10/- Per Share To Rs 5/- Per Share"
                    match = re.search(r'from\s*(?:rs\.?|re\.?|rupees?)?\s*(\d+(?:\.\d+)?).*?to\s*(?:rs\.?|re\.?|rupees?)?\s*(\d+(?:\.\d+)?)', purpose_lower)
                    if match:
                        old_fv = float(match.group(1))
                        new_fv = float(match.group(2))
                        if old_fv > 0:
                            ratio = new_fv / old_fv
                    else:
                        # fallback ratio e.g., "Sub-division 1:10"
                        match2 = re.search(r'(\d+)\s*:\s*(\d+)', purpose_lower)
                        if match2:
                            new_shares = float(match2.group(1))
                            old_shares = float(match2.group(2))
                            # often it's old:new or new:old depending on format. Usually old:new = 1:10
                            if old_shares > 0 and new_shares > 0:
                                if new_shares > old_shares:
                                    ratio = old_shares / new_shares
                                else:
                                    ratio = new_shares / old_shares
                elif r.dividend_type == 'Demerger':
                    # Demergers typically split value, hard to parse ratio accurately from string usually.
                    # A common placeholder is 0.5 or checking the specific text.
                    # Let's see if there's a ratio in the string e.g. "1:1"
                    match3 = re.search(r'(\d+)\s*:\s*(\d+)', purpose_lower)
                    if match3:
                        new_shares = float(match3.group(1))
                        old_shares = float(match3.group(2))
                        if old_shares > 0 and new_shares > 0:
                            ratio = old_shares / (old_shares + new_shares)
                    else:
                        # Default heuristic for demerger: reduce historical dividends by half
                        # to prevent massive over-forecasting unless manually overridden.
                        ratio = 0.5

                if ratio != 1.0 and r.date:
                    adjustments_by_symbol[sym].append({
                        "date": r.date,
                        "ratio": ratio
                    })
            elif r.parsed_dividend_amount is not None or (r.purpose and 'dividend' in r.purpose.lower()):
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
                    "amount": r.parsed_dividend_amount,
                    "raw_amount": r.parsed_dividend_amount
                })

        bm_by_symbol = defaultdict(list)
        for bm in bm_records:
            bm_by_symbol[bm.symbol.upper()].append(bm)

        # Compile the chain of events strictly without data-loss deductions
        # We only care about symbols that are in the F&O universe AND have upcoming events or history
        event_symbols = set(ca_by_symbol.keys()).union(set(bm_by_symbol.keys()))
        target_symbols = event_symbols

        for sym in target_symbols:
            history = ca_by_symbol.get(sym, [])
            bms = bm_by_symbol.get(sym, [])
            chained_history = []

            # Keep all real Corporate Actions
            for h in history:
                # We match to a BM just to get its intimation date (broadcast_date), nothing else. We don't delete anything.
                if h.get('dividend_type') not in ['Bonus', 'Split', 'Demerger']:
                    # Sort board meetings by proximity to the corporate action to find the best match
                    ca_date = h['ex_date_obj'] or h.get('announcement_date_obj')
                    if ca_date:
                        best_bm = None
                        min_diff = float('inf')
                        for bm in bms:
                            if bm.extracted_dividend_type == h['dividend_type'] or not bm.extracted_dividend_type:
                                if bm.date:
                                    diff = (ca_date - bm.date).days
                                    # Accept if CA happens -10 to 180 days after BM, matching Databank logic
                                    if -10 <= diff <= 180 and abs(diff) < min_diff:
                                        # Strict amount match if both have it
                                        if h.get('amount') and bm.extracted_dividend_amount:
                                            if float(h['amount']) != float(bm.extracted_dividend_amount):
                                                continue
                                        min_diff = abs(diff)
                                        best_bm = bm
                        if best_bm:
                            # Pass the exact Board Meeting timestamp instead of the partition date
                            h['broadcast_date'] = best_bm.broadcast_date

                            best_ann_date = best_bm.meeting_date or best_bm.broadcast_date or best_bm.date
                            if hasattr(best_ann_date, 'date'):
                                best_ann_date = best_ann_date.date()

                            h['announcement_date_obj'] = best_ann_date

                            # If the CA is missing an amount but the BM has it, backfill it
                            if not h.get('amount') and best_bm.extracted_dividend_amount:
                                h['amount'] = best_bm.extracted_dividend_amount
                                h['raw_amount'] = best_bm.extracted_dividend_amount
                            bms.remove(best_bm) # Consume the BM so it doesn't duplicate

                chained_history.append(h)

            # Deduplicate synthetics (multiple board meetings for the same event) before appending

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
                        # Merge synthetics if they fall on the exact same date, OR if they are within 60 days of each other and have the same dividend type
                        if diff_days == 0 or (diff_days <= 60 and bm.extracted_dividend_type == existing['bm'].extracted_dividend_type):
                            is_duplicate = True
                            # Update amount if the newer duplicate has it
                            if not existing['extracted_dividend_amount'] and bm.extracted_dividend_amount:
                                existing['extracted_dividend_amount'] = bm.extracted_dividend_amount
                            break

                if not is_duplicate:
                    deduplicated_bms.append({
                        'bm': bm,
                        'sort_date': bm_date,
                        'extracted_dividend_amount': bm.extracted_dividend_amount
                    })

            # Append remaining deduplicated BMs that haven't dropped an official CA yet (Upcoming Dividends/Intimations)
            for dedup_item in deduplicated_bms:
                bm = dedup_item['bm']
                amt = dedup_item['extracted_dividend_amount']
                # Drop unlinked bms older than 180 days (exactly matching the Databank merge window)
                if bm.date and bm.date < today - datetime.timedelta(days=180):
                    continue
                # amt already extracted
                purpose_lower = (bm.purpose or '').lower()

                # To avoid polluting the Special Situations UI with generic "Financial Results" or "AGM" meetings
                # that have no actual declared dividend amount, strictly enforce that an amount must exist.
                # However, we MUST preserve upcoming intimations (meetings that haven't happened yet),
                # because most companies announce upcoming dividends with the purpose "Financial Results & Dividend".
                is_valid_standalone = False
                if amt is not None:
                    is_valid_standalone = True
                elif bm.date and bm.date >= today:
                    # It's an upcoming meeting in the future, we don't have the amount yet. Allow it to show as 'Expected'.
                    is_valid_standalone = True
                elif 'dividend' in purpose_lower:
                    # It's a historical dividend intimation without a CA, allow it even if it mentions financial results since the amount is just pending
                    is_valid_standalone = True

                if is_valid_standalone:
                    bm_ann_date = bm.meeting_date or bm.broadcast_date or bm.date
                    if hasattr(bm_ann_date, 'date'):
                        bm_ann_date = bm_ann_date.date()

                    chained_history.append({
                        "ex_date": 'Record date not yet declared',
                        "ex_date_obj": None,
                        "broadcast_date": bm.broadcast_date,
                        "announcement_date_obj": bm_ann_date,
                        "dividend_type": bm.extracted_dividend_type or 'Interim',
                        "purpose": bm.purpose or "Dividend Declared in Board Meeting",
                        "amount": amt,
                        "raw_amount": amt
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

        # Adjust historical dividends for bonuses and splits
        for sym in target_symbols:
            history = ca_by_symbol.get(sym, [])
            adjustments = adjustments_by_symbol.get(sym, [])
            if adjustments:
                for h in history:
                    if h['ex_date_obj']:
                        adjusted_amount = h.get('raw_amount')
                        if adjusted_amount is not None:
                            # Apply adjustments that happened AFTER this dividend
                            for adj in adjustments:
                                if adj['date'] > h['ex_date_obj']:
                                    adjusted_amount *= adj['ratio']
                            h['amount'] = adjusted_amount


        # Now ca_by_symbol contains the completely clean, deduplicated, and split-adjusted history.
        # We just need to insert it into DividendDatabank


        if force:
            db.query(DividendDatabank).delete()
        else:
            # Incremental: Only delete records for the symbols we are updating
            symbols_to_update = list(ca_by_symbol.keys())
            if symbols_to_update:
                db.query(DividendDatabank).filter(DividendDatabank.symbol.in_(symbols_to_update)).delete(synchronize_session=False)

        db_items = []
        for sym, history in ca_by_symbol.items():
            for h in history:
                ex_date_val = h.get('ex_date_obj')
                is_awaited = False
                if ex_date_val is None:
                    is_awaited = True

                sort_dt = ex_date_val or h.get('announcement_date_obj') or datetime.date.min
                if hasattr(sort_dt, 'date'):
                    sort_dt = sort_dt.date()

                db_items.append(DividendDatabank(
                    date=sort_dt,
                    symbol=sym.upper(),
                    ex_date=ex_date_val,
                    announcement_date=h.get('announcement_date_obj'),
                    broadcast_date=h.get('broadcast_date'),
                    dividend_type=h.get('dividend_type'),
                    amount=h.get('amount'),
                    raw_amount=h.get('raw_amount'),
                    purpose=h.get('purpose'),
                    is_awaited=is_awaited
                ))

        db.bulk_save_objects(db_items)
        db.commit()
    finally:
        db.close()

@router.post("/api/data/dividends/build-databank")
def build_dividend_databank(background_tasks: BackgroundTasks, force: bool = Query(False)):
    """
    Rebuilds the DividendDatabank table.
    """
    background_tasks.add_task(_run_build_databank, force)
    return {"message": "Dividend Databank build triggered in background"}
