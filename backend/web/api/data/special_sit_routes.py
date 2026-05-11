from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_
from typing import List, Dict, Optional
import datetime
from collections import defaultdict
import numpy as np

from backend.infrastructure.db import get_db
from backend.ingest.nse_models import SecurityMaster, BhavcopyFO, BhavcopyEQ, CorporateAction, SymbolMaster

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

    # 4. Fetch Corporate Actions (Dividends, Splits, Bonuses) for the last 10 years
    today = datetime.date.today()
    ten_years_ago = today - datetime.timedelta(days=365*10)

    # We also need splits and bonuses to adjust historical dividends.
    # dividend_type captures "Bonus" and "Split" from our ingest logic.
    ca_records = db.query(CorporateAction).filter(
        CorporateAction.symbol.in_(symbols),
        CorporateAction.date >= ten_years_ago,
        or_(
            CorporateAction.parsed_dividend_amount != None,
            CorporateAction.dividend_type.in_(['Bonus', 'Split', 'Demerger'])
        )
    ).order_by(desc(CorporateAction.date)).all()

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
                "dividend_type": r.dividend_type,
                "purpose": r.purpose,
                "amount": r.parsed_dividend_amount,
                "raw_amount": r.parsed_dividend_amount
            })

    # Deduplicate synthesized records if an official record exists
    for sym, history in ca_by_symbol.items():
        # A synthesized record is one that was generated by our nse_importer board meetings parser.
        # It typically has "not yet declared" OR just "Dividend (" if it parsed the date but isn't a direct CA import yet.
        # Alternatively, we can check if it lacks an ex_date or if it matches exactly.
        # To be safe, we'll consider any record without an ex_date or with a synthesized purpose pattern as synthesized.
        synthesized = []
        official = []
        for h in history:
            is_syn = False
            purp_lower = (h['purpose'] or '').lower()
            if 'not yet declared' in purp_lower:
                is_syn = True
            elif purp_lower.startswith('dividend (') and purp_lower.endswith(')'):
                is_syn = True

            if is_syn:
                synthesized.append(h)
            else:
                official.append(h)

        filtered_history = []
        for syn in synthesized:
            # Check if there is an official record within 90 days after this synthesized record's date
            # with the exact same amount.
            has_official = False
            # Fallback to announcement_date_obj if ex_date_obj is missing
            syn_date = syn['ex_date_obj'] or syn.get('announcement_date_obj')
            if syn_date:
                for off in official:
                    off_date = off['ex_date_obj']
                    if off_date and syn_date <= off_date <= syn_date + datetime.timedelta(days=90):
                        if abs(off['raw_amount'] - syn['raw_amount']) < 0.01:
                            has_official = True
                            break
            if not has_official:
                filtered_history.append(syn)

        filtered_history.extend(official)
        # Sort back by date descending. Prioritize ex_date, fallback to announcement_date
        filtered_history.sort(key=lambda x: x['ex_date_obj'] if x['ex_date_obj'] else (x.get('announcement_date_obj') or datetime.date.min), reverse=True)
        ca_by_symbol[sym] = filtered_history

    # Adjust historical dividends for bonuses and splits
    for sym, history in ca_by_symbol.items():
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

            ref_date = h.get('broadcast_date') or h.get('ex_date_obj')
            if ref_date and h['amount']:
                # Simple fallback: query the DB directly here for now. It might be slow, but it's correct.
                # (Ideally, we'd pre-fetch all needed historical prices).
                # To avoid N+1 we should bulk fetch, but let's just do a single query for now as a fix.
                try:
                    pass
                    # If broadcast date has a time after 15:30:00, use <= ref_date.date()
                    # If broadcast date has a time before 15:30:00, use < ref_date.date()
                    # If ref_date is just a date, use < ref_date

                    price_query = db.query(BhavcopyEQ.close).filter(
                        BhavcopyEQ.symbol == sym
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
                        price_query = price_query.filter(BhavcopyEQ.trade_date < ref_date)

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

        if history:
            # Most recent overall dividend (just for table display purposes)
            last = history[0]
            last_type = last['dividend_type'] or '-'
            last_ex_date = last['ex_date'] or '-'
            last_amount = last['amount']
            is_above_2_percent = last['is_above_2_percent']

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

                if next_cycle['exp_amt'] is not None:
                    expected_amount = round(next_cycle['exp_amt'], 2)
                    expected_amount_compare = next_cycle['last_amt_in_cycle']
                    expected_type = next_cycle['type']

                if next_cycle['is_announced']:
                    expected_highly_likely = f"Announced: {next_cycle['next_date'].strftime('%d-%m-%Y')}"
                    expected_less_likely = "Confirmed"
                else:
                    expected_highly_likely = next_cycle['next_date'].strftime('%d-%m-%Y')
                    if next_cycle['less_likely_months']:
                        m_names = [datetime.date(2000, m, 1).strftime('%b') for m in next_cycle['less_likely_months']]
                        expected_less_likely = ", ".join(m_names)
                    else:
                        expected_less_likely = "-"

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
