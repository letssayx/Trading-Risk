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
                    "amount": None,
                    "raw_amount": None,
                    "face_value": r.face_value if hasattr(r, 'face_value') else None,
                    "record_date": r.record_date if hasattr(r, 'record_date') else None
                })

            elif r.parsed_dividend_amount is not None or (r.purpose and ('dividend' in r.purpose.lower() or 'special' in r.purpose.lower() or 'bonus' in r.purpose.lower() or 'split' in r.purpose.lower())):
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
                    "raw_amount": r.parsed_dividend_amount,
                    "face_value": r.face_value if hasattr(r, 'face_value') else None,
                    "record_date": r.record_date if hasattr(r, 'record_date') else None
                })

        bm_by_symbol = defaultdict(list)
        for bm in bm_records:
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
                                    if -10 <= diff <= 180 and abs(diff) < min_diff:
                                        if h.get('amount') and bm.extracted_dividend_amount:
                                            # If CA amount is smaller than BM amount, they definitely don't match.
                                            # If CA amount is larger, it might be a sum of multiple components (e.g. Final + Special), so we allow it to match the component BM.
                                            if float(h['amount']) < float(bm.extracted_dividend_amount):
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
                        # Only deduplicate if they are the exact same type of dividend.
                        # This prevents dropping a Special dividend that happens on the exact same day as a Final dividend.
                        if bm.extracted_dividend_type == existing['bm'].extracted_dividend_type:
                            if diff_days <= 60:
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
                            h_date = h.get('announcement_date_obj') or h.get('ex_date_obj')
                            if h_date:
                                if hasattr(h_date, 'date'): h_date = h_date.date()

                            if h_date and bm_ann_date:
                                days_diff = abs((h_date - bm_ann_date).days)

                                # Exact match
                                if h.get('amount') == amt and h.get('dividend_type') == (bm.extracted_dividend_type or 'Interim'):
                                    if days_diff <= 300:
                                        is_history_duplicate = True
                                        break

                                # If the BM amount is likely a component of a combined CA sum
                                if h.get('amount') and float(h['amount']) > float(amt):
                                    if days_diff <= 30:
                                        is_history_duplicate = True
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

        for sym in target_symbols:
            history = ca_by_symbol.get(sym, [])
            adjustments = adjustments_by_symbol.get(sym, [])
            if adjustments:
                for h in history:
                    if h['ex_date_obj']:
                        adjusted_amount = h.get('raw_amount')
                        if adjusted_amount is not None:
                            was_adjusted = False
                            for adj in adjustments:
                                if adj['date'] > h['ex_date_obj']:
                                    adjusted_amount *= adj['ratio']
                                    was_adjusted = True
                            h['amount'] = adjusted_amount
                            if was_adjusted:
                                h['purpose'] = f"{h.get('purpose', '')} (Originally Declared: {h.get('raw_amount')})"

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
