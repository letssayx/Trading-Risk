@shared_task(bind=True, max_retries=3, acks_late=True, reject_on_worker_lost=True)
def build_dividend_databank_task(self, force: bool = False):
    from sqlalchemy import func, or_, desc
    import datetime
    from collections import defaultdict
    import re
    from backend.infrastructure.db import SessionLocal
    from backend.ingest.nse_models import CorporateAction, BoardMeeting, DividendDatabank

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
