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

    symbols = list(set([t[0].upper() for t in fo_tickers]))

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

    # 4. Fetch from unified DividendDatabank for the last 10 years (Lightning Fast)
    today = datetime.date.today()
    ten_years_ago = today - datetime.timedelta(days=365*10)

    from backend.ingest.nse_models import DividendDatabank
    databank_records = db.query(DividendDatabank).filter(
        DividendDatabank.symbol.in_(symbols),
        DividendDatabank.date >= ten_years_ago
    ).order_by(desc(DividendDatabank.date)).all()

    ca_by_symbol = defaultdict(list)
    for r in databank_records:
        ex_dt_str = 'Record date not yet declared' if r.is_awaited else (r.ex_date.strftime("%Y-%m-%d") if r.ex_date else None)
        ca_by_symbol[r.symbol.upper()].append({
            "ex_date": ex_dt_str,
            "ex_date_obj": r.ex_date,
            "announcement_date_obj": r.announcement_date,
            "broadcast_date": r.broadcast_date,
            "dividend_type": r.dividend_type,
            "purpose": r.purpose,
            "amount": r.amount,
            "raw_amount": r.raw_amount,
            "face_value": r.face_value,
            "eps": r.eps,
            "net_profit": r.net_profit,
            "dps": r.dps,
            "dividend_yield": r.dividend_yield,
            "payout_ratio": r.payout_ratio,
            "agm_date": r.agm_date.strftime("%Y-%m-%d") if r.agm_date else None,
            "agm_announcement_date": r.agm_announcement_date.strftime("%Y-%m-%d") if r.agm_announcement_date else None,
            "fy_year": r.date.year if r.date.month > 3 else r.date.year - 1
        })

    # 4.2 Fetch Bonus/Split actions to dynamically calculate adjustments
    import re
    adjustment_records = db.query(CorporateAction).filter(
        CorporateAction.symbol.in_(symbols),
        CorporateAction.date >= ten_years_ago,
        CorporateAction.dividend_type.in_(['Bonus', 'Split', 'Demerger'])
    ).all()

    adjustments_by_symbol = defaultdict(list)
    for r in adjustment_records:
        sym = r.symbol.upper()
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
            match = re.search(r'from\s*(?:rs\.?\s*|re\.?\s*|rupees?\s*)?(\d+(?:\.\d+)?).*?to\s*(?:rs\.?\s*|re\.?\s*|rupees?\s*)?(\d+(?:\.\d+)?)', purpose_lower)
            if not match:
                match = re.search(r'(?:rs\.?\s*|re\.?\s*|rupees?\s*|face value of\s*)(\d+(?:\.\d+)?)\s*(?:per share)?\s*(?:to|into)\s*(?:rs\.?\s*|re\.?\s*|rupees?\s*|face value of\s*)(\d+(?:\.\d+)?)', purpose_lower)
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


    # 4.5 Fetch Board Meetings for the last 30 days
    recent_bms_date = today - datetime.timedelta(days=30)
    bm_records = db.query(BoardMeeting).filter(
        BoardMeeting.symbol.in_(symbols),
        or_(
            BoardMeeting.date >= recent_bms_date,
            BoardMeeting.meeting_date >= recent_bms_date
        )
    ).all()
    bm_by_symbol = defaultdict(list)
    for bm in bm_records:
        bm_by_symbol[bm.symbol.upper()].append(bm)

    # 5. Process data and generate "guesstimates" using Seasonal Cycle Detection
    results = []

    def get_doy(d): return d.timetuple().tm_yday
    def circ_diff(d1, d2):
        diff = abs(d1 - d2)
        return min(diff, 365 - diff)

    hist_price_map = {}
    if symbols and latest_eq_date:
        try:
            hist_price_map = defaultdict(list)
            # Fetch last 3 years of prices for these symbols to be safe for 2% check
            three_years_ago = latest_eq_date - datetime.timedelta(days=1095)
            all_prices = db.query(BhavcopyEQ.symbol, BhavcopyEQ.trade_date, BhavcopyEQ.close_price).filter(
                BhavcopyEQ.symbol.in_(symbols),
                BhavcopyEQ.series == 'EQ',
                BhavcopyEQ.trade_date >= three_years_ago
            ).order_by(BhavcopyEQ.trade_date).all()
            for r in all_prices:
                hist_price_map[r.symbol.upper()].append((r.trade_date, float(r.close_price)))
        except Exception:
            pass

    for sym in symbols:
        history = ca_by_symbol.get(sym, [])
        spot = spot_prices.get(sym)
        futures = futures_map.get(sym, [])

        # Apply adjustments first
        adjustments = adjustments_by_symbol.get(sym, [])
        if adjustments:
            for h in history:
                h_date = h.get('ex_date_obj') or h.get('announcement_date_obj')
                if h_date:
                    if hasattr(h_date, 'date'):
                        h_date = h_date.date()
                    adjusted_amount = h.get('raw_amount')
                    if adjusted_amount is not None:
                        for adj in adjustments:
                            adj_date = adj['date']
                            if hasattr(adj_date, 'date'):
                                adj_date = adj_date.date()
                            if adj_date > h_date:
                                adjusted_amount *= adj['ratio']
                        h['amount'] = adjusted_amount

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
                    if isinstance(ref_date, datetime.datetime):
                        target_time = datetime.time(15, 30, 0)
                        if ref_date.time() >= target_time:
                            target_date = ref_date.date()
                        else:
                            target_date = ref_date.date() - datetime.timedelta(days=1)
                    else:
                        if hasattr(ref_date, "date"):
                            target_date = ref_date.date()
                        else:
                            target_date = ref_date

                    import bisect
                    sym_prices = hist_price_map.get(sym, [])
                    dates_only = [x[0] for x in sym_prices]
                    idx = bisect.bisect_right(dates_only, target_date)

                    if idx > 0:
                        closest_price = sym_prices[idx - 1][1]
                        if closest_price and closest_price > 0:
                            if (h['amount'] / closest_price) * 100 >= 2.0:
                                h['is_above_2_percent'] = True
                except Exception:
                    pass

        last_type = "-"
        last_ex_date = "-"
        last_amount = None
        last_face_value = "-"
        last_purpose = "-"
        is_above_2_percent = False

        expected_amount = None
        expected_highly_likely = None
        expected_less_likely = None
        expected_type = None
        expected_amount_compare = None
        board_meeting_date = None
        broadcast_date = None

        # Fetch board meetings regardless of if there is history
        bms_for_sym = bm_by_symbol.get(sym, [])

        # Prioritize meetings that actually have a meeting_date set
        upcoming_bms = [bm for bm in bms_for_sym if bm.meeting_date and bm.meeting_date >= today - datetime.timedelta(days=30)]
        upcoming_bms.sort(key=lambda x: x.meeting_date, reverse=True)

        if not upcoming_bms:
             # Fallback to intimation date
             upcoming_bms = [bm for bm in bms_for_sym if bm.date and bm.date >= today - datetime.timedelta(days=30) and not bm.meeting_date]
             upcoming_bms.sort(key=lambda x: x.date, reverse=True)

        if upcoming_bms:
            bm = upcoming_bms[0]
            if bm.meeting_date:
                 board_meeting_date = bm.meeting_date.isoformat()
            else:
                 # DO NOT fallback to broadcast_date or date for the 'Upcoming Meeting' filter,
                 # as it represents when the intimation was received, not when the meeting actually is.
                 board_meeting_date = None

            if bm.broadcast_date:
                 broadcast_date = bm.broadcast_date.strftime('%Y-%m-%dT%H:%M:%S')
            else:
                 broadcast_date = None

        if history:
            # Find the most recent actual dividend (skip standalone splits/bonuses if possible)
            last_div = next((h for h in history if h.get('amount') is not None), history[0])
            last_type = last_div.get('dividend_type') or '-'
            last_ex_date = last_div.get('ex_date') or '-'
            last_amount = last_div.get('amount')
            last_face_value = last_div.get('face_value') or '-'
            last_purpose = last_div.get('purpose') or '-'

            # Check if the event is still Active (Ex-Date >= today or Ex-Awaited)
            is_active = False
            if last_ex_date == '-' or last_ex_date == 'Record date not yet declared':
                # Ex-Awaited
                is_active = True
            elif last_div.get('ex_date_obj') and last_div['ex_date_obj'] >= today:
                # Ex-Date in future or today
                is_active = True

            if is_active:
                is_above_2_percent = last_div.get('is_above_2_percent', False)
            else:
                is_above_2_percent = False

            # Sort ascending for cycle processing
            def get_sort_key_asc(x):
                if x.get('ex_date_obj'): return x['ex_date_obj']
                ann_dt = x.get('announcement_date_obj')
                if ann_dt is None: return datetime.date.min
                if hasattr(ann_dt, 'date'): return ann_dt.date()
                return ann_dt
            history_asc = sorted(history, key=get_sort_key_asc)

            final_cluster = []
            interim_clusters = []

            five_years_ago = today - datetime.timedelta(days=365*5)
            recent_hist = [h for h in history_asc if h['ex_date_obj'] and h['ex_date_obj'] >= five_years_ago]

            for h in recent_hist:
                # Skip special dividends entirely for forecasting
                # if 'special' in (h.get('purpose') or '').lower() or h.get('dividend_type') == 'Special':
#                    continue

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

                        # Add note to check for >2% if forecasted amount is high
                        if spot and expected_amount and (expected_amount / spot) >= 0.02:
                            expected_less_likely = "<span style='color: red;'>check for extra-ordinary</span>"
                            is_above_2_percent = True

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
                # If there's an ex_date that is today or in the future, it's not Ex-Awaited, it's Confirmed.
                has_valid_future_ex_date = False
                if latest.get('ex_date_obj') and latest['ex_date_obj'] >= today:
                    has_valid_future_ex_date = True

                if latest.get('amount') and (not latest.get('ex_date') or latest.get('ex_date') == 'Record date not yet declared') and not has_valid_future_ex_date:
                    # Only apply Ex-Awaited status if we haven't already confirmed an upcoming declared date
                    if expected_less_likely != "Confirmed":
                        expected_amount = latest['amount']
                        expected_amount_compare = latest['amount']
                        expected_type = latest.get('dividend_type', 'Interim')

                        # Sync the >2% flag for Ex-Awaited
                        is_above_2_percent = latest.get('is_above_2_percent', False)

                        if upcoming_cycles:
                            # Try to find a matching cycle type to use its date
                            matching_cycle = next((c for c in upcoming_cycles if c['type'] == expected_type), upcoming_cycles[0])
                            expected_highly_likely = f"Forecasted: {matching_cycle['next_date'].strftime('%d-%m-%Y')}"
                        else:
                            expected_highly_likely = "-"
                        expected_less_likely = "Amount declared, date not yet announced"

            # Check forecasted expected amount for >2% flag regardless of what branch it took above
            if not is_active and spot and expected_amount and (expected_amount / spot) >= 0.02:
                is_above_2_percent = True
                if expected_less_likely == "-" or not expected_less_likely or expected_less_likely == "Confirmed" or expected_less_likely == "Amount declared, date not yet announced":
                    expected_less_likely = "<span style='color: red;'>check for extra-ordinary</span>"
                else:
                    if "check for extra-ordinary" not in expected_less_likely:
                        expected_less_likely += " | <span style='color: red;'>check for extra-ordinary</span>"
        def safe_round_to_05(val):
            try:
                if val is None or val == "" or str(val).strip() in ["N/A", "-"]:
                    return val
                return round(float(val) * 20) / 20
            except (ValueError, TypeError):
                return val

        # Explicitly round expected_amount for json response to nearest 0.05
        expected_amount = safe_round_to_05(expected_amount)

        # We also round historical amounts and last_amount to nearest 0.05 to be clean
        last_amount = safe_round_to_05(last_amount)

        for h in history:
            h['amount'] = safe_round_to_05(h.get('amount'))

        # If it has no history, no upcoming board meetings, and no expectations, we can skip it.
        # But if we just look at the return format, we need to include things that are pending or have history.

        # Calculate Delta DPS and Total FY Dividend
        # We process history which is sorted chronologically descending
        fy_groups = defaultdict(list)
        for h in history:
             fy = h.get('fy_year')
             if fy:
                  fy_groups[fy].append(h)

        # FY Aggregates
        fy_totals = {}
        for fy, items in fy_groups.items():
             tot_div = sum((i.get('amount') or 0) for i in items)
             eps_val = next((i.get('eps') for i in items if i.get('eps') is not None), None)
             fy_totals[fy] = {
                  'total_dps': tot_div,
                  'eps': eps_val
             }

        for h in history:
             fy = h.get('fy_year')
             if fy:
                  h['fy_total_dps'] = fy_totals[fy]['total_dps']
                  # Delta DPS vs Prev Year
                  prev_fy_tot = fy_totals.get(fy - 1)
                  if prev_fy_tot and prev_fy_tot['total_dps']:
                       h['delta_dps_pct'] = round(((fy_totals[fy]['total_dps'] - prev_fy_tot['total_dps']) / prev_fy_tot['total_dps']) * 100, 2)
                  else:
                       h['delta_dps_pct'] = None

                  # Delta EPS vs Prev Year
                  if fy_totals[fy]['eps'] and prev_fy_tot and prev_fy_tot['eps']:
                       h['delta_eps_pct'] = round(((fy_totals[fy]['eps'] - prev_fy_tot['eps']) / abs(prev_fy_tot['eps'])) * 100, 2)
                  else:
                       h['delta_eps_pct'] = None

                  if spot and h.get('amount'):
                       h['dividend_yield'] = round((h['amount'] / spot) * 100, 2)

        last_agm_date = None
        last_agm_announcement_date = None
        if history:
            for h in history:
                if h.get('agm_date'):
                    last_agm_date = h.get('agm_date')
                    last_agm_announcement_date = h.get('agm_announcement_date')
                    break

        if history or board_meeting_date or expected_amount or expected_highly_likely != "-":
            results.append({
                "symbol": sym,
                "lot_size": lot_size_map.get(sym),
                "spot": spot,
                "sector": sector_map.get(sym, "-"),
                "futures": futures[:3], # take up to Future 3
                "last_type": last_type,
                "last_ex_date": last_ex_date,
                "last_amount": last_amount,
                "last_face_value": last_face_value,
                "last_purpose": last_purpose,
                "last_agm_date": last_agm_date,
                "last_agm_announcement_date": last_agm_announcement_date,
                "is_above_2_percent": is_above_2_percent,
                "board_meeting_date": board_meeting_date,
                "broadcast_date": broadcast_date,
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
