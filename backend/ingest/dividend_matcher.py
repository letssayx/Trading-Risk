import datetime

MATCH_WINDOW_DAYS = 180

def _is_final_purpose(purpose_lower: str) -> bool:
    return ('final' in purpose_lower or 'findiv' in purpose_lower or
            'yearly audited' in purpose_lower or 'annual results' in purpose_lower)

def _is_interim_purpose(purpose_lower: str) -> bool:
    return ('interim' in purpose_lower or 'intdiv' in purpose_lower)

def find_best_bm_for_ca(ca, candidate_bms, already_matched_ids):
    """
    candidate_bms: BM rows for this symbol not yet consumed for this TYPE.
    Enforces: one BM can supply at most one dividend per type (Final/Interim/Special) —
    NOT globally exclusive, just exclusive per (bm.id, dividend_type).
    """
    ca_type = ca.get('dividend_type')
    ca_amt = ca.get('amount')
    ca_ex_date = ca.get('ex_date_obj')

    candidates = []
    for bm in candidate_bms:
        if (bm.id, ca_type) in already_matched_ids:
            continue  # this BM already supplied a dividend of this exact type

        bm_date = bm.date
        if hasattr(bm_date, 'date'):
            bm_date = bm_date.date()

        if not bm_date or not ca_ex_date:
            continue

        days_diff = (ca_ex_date - bm_date).days
        if days_diff < -1 or days_diff > MATCH_WINDOW_DAYS:
            continue  # outside the 180-day AGM window — hard reject, not scored down

        bm_purpose = (bm.purpose or '').lower()
        bm_is_final = _is_final_purpose(bm_purpose)
        bm_is_interim = _is_interim_purpose(bm_purpose)
        bm_is_special = 'special' in bm_purpose

        if ca_type == 'Final' and bm_is_interim: continue
        if ca_type == 'Interim' and bm_is_final: continue
        if ca_type == 'Special' and not bm_is_special and (bm_is_final or bm_is_interim):
            continue  # only reject if BM purpose is unambiguously a different type

        bm_amt = bm.extracted_dividend_amount
        if bm_amt is not None and ca_amt is not None:
            try:
                if abs(float(bm_amt) - float(ca_amt)) >= 0.01:
                    continue  # amount mismatch — hard reject, never a candidate
                amount_confidence = 2  # confirmed match
            except ValueError:
                continue
        elif bm_amt is None and ca_amt is not None:
            amount_confidence = 1  # unknown, weak candidate
        else:
            amount_confidence = 0

        candidates.append((amount_confidence, bm_date, bm))

    if not candidates:
        return None

    # Tie-break: prefer confirmed amount match over unknown: THEN prefer EARLIEST bm_date
    # (earliest = the meeting that actually recommended the dividend, not the one nearest ex-date).
    candidates.sort(key=lambda c: (-c[0], c[1]))
    return candidates[0][2]
