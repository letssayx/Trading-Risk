from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_
from typing import List, Dict, Optional
import datetime
from collections import defaultdict
import numpy as np

from backend.infrastructure.db import get_db
from backend.ingest.nse_models import SecurityMaster, BhavcopyFO, BhavcopyEQ, CorporateAction, SymbolMaster, BoardMeeting

router = APIRouter()

@router.get("/api/special-sit/dividends")
def get_special_sit_dividends(db: Session = Depends(get_db)):
    # 1. Fetch all F&O stocks from the latest FO bhavcopy to determine F&O universe
    latest_fo_date = db.query(func.max(BhavcopyFO.trade_date)).scalar()

    if not latest_fo_date:
        return []

    fo_tickers = db.query(BhavcopyFO.ticker_symb).filter(
        BhavcopyFO.trade_date == latest_fo_date,
        BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK'])
    ).distinct().all()

    symbols = [t[0].upper() for t in fo_tickers]

    if not symbols:
        return []

    # Fetch lot sizes from SecurityMaster
    sm_records = db.query(SecurityMaster.ticker_symb, SecurityMaster.new_brd_lot_qty).filter(
        SecurityMaster.ticker_symb.in_(symbols)
    ).all()

    lot_size_map = {s.ticker_symb.upper(): s.new_brd_lot_qty for s in sm_records}

    # Fetch sectors from SymbolMaster
    symbol_master_records = db.query(SymbolMaster.symbol, SymbolMaster.sector_index).filter(
        SymbolMaster.symbol.in_(symbols)
    ).all()

    sector_map = {s.symbol.upper(): s.sector_index for s in symbol_master_records}

    # 2. Fetch Spot prices from latest BhavcopyEQ
    latest_eq_date = db.query(func.max(BhavcopyEQ.trade_date)).scalar()
    spot_prices = {}
    if latest_eq_date:
        eq_records = db.query(BhavcopyEQ.symbol, BhavcopyEQ.close_price).filter(
            BhavcopyEQ.trade_date == latest_eq_date,
            BhavcopyEQ.series == 'EQ',
            BhavcopyEQ.symbol.in_(symbols)
        ).all()
        for r in eq_records:
            spot_prices[r.symbol.upper()] = r.close_price

    # 3. Fetch Future Prices from latest BhavcopyFO
    latest_fo_date = db.query(func.max(BhavcopyFO.trade_date)).scalar()
    futures_map = defaultdict(list)
    if latest_fo_date:
        fo_records = db.query(BhavcopyFO.ticker_symb, BhavcopyFO.expiry_date, BhavcopyFO.close_price).filter(
            BhavcopyFO.trade_date == latest_fo_date,
            BhavcopyFO.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK', 'FUTIVX', 'FUTIRC']),
            BhavcopyFO.ticker_symb.in_(symbols)
        ).order_by(BhavcopyFO.ticker_symb, BhavcopyFO.expiry_date).all()

        for r in fo_records:
            # Append dict containing both price and expiry date
            futures_map[r.ticker_symb.upper()].append({
                "price": r.close_price,
                "expiry": r.expiry_date.strftime("%d-%b") if r.expiry_date else None
            })

    # 4. Fetch Corporate Actions and Board Meetings for the last 10 years
    today = datetime.date.today()
    ten_years_ago = today - datetime.timedelta(days=365*10)

    # We also need splits and bonuses to adjust historical dividends.
    ca_records = db.query(CorporateAction).filter(
        CorporateAction.symbol.in_(symbols),
        CorporateAction.date >= ten_years_ago,
        or_(
            CorporateAction.parsed_dividend_amount != None,
            CorporateAction.dividend_type.in_(['Bonus', 'Split', 'Demerger'])
        )
    ).order_by(desc(CorporateAction.date)).all()

    # Fetch Board Meetings discussing dividends
    bm_records = db.query(BoardMeeting).filter(
        BoardMeeting.symbol.in_(symbols),
        BoardMeeting.date >= ten_years_ago,
        BoardMeeting.purpose.ilike('%dividend%')
    ).order_by(desc(BoardMeeting.date)).all()

    import re

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
        elif r.parsed_dividend_amount is not None:
            ca_by_symbol[sym].append({
                "ex_date": r.ex_date.strftime("%Y-%m-%d") if r.ex_date else None,
                "ex_date_obj": r.ex_date,
                "announcement_date_obj": r.date,
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
    all_symbols = set(ca_by_symbol.keys()).union(set(bm_by_symbol.keys()))

    for sym in all_symbols:
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
                                # Accept if CA happens -10 to 60 days after BM, matching the Databank logic
                                if -10 <= diff <= 60 and abs(diff) < min_diff:
                                    # Strict amount match if both have it
                                    if h.get('amount') and bm.extracted_dividend_amount:
                                        if float(h['amount']) != float(bm.extracted_dividend_amount):
                                            continue
                                    min_diff = abs(diff)
                                    best_bm = bm
                    if best_bm:
                        h['broadcast_date'] = best_bm.broadcast_date or h.get('broadcast_date')
                        h['announcement_date_obj'] = best_bm.date
                        # If the CA is missing an amount but the BM has it, backfill it
                        if not h.get('amount') and best_bm.extracted_dividend_amount:
                            h['amount'] = best_bm.extracted_dividend_amount
                            h['raw_amount'] = best_bm.extracted_dividend_amount
                        bms.remove(best_bm) # Consume the BM so it doesn't duplicate

            chained_history.append(h)

        # Append remaining BMs that haven't dropped an official CA yet (Upcoming Dividends/Intimations)
        for bm in bms:
            # Drop unlinked bms older than 180 days to prevent very old duplicates from surfacing,
            # but allow enough window (similar to Databank) for genuine delayed ex-dates.
            if bm.date and bm.date < today - datetime.timedelta(days=180):
                continue
            amt = bm.extracted_dividend_amount
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
            elif 'dividend' in purpose_lower and not any(x in purpose_lower for x in ['financial results', 'agm', 'annual general meeting', 'postponed']):
                # It's a pure historical dividend intimation without a CA
                is_valid_standalone = True

            if is_valid_standalone:
                chained_history.append({
                    "ex_date": 'Record date not yet declared',
                    "ex_date_obj": None,
                    "announcement_date_obj": bm.date,
                    "broadcast_date": bm.broadcast_date,
                    "dividend_type": bm.extracted_dividend_type or 'Interim',
                    "purpose": bm.purpose or "Dividend Declared in Board Meeting",
                    "amount": amt,
                    "raw_amount": amt
                })

        chained_history.sort(key=lambda x: x['ex_date_obj'] if x['ex_date_obj'] else (x.get('announcement_date_obj') or datetime.date.min), reverse=True)
        ca_by_symbol[sym] = chained_history

    # Adjust historical dividends for bonuses and splits
    for sym in all_symbols:
        history = ca_by_symbol.get(sym, [])
        adjustments = adjustments_by_symbol.get(sym, [])
        if adjustments:
            for h in history:
                if h['ex_date_obj']:
                    adjusted_amount = h['raw_amount']
                    # Apply adjustments that happened AFTER this dividend
                    for adj in adjustments:
                        if adj['date'] > h['ex_date_obj']:
                            adjusted_amount *= adj['ratio']
                    h['amount'] = adjusted_amount

    # 5. Process data and generate "guesstimates" using Seasonal Cycle Detection
    results = []

    def get_doy(d): return d.timetuple().tm_yday
    def circ_diff(d1, d2):
        diff = abs(d1 - d2)
        return min(diff, 365 - diff)

    for sym in symbols:
        history = ca_by_symbol.get(sym, [])
        spot = spot_prices.get(sym)
        futures = futures_map.get(sym, [])

        # Add >2% extraordinary flag to historical records
        for h in history:
            h['is_above_2_percent'] = False
            # Fetch the closing price prior to the announcement (broadcast_date) to determine extra-ordinary status.
            # In a real scenario, this requires a DB query per record or a bulk fetch. To prevent N+1 queries freezing the API,
            # we query the closest EQ close price prior to the broadcast date.

            # Prefer broadcast date (announcement date), fallback to announcement_date_obj, then ex_date_obj
            ref_date = h.get('broadcast_date') or h.get('announcement_date_obj') or h.get('ex_date_obj')
            if ref_date and h['amount']:
                # Simple fallback: query the DB directly here for now. It might be slow, but it's correct.
                # (Ideally, we'd pre-fetch all needed historical prices).
                # To avoid N+1 we should bulk fetch, but let's just do a single query for now as a fix.
                try:
                    pass
                    # If broadcast date has a time after 15:30:00, use <= ref_date.date()
                    # If broadcast date has a time before 15:30:00, use < ref_date.date()
                    # If ref_date is just a date, use < ref_date

                    price_query = db.query(BhavcopyEQ.close_price).filter(
                        BhavcopyEQ.symbol == sym,
                        BhavcopyEQ.series == 'EQ'
                    )

                    if isinstance(ref_date, datetime.datetime):
                        target_time = datetime.time(15, 30, 0)
                        if ref_date.time() >= target_time:
                            # after or exactly at market close, we can use the same day's closing price
                            price_query = price_query.filter(BhavcopyEQ.trade_date <= ref_date.date())
                        else:
                            # before or during market hours, we MUST use the previous day's closing price
                            price_query = price_query.filter(BhavcopyEQ.trade_date < ref_date.date())
                    else:
                        # As per user instruction, if we are completely unsure of the exact time, default to checking the same day's price
                        if hasattr(ref_date, "date"):
                            price_query = price_query.filter(BhavcopyEQ.trade_date <= ref_date.date())
                        else:
                            price_query = price_query.filter(BhavcopyEQ.trade_date <= ref_date)

                    hist_price = price_query.order_by(BhavcopyEQ.trade_date.desc()).first()

                    if hist_price and hist_price[0] and hist_price[0] > 0:
                        if (h['amount'] / hist_price[0]) * 100 >= 2.0:
                            h['is_above_2_percent'] = True
                except Exception:
                    pass

        last_type = "-"
        last_ex_date = "-"
        last_amount = None
        is_above_2_percent = False

        expected_amount = None
        expected_highly_likely = None
        expected_less_likely = None
        expected_type = None
        expected_amount_compare = None
        board_meeting_date = None

        if history:
            # Determine nearest upcoming board meeting (if any exists in future or today)
            bms_for_sym = bm_by_symbol.get(sym, [])
            upcoming_bms = [bm for bm in bms_for_sym if bm.date and bm.date >= today]
            upcoming_bms.sort(key=lambda x: x.date)

            if upcoming_bms:
                # Store it as an ISO string so JS can parse it, preserving time if broadcast_date exists
                bm = upcoming_bms[0]
                if bm.meeting_date:
                     board_meeting_date = bm.meeting_date.isoformat()
                elif bm.broadcast_date:
                     board_meeting_date = bm.broadcast_date.isoformat()
                else:
                     # Date only
                     board_meeting_date = bm.date.isoformat() + "T00:00:00"


            # Most recent overall dividend (just for table display purposes)
            last = history[0]
            last_type = last['dividend_type'] or '-'
            last_ex_date = last['ex_date'] or '-'
            last_amount = last['amount']

            # User reported that dividends with past ex-dates are incorrectly triggering the extra-ordinary = yes flag for future forecasts.
            # Only set it for the main row if it's the latest event AND the ex_date hasn't passed yet or is today.
            # If it's a past event, the main row shouldn't inherit its >2% flag, as we are looking ahead.
            latest_ex_date_obj = last.get('ex_date_obj')
            if latest_ex_date_obj and latest_ex_date_obj >= today:
                is_above_2_percent = last.get('is_above_2_percent', False)
            elif not latest_ex_date_obj: # e.g. "Record date not yet declared"
                is_above_2_percent = last.get('is_above_2_percent', False)
            else:
                is_above_2_percent = False

            # Extra rule: Also inherit the >2% flag if there is an upcoming board meeting,
            # meaning the current/next action is still live and the sub-row flag should bubble up
            if board_meeting_date and not is_above_2_percent:
                is_above_2_percent = last.get('is_above_2_percent', False)

            # Sort ascending for cycle processing
            history_asc = sorted(history, key=lambda x: x['ex_date_obj'] if x['ex_date_obj'] else datetime.date.min)

            final_cluster = []
            interim_clusters = []

            five_years_ago = today - datetime.timedelta(days=365*5)
            recent_hist = [h for h in history_asc if h['ex_date_obj'] and h['ex_date_obj'] >= five_years_ago]

            for h in recent_hist:
                # Skip special dividends entirely for forecasting
                if 'special' in (h.get('purpose') or '').lower() or h.get('dividend_type') == 'Special':
                    continue

                if h.get('dividend_type') == 'Final':
                    final_cluster.append(h)
                else:
                    doy = get_doy(h['ex_date_obj'])
                    placed = False
                    for c in interim_clusters:
                        mean_doy = sum(get_doy(x['ex_date_obj']) for x in c) / len(c)
                        if circ_diff(doy, mean_doy) <= 90: # 90 days threshold to handle larger shifts like May->June
                            if not any(x['ex_date_obj'].year == h['ex_date_obj'].year for x in c):
                                c.append(h)
                                placed = True
                                break
                    if not placed:
                        interim_clusters.append([h])

            clusters = [final_cluster] + interim_clusters if final_cluster else interim_clusters

            # For each cycle, find its next upcoming date
            upcoming_cycles = []
            for c in clusters:
                if not c: continue
                most_recent = c[-1]
                mr_date = most_recent['ex_date_obj']

                # Skip clusters that haven't paid in the last 2 years (kill the cycle)
                if mr_date.year < today.year - 1:
                    continue

                if mr_date >= today:
                    # Already announced for future
                    next_date = mr_date
                    is_announced = True
                else:
                    # Project forward using the exact month and day of the most recent dividend in this cycle
                    # Next expected year is mr_date.year + 1
                    next_year = mr_date.year + 1

                    try:
                        next_date = datetime.date(next_year, mr_date.month, mr_date.day)
                    except ValueError:
                        # handle leap day edge case
                        next_date = datetime.date(next_year, mr_date.month, mr_date.day - 1)

                    while next_date < today - datetime.timedelta(days=15): # grace period
                        next_year += 1
                        try:
                            next_date = datetime.date(next_year, mr_date.month, mr_date.day)
                        except ValueError:
                            next_date = datetime.date(next_year, mr_date.month, mr_date.day - 1)

                    is_announced = False

                # Calculate cycle growth (using CAGR to handle skipped years)
                growth_rates = []
                for i in range(1, len(c)):
                    prev_amt = c[i-1]['amount']
                    curr_amt = c[i]['amount']
                    days_diff = (c[i]['ex_date_obj'] - c[i-1]['ex_date_obj']).days
                    years_diff = round(days_diff / 365)

                    if years_diff >= 1 and prev_amt and curr_amt and prev_amt > 0:
                        pct_change = (curr_amt - prev_amt) / prev_amt
                        # Annualize the percent change roughly if it spans multiple years
                        annualized_pct_change = pct_change / years_diff
                        annualized_pct_change = min(max(annualized_pct_change, -1.0), 0.5) # Cap between -100% and +50%
                        growth_rates.append(annualized_pct_change)

                avg_growth = np.mean(growth_rates) if growth_rates else 0
                exp_amt = most_recent['amount'] * (1 + avg_growth) if most_recent['amount'] else None

                # Less likely months
                highly_likely_month = next_date.month
                all_months = set(x['ex_date_obj'].month for x in c)
                less_likely_m = all_months - {highly_likely_month}

                upcoming_cycles.append({
                    'next_date': next_date,
                    'is_announced': is_announced,
                    'exp_amt': None if is_announced else exp_amt,
                    'highly_likely_month': highly_likely_month,
                    'less_likely_months': less_likely_m,
                    'type': most_recent.get('dividend_type') or 'Interim',
                    'last_amt_in_cycle': most_recent['amount']
                })

            # Pick the chronologically next cycle
            if upcoming_cycles:
                upcoming_cycles.sort(key=lambda x: x['next_date'])
                next_cycle = upcoming_cycles[0]

                if next_cycle['is_announced']:
                    # Use the actual announced amount as the "expected" amount
                    expected_amount = next_cycle['last_amt_in_cycle']
                    expected_amount_compare = next_cycle['last_amt_in_cycle']
                    expected_type = next_cycle['type']
                    expected_highly_likely = f"Announced: {next_cycle['next_date'].strftime('%d-%m-%Y')}"
                    expected_less_likely = "Confirmed"
                else:
                    if next_cycle['exp_amt'] is not None:
                        expected_amount = round(next_cycle['exp_amt'], 2)
                        expected_amount_compare = next_cycle['last_amt_in_cycle']
                        expected_type = next_cycle['type']



                    expected_highly_likely = f"Forecasted: {next_cycle['next_date'].strftime('%d-%m-%Y')}"
                    if not expected_less_likely:
                        if next_cycle['less_likely_months']:
                            m_names = [datetime.date(2000, m, 1).strftime('%b') for m in next_cycle['less_likely_months']]
                            expected_less_likely = ", ".join(m_names)
                        else:
                            expected_less_likely = "-"

            # If the last event is Ex-Awaited (amount declared, but no ex-date yet)
            if history:
                latest = history[0]
                if latest.get('amount') and (not latest.get('ex_date') or latest.get('ex_date') == 'Record date not yet declared'):
                    expected_amount = latest['amount']
                    expected_amount_compare = latest['amount']
                    expected_type = latest.get('dividend_type', 'Interim')

                    # If there's an announcement date, use it instead of just generic forecast
                    ann_date = latest.get('announcement_date_obj')
                    if ann_date:
                        expected_highly_likely = f"Announced: {ann_date.strftime('%d-%m-%Y')}"
                        expected_less_likely = "Amount declared, date not yet announced"
                    else:
                        # Instead of "-" use the highly likely date we just forecasted for this cycle if it exists
                        if upcoming_cycles:
                            # Try to find a matching cycle type to use its date
                            matching_cycle = next((c for c in upcoming_cycles if c['type'] == expected_type), upcoming_cycles[0])
                            expected_highly_likely = f"Forecasted: {matching_cycle['next_date'].strftime('%d-%m-%Y')}"
                        else:
                            expected_highly_likely = "-"
                        expected_less_likely = "Amount declared, date not yet announced"

        # Explicitly round expected_amount for json response
        if expected_amount is not None:
            expected_amount = round(float(expected_amount), 2)

        results.append({
            "symbol": sym,
            "lot_size": lot_size_map.get(sym),
            "spot": spot,
            "sector": sector_map.get(sym, "-"),
            "futures": futures[:3], # take up to Future 3
            "last_type": last_type,
            "last_ex_date": last_ex_date,
            "last_amount": last_amount,
            "is_above_2_percent": is_above_2_percent,
            "board_meeting_date": board_meeting_date,
            "expected_amount": expected_amount,
            "expected_amount_compare": expected_amount_compare,
            "expected_type": expected_type,
            "expected_highly_likely": expected_highly_likely,
            "expected_less_likely": expected_less_likely,
            "history": history
        })

    # Sort alphabetical by symbol
    results.sort(key=lambda x: x['symbol'])

    return {
        "eq_date": latest_eq_date.strftime('%Y-%m-%d') if latest_eq_date else None,
        "data": results
    }
