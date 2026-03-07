from sqlalchemy.orm import Session
from datetime import date
from typing import Dict, Any, List
from sqlalchemy import func
from datetime import timedelta
import pandas as pd
import numpy as np

from backend.ingest.nse_models import (
    BhavcopyFO, BhavcopyEQ, FOVolatility, MWPLClientPosition, DailyDerivativesAnalysis
)
from backend.risk.greeks import calculate_option_greeks, bs_price, calculate_implied_volatility

class MorningReportCalculator:
    """Calculates Daily Derivative metrics using institutional models (Black-Scholes, etc)."""

    def __init__(self, db: Session):
        self.db = db
        # Set a static risk-free rate proxy for now (e.g. 30-day MIBOR ~ 6.5%)
        self.risk_free_rate = 0.065

    def _get_annualized_vol(self, target_date: date, symbol: str) -> float:
        """Fetch 30-day annualized volatility from FOVolatility table."""
        record = self.db.query(FOVolatility).filter(
            FOVolatility.trade_date == target_date,
            FOVolatility.symbol == symbol
        ).first()
        return record.applicable_annualised_vol if record else 0.0

    def _get_mwpl_data(self, target_date: date, symbol: str) -> tuple[float, float]:
        """Fetch and aggregate MWPL client limits for the symbol."""
        records = self.db.query(MWPLClientPosition).filter(
            MWPLClientPosition.date == target_date,
            MWPLClientPosition.underlying_stock == symbol
        ).order_by(MWPLClientPosition.position_pct.desc()).all()

        if not records:
            return 0.0, 0.0

        total_utilization = sum(r.position_pct for r in records)
        top_3_concentration = sum(r.position_pct for r in records[:3])
        return total_utilization, top_3_concentration

    def calculate_for_date(self, target_date: date) -> Dict[str, Any]:
        """Calculates and stores metrics for all symbols on the target date."""

        # 1. Find all active symbols in F&O for the date
        symbols_query = self.db.query(BhavcopyFO.ticker_symb).filter(
            BhavcopyFO.trade_date == target_date,
            BhavcopyFO.instrument_type.in_(['FUTSTK', 'FUTIDX'])
        ).distinct().all()

        symbols = [s[0] for s in symbols_query]
        print(f"[{target_date}] Found {len(symbols)} active F&O symbols.")

        processed_count = 0

        for symbol in symbols:
            # 2. Get Near Expiry Future Price
            near_fut = self.db.query(BhavcopyFO).filter(
                BhavcopyFO.trade_date == target_date,
                BhavcopyFO.ticker_symb == symbol,
                BhavcopyFO.instrument_type.in_(['FUTSTK', 'FUTIDX']),
                BhavcopyFO.expiry_date >= target_date
            ).order_by(BhavcopyFO.expiry_date.asc()).first()

            if not near_fut:
                continue

            underlying_close = near_fut.open_price # fallback if close is 0 somehow

            # Fetch EQ close price if available for underlying, else use Future
            eq_record = self.db.query(BhavcopyEQ).filter(
                BhavcopyEQ.trade_date == target_date,
                BhavcopyEQ.ticker_symb == symbol,
                BhavcopyEQ.series == 'EQ'
            ).first()

            underlying_close = eq_record.close_price if eq_record else near_fut.close_price

            # Basis calculation
            futures_close = near_fut.close_price
            basis = futures_close - underlying_close
            basis_pct = (basis / underlying_close * 100) if underlying_close > 0 else 0.0

            # Open Interest & Volume for all expiries
            futs_aggr = self.db.query(
                func.sum(BhavcopyFO.open_interest),
                func.sum(BhavcopyFO.total_trading_vol)
            ).filter(
                BhavcopyFO.trade_date == target_date,
                BhavcopyFO.ticker_symb == symbol,
                BhavcopyFO.instrument_type.in_(['FUTSTK', 'FUTIDX'])
            ).first()

            futures_oi = futs_aggr[0] or 0
            futures_volume = futs_aggr[1] or 0

            # Rollover (Next + Far OI / Total OI)
            next_far_oi_sum = self.db.query(func.sum(BhavcopyFO.open_interest)).filter(
                BhavcopyFO.trade_date == target_date,
                BhavcopyFO.ticker_symb == symbol,
                BhavcopyFO.instrument_type.in_(['FUTSTK', 'FUTIDX']),
                BhavcopyFO.expiry_date > near_fut.expiry_date
            ).scalar() or 0

            rollover_pct = (next_far_oi_sum / futures_oi * 100) if futures_oi > 0 else 0.0

            # Volatility & MWPL
            ann_vol = self._get_annualized_vol(target_date, symbol)
            mwpl_total, mwpl_top_3 = self._get_mwpl_data(target_date, symbol)

            # OPTIONS DATA: PCR, ATM Vol, 25-Delta Skew
            options_data = self.db.query(BhavcopyFO).filter(
                BhavcopyFO.trade_date == target_date,
                BhavcopyFO.ticker_symb == symbol,
                BhavcopyFO.instrument_type.in_(['OPTSTK', 'OPTIDX']),
                BhavcopyFO.expiry_date == near_fut.expiry_date
            ).all()

            total_call_oi = sum(o.open_interest for o in options_data if o.option_type == 'CE')
            total_put_oi = sum(o.open_interest for o in options_data if o.option_type == 'PE')
            total_call_vol = sum(o.total_trading_vol for o in options_data if o.option_type == 'CE')
            total_put_vol = sum(o.total_trading_vol for o in options_data if o.option_type == 'PE')

            pcr_oi = (total_put_oi / total_call_oi) if total_call_oi > 0 else 0.0
            pcr_volume = (total_put_vol / total_call_vol) if total_call_vol > 0 else 0.0

            atm_iv = 0.0
            put_25d_iv = 0.0
            call_25d_iv = 0.0
            skew_25d = 0.0

            if options_data and underlying_close > 0:
                T_days = (near_fut.expiry_date - target_date).days
                T_years = T_days / 365.0

                # ATM Vol calculation
                closest_atm_opt = min(options_data, key=lambda o: abs(o.strike_price - underlying_close))
                atm_opt = [o for o in options_data if o.strike_price == closest_atm_opt.strike_price and o.option_type == 'CE']
                if atm_opt and T_years > 0:
                    atm_price = atm_opt[0].close_price
                    atm_iv = calculate_implied_volatility(
                        target_price=atm_price,
                        S=underlying_close,
                        K=closest_atm_opt.strike_price,
                        T=T_years,
                        r=self.risk_free_rate,
                        option_type="call"
                    )

                # 25-Delta Skew Calculation
                # We need to find the strikes whose Delta is closest to 0.25 (Call) and -0.25 (Put)
                # To do this, we approximate delta using the ATM Vol or Annualized Vol as a proxy
                proxy_vol = atm_iv if atm_iv > 0 else ann_vol
                if proxy_vol == 0:
                    proxy_vol = 0.20 # Fallback 20% vol

                closest_call_25d = None
                closest_put_25d = None
                call_min_diff = 1.0
                put_min_diff = 1.0

                for opt in options_data:
                    opt_type = "call" if opt.option_type == 'CE' else "put"
                    greeks = calculate_option_greeks(
                        S=underlying_close,
                        K=opt.strike_price,
                        T=max(0.001, T_years),
                        r=self.risk_free_rate,
                        sigma=proxy_vol,
                        option_type=opt_type
                    )

                    if opt.option_type == 'CE':
                        diff = abs(greeks['delta'] - 0.25)
                        if diff < call_min_diff:
                            call_min_diff = diff
                            closest_call_25d = opt
                    else: # PE
                        diff = abs(greeks['delta'] - (-0.25))
                        if diff < put_min_diff:
                            put_min_diff = diff
                            closest_put_25d = opt

                # Calculate True IV for these identified 25-delta strikes
                if closest_call_25d and T_years > 0:
                    call_25d_iv = calculate_implied_volatility(
                        target_price=closest_call_25d.close_price,
                        S=underlying_close,
                        K=closest_call_25d.strike_price,
                        T=T_years,
                        r=self.risk_free_rate,
                        option_type="call"
                    )

                if closest_put_25d and T_years > 0:
                    put_25d_iv = calculate_implied_volatility(
                        target_price=closest_put_25d.close_price,
                        S=underlying_close,
                        K=closest_put_25d.strike_price,
                        T=T_years,
                        r=self.risk_free_rate,
                        option_type="put"
                    )

                skew_25d = put_25d_iv - call_25d_iv

            # Upsert Record into Database
            record = self.db.query(DailyDerivativesAnalysis).filter(
                DailyDerivativesAnalysis.trade_date == target_date,
                DailyDerivativesAnalysis.symbol == symbol
            ).first()

            if not record:
                record = DailyDerivativesAnalysis(
                    trade_date=target_date,
                    symbol=symbol
                )
                self.db.add(record)

            record.underlying_close = underlying_close
            record.futures_close = futures_close
            record.basis = basis
            record.basis_pct = basis_pct
            record.annualized_vol = ann_vol
            record.futures_oi = futures_oi
            record.futures_volume = futures_volume
            record.rollover_pct = rollover_pct
            record.pcr_oi = pcr_oi
            record.pcr_volume = pcr_volume
            record.atm_iv = atm_iv
            record.put_25d_iv = put_25d_iv
            record.call_25d_iv = call_25d_iv
            record.skew_25d = skew_25d
            record.mwpl_utilization_pct = mwpl_total
            record.top_3_clients_mwpl_pct = mwpl_top_3

            processed_count += 1

        self.db.commit()
        return {"status": "success", "processed_symbols": processed_count, "date": str(target_date)}
