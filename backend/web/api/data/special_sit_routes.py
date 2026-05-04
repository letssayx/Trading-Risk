from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_
from typing import List, Dict, Optional
import datetime
from collections import defaultdict
import numpy as np

from backend.infrastructure.db import get_db
from backend.ingest.nse_models import SecurityMaster, BhavcopyFO, BhavcopyEQ, CorporateAction

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
            futures_map[r.ticker_symb.upper()].append(r.close_price)

    # 4. Fetch Corporate Actions (Dividends) for the last 10 years
    today = datetime.date.today()
    ten_years_ago = today - datetime.timedelta(days=365*10)
    ca_records = db.query(CorporateAction).filter(
        CorporateAction.symbol.in_(symbols),
        CorporateAction.date >= ten_years_ago,
        CorporateAction.parsed_dividend_amount != None
    ).order_by(desc(CorporateAction.date)).all()

    # Group by symbol
    ca_by_symbol = defaultdict(list)
    for r in ca_records:
        ca_by_symbol[r.symbol.upper()].append({
            "ex_date": r.date.strftime("%Y-%m-%d") if r.date else None,
            "ex_date_obj": r.date,
            "dividend_type": r.dividend_type,
            "purpose": r.purpose,
            "amount": r.parsed_dividend_amount
        })

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
            if spot and spot > 0 and h['amount']:
                if (h['amount'] / spot) * 100 > 2.0:
                    h['is_above_2_percent'] = True

        last_type = "-"
        last_ex_date = "-"
        last_amount = None
        is_above_2_percent = False

        expected_amount = None
        expected_highly_likely = None
        expected_less_likely = None

        if history:
            # Most recent overall dividend (just for table display purposes)
            last = history[0]
            last_type = last['dividend_type'] or '-'
            last_ex_date = last['ex_date'] or '-'
            last_amount = last['amount']
            is_above_2_percent = last['is_above_2_percent']

            # Sort ascending for cycle processing
            history_asc = sorted(history, key=lambda x: x['ex_date_obj'] if x['ex_date_obj'] else datetime.date.min)

            # Cluster historical dividends into "Cycles"
            clusters = []
            five_years_ago = today - datetime.timedelta(days=365*5)
            recent_hist = [h for h in history_asc if h['ex_date_obj'] and h['ex_date_obj'] >= five_years_ago]

            for h in recent_hist:
                doy = get_doy(h['ex_date_obj'])
                placed = False
                for c in clusters:
                    mean_doy = sum(get_doy(x['ex_date_obj']) for x in c) / len(c)
                    if circ_diff(doy, mean_doy) <= 55: # 55 days threshold to group shifting months
                        c.append(h)
                        placed = True
                        break
                if not placed:
                    clusters.append([h])

            # For each cycle, find its next upcoming date
            upcoming_cycles = []
            for c in clusters:
                most_recent = c[-1]
                mr_date = most_recent['ex_date_obj']

                if mr_date >= today:
                    # Already announced for future
                    next_date = mr_date
                    is_announced = True
                else:
                    # Project forward
                    next_date = mr_date + datetime.timedelta(days=364)
                    while next_date < today - datetime.timedelta(days=15): # grace period
                        next_date += datetime.timedelta(days=364)
                    is_announced = False

                # Calculate cycle growth
                growth_rates = []
                for i in range(1, len(c)):
                    prev_amt = c[i-1]['amount']
                    curr_amt = c[i]['amount']
                    days_diff = (c[i]['ex_date_obj'] - c[i-1]['ex_date_obj']).days
                    if 300 <= days_diff <= 430 and prev_amt and curr_amt and prev_amt > 0:
                        growth_rates.append((curr_amt - prev_amt) / prev_amt)

                avg_growth = np.mean(growth_rates) if growth_rates else 0
                exp_amt = most_recent['amount'] * (1 + avg_growth) if most_recent['amount'] else None

                # Less likely months
                highly_likely_month = next_date.month
                all_months = set(x['ex_date_obj'].month for x in c)
                less_likely_m = all_months - {highly_likely_month}

                upcoming_cycles.append({
                    'next_date': next_date,
                    'is_announced': is_announced,
                    'exp_amt': exp_amt,
                    'highly_likely_month': highly_likely_month,
                    'less_likely_months': less_likely_m
                })

            # Pick the chronologically next cycle
            if upcoming_cycles:
                upcoming_cycles.sort(key=lambda x: x['next_date'])
                next_cycle = upcoming_cycles[0]

                if next_cycle['exp_amt'] is not None:
                    expected_amount = round(next_cycle['exp_amt'], 2)

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
            "futures": futures[:3], # take up to Future 3
            "last_type": last_type,
            "last_ex_date": last_ex_date,
            "last_amount": last_amount,
            "is_above_2_percent": is_above_2_percent,
            "expected_amount": expected_amount,
            "expected_highly_likely": expected_highly_likely,
            "expected_less_likely": expected_less_likely,
            "history": history
        })

    # Sort alphabetical by symbol
    results.sort(key=lambda x: x['symbol'])

    return results
