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
