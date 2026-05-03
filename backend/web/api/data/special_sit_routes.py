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
    # 1. Fetch all F&O stocks and their lot sizes from SecurityMaster
    fo_securities = db.query(SecurityMaster.symbol, SecurityMaster.market_lot).filter(
        SecurityMaster.derivative_liquidity_tier != None
    ).all()

    if not fo_securities:
        return []

    symbols = [s.symbol.upper() for s in fo_securities]
    lot_size_map = {s.symbol.upper(): s.market_lot for s in fo_securities}

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
    ten_years_ago = datetime.date.today() - datetime.timedelta(days=365*10)
    ca_records = db.query(CorporateAction).filter(
        CorporateAction.symbol.in_(symbols),
        CorporateAction.ex_date >= ten_years_ago,
        CorporateAction.parsed_dividend_amount != None
    ).order_by(desc(CorporateAction.ex_date)).all()

    # Group by symbol
    ca_by_symbol = defaultdict(list)
    for r in ca_records:
        ca_by_symbol[r.symbol.upper()].append({
            "ex_date": r.ex_date.strftime("%Y-%m-%d") if r.ex_date else None,
            "ex_date_obj": r.ex_date,
            "dividend_type": r.dividend_type,
            "purpose": r.purpose,
            "amount": r.parsed_dividend_amount
        })

    # 5. Process data and generate "guesstimates"
    results = []
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
            last = history[0]
            last_type = last['dividend_type'] or '-'
            last_ex_date = last['ex_date'] or '-'
            last_amount = last['amount']
            is_above_2_percent = last['is_above_2_percent']

            # Guesstimate Algorithm
            # Group by cycle (approximate by month of ex_date) over last 5 years
            five_years_ago = datetime.date.today() - datetime.timedelta(days=365*5)
            recent_hist = [h for h in history if h['ex_date_obj'] and h['ex_date_obj'] >= five_years_ago]

            if recent_hist and last['ex_date_obj']:
                last_month = last['ex_date_obj'].month

                # Find dividends in the same cycle (same month +/- 1)
                cycle_divs = []
                for h in recent_hist:
                    m = h['ex_date_obj'].month
                    if m == last_month or m == (last_month % 12) + 1 or m == (last_month - 2) % 12 + 1:
                        cycle_divs.append(h)

                # Sort ascending for growth calculation
                cycle_divs.sort(key=lambda x: x['ex_date_obj'])

                # Calculate YoY growth
                growth_rates = []
                for i in range(1, len(cycle_divs)):
                    prev_amt = cycle_divs[i-1]['amount']
                    curr_amt = cycle_divs[i]['amount']
                    if prev_amt and curr_amt and prev_amt > 0:
                        growth = (curr_amt - prev_amt) / prev_amt
                        growth_rates.append(growth)

                if growth_rates:
                    avg_growth = np.mean(growth_rates)
                    expected_amount = last_amount * (1 + avg_growth)
                else:
                    expected_amount = last_amount

                # Project Dates
                # Highly likely = exactly 364 days from last ex-date (to match day of week)
                highly_likely_date = last['ex_date_obj'] + datetime.timedelta(days=364)

                # If highly likely date has already passed, they might be looking at the next cycle
                if highly_likely_date < datetime.date.today():
                     highly_likely_date = highly_likely_date + datetime.timedelta(days=364)

                expected_highly_likely = highly_likely_date.strftime("%d-%m-%Y")
                expected_less_likely = highly_likely_date.strftime("%b-%Y")

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

    # Sort results to put ones with upcoming dividends at the top (or just alphabetical)
    # For now, sort alphabetically by symbol
    results.sort(key=lambda x: x['symbol'])

    return results
