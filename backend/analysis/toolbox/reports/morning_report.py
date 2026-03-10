import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import Dict, Any, List
from sqlalchemy import func, text
import json

from backend.ingest.nse_models import (
    BhavcopyFO, BhavcopyEQ, FOVolatility, MWPLClientPosition, DailyDerivativesAnalysis, PERatio, MTODelivery
)
from backend.risk.greeks import calculate_option_greeks, calculate_implied_volatility

class MorningReportCalculator:
    """Calculates Daily Derivative metrics using institutional models (Black-Scholes, etc)."""

    def __init__(self, db: Session):
        self.db = db
        # Set a static risk-free rate proxy for now (e.g. 30-day MIBOR ~ 6.5%)
        self.risk_free_rate = 0.065

    def _get_daily_vol(self, target_date: date, symbol: str) -> float:
        """Fetch 1-Sigma daily volatility from FOVolatility table."""
        record = self.db.query(FOVolatility).filter(
            FOVolatility.trade_date == target_date,
            FOVolatility.symbol == symbol
        ).first()
        return record.applicable_daily_vol if record else 0.0

    def _get_pe_ratio(self, target_date: date, symbol: str) -> float:
        """Fetch PE ratio from pe_ratio table."""
        record = self.db.query(PERatio).filter(
            PERatio.date == target_date,
            PERatio.symbol == symbol
        ).first()
        return record.symbol_pe if record else 0.0

    def _get_mwpl_array(self, target_date: date, symbol: str) -> list:
        """Fetch MWPL client limits for the symbol as a JSON array."""
        records = self.db.query(MWPLClientPosition).filter(
            MWPLClientPosition.date == target_date,
            MWPLClientPosition.underlying_stock == symbol
        ).order_by(MWPLClientPosition.position_pct.desc()).all()

        if not records:
            return []

        arr = []
        for i, r in enumerate(records):
            arr.append({f"client_{i+1}": r.position_pct})
        return arr

    def _fetch_cash_history(self, target_date: date, symbol: str, days: int = 500) -> pd.DataFrame:
        """Fetches historical cash close prices for Regression, ATR, and EMA calculations."""
        # Using a raw query for speed over a large window
        query = text("""
            SELECT trade_date, close_price, high_price, low_price
            FROM bhavcopy_eq
            WHERE symbol = :sym AND series = 'EQ' AND trade_date <= :dt
            ORDER BY trade_date DESC
            LIMIT :lmt
        """)
        result = self.db.execute(query, {"sym": symbol, "dt": target_date, "lmt": days}).fetchall()
        if not result:
            return pd.DataFrame()

        df = pd.DataFrame(result, columns=['date', 'close', 'high', 'low'])
        df = df.sort_values('date').reset_index(drop=True)
        return df

    def _fetch_nifty_history(self, target_date: date, days: int = 500) -> pd.DataFrame:
        """Fetches NIFTY spot history to act as the regression benchmark."""
        # We try to get NIFTY 50 index from bhavcopy_eq (if available) or bhavcopy_fo
        query = text("""
            SELECT trade_date, close_price
            FROM bhavcopy_fo
            WHERE ticker_symb = 'NIFTY' AND instrument_type = 'FUTIDX' AND trade_date <= :dt
            -- Approximating spot via near fut for index if spot not in EQ
            ORDER BY trade_date DESC, expiry_date ASC
            LIMIT :lmt
        """)
        # Note: Above query might yield duplicates per date if multiple expiries exist.
        # We will group by date and take the first (near).
        result = self.db.execute(query, {"dt": target_date, "lmt": days * 3}).fetchall() # Fetch extra due to expiries
        if not result:
            return pd.DataFrame()

        df = pd.DataFrame(result, columns=['date', 'close'])
        df = df.sort_values(['date']).groupby('date').first().reset_index()
        return df.tail(days).reset_index(drop=True)

    def _calculate_betas_and_rsquared(self, df_stock: pd.DataFrame, df_nifty: pd.DataFrame) -> dict:
        """Calculates Beta and R-Squared for 252 and 500 days using Log Returns."""
        if df_stock.empty or df_nifty.empty or len(df_stock) < 20 or len(df_nifty) < 20:
            return {"beta_252": 0.0, "beta_500": 0.0, "r_squared_252": 0.0, "r_squared_500": 0.0}

        # Merge on date to align series
        df = pd.merge(df_stock[['date', 'close']], df_nifty[['date', 'close']], on='date', suffixes=('_stock', '_nifty'))
        if len(df) < 20:
            return {"beta_252": 0.0, "beta_500": 0.0, "r_squared_252": 0.0, "r_squared_500": 0.0}

        # Calculate log returns: ln(P_t / P_{t-1})
        df['ret_stock'] = np.log(df['close_stock'] / df['close_stock'].shift(1))
        df['ret_nifty'] = np.log(df['close_nifty'] / df['close_nifty'].shift(1))
        df = df.dropna()

        def run_regression(window_df):
            if len(window_df) < 2: return 0.0, 0.0
            cov_matrix = np.cov(window_df['ret_stock'], window_df['ret_nifty'])
            var_nifty = np.var(window_df['ret_nifty'], ddof=1)
            if var_nifty == 0: return 0.0, 0.0
            beta = cov_matrix[0, 1] / var_nifty
            corr_matrix = np.corrcoef(window_df['ret_stock'], window_df['ret_nifty'])
            r_squared = corr_matrix[0, 1] ** 2
            return beta, r_squared

        b252, r252 = run_regression(df.tail(252))
        b500, r500 = run_regression(df.tail(500))

        return {
            "beta_252": b252,
            "beta_500": b500,
            "r_squared_252": r252,
            "r_squared_500": r500
        }

    def _calculate_technicals(self, df: pd.DataFrame) -> dict:
        """Calculates 14-day ATR and 20/50/100/200-day EMAs."""
        res = {"atr_14": 0.0, "ema_20": 0.0, "ema_50": 0.0, "ema_100": 0.0, "ema_200": 0.0}
        if df.empty:
            return res

        close = df['close']

        if len(df) >= 20: res['ema_20'] = close.ewm(span=20, adjust=False).mean().iloc[-1]
        if len(df) >= 50: res['ema_50'] = close.ewm(span=50, adjust=False).mean().iloc[-1]
        if len(df) >= 100: res['ema_100'] = close.ewm(span=100, adjust=False).mean().iloc[-1]
        if len(df) >= 200: res['ema_200'] = close.ewm(span=200, adjust=False).mean().iloc[-1]

        # ATR
        if len(df) > 1:
            high = df['high']
            low = df['low']
            prev_close = close.shift(1)
            tr1 = high - low
            tr2 = (high - prev_close).abs()
            tr3 = (low - prev_close).abs()
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            res['atr_14'] = tr.rolling(window=14).mean().iloc[-1]

        return res

    def _get_delivery_averages(self, target_date: date, symbol: str) -> dict:
        query = text("""
            SELECT trade_date, quantity_traded, deliverable_qty
            FROM mto_delivery
            WHERE security_name = :sym AND trade_date <= :dt
            ORDER BY trade_date DESC
            LIMIT 30
        """)
        # Fallback to symbol matching if security_name isn't perfectly mapped (MTO sometimes uses full names or symbols)
        # Assuming security_name matches symbol for now.
        result = self.db.execute(query, {"sym": symbol, "dt": target_date}).fetchall()

        res = {"5d": 0.0, "10d": 0.0, "20d": 0.0, "30d": 0.0}
        if not result:
            return res

        df = pd.DataFrame(result, columns=['date', 'traded', 'delivered'])
        df['pct'] = np.where(df['traded'] > 0, (df['delivered'] / df['traded']) * 100, 0)

        res['5d'] = df['pct'].head(5).mean() if len(df) >= 1 else 0.0
        res['10d'] = df['pct'].head(10).mean() if len(df) >= 10 else res['5d']
        res['20d'] = df['pct'].head(20).mean() if len(df) >= 20 else res['10d']
        res['30d'] = df['pct'].head(30).mean() if len(df) >= 30 else res['20d']

        return res

    def calculate_iv_and_skew(self, options_data, underlying_close, expiry_date, target_date, proxy_vol) -> tuple:
        """Calculates ATM IV and 25-Delta Skew for a given expiry."""
        if not options_data or underlying_close <= 0:
            return 0.0, 0.0

        T_days = (expiry_date - target_date).days
        T_years = max(0.001, T_days / 365.0)

        closest_atm_opt = min(options_data, key=lambda o: abs(o.strike_price - underlying_close))
        atm_opt = [o for o in options_data if o.strike_price == closest_atm_opt.strike_price and o.option_type == 'CE']

        atm_iv = 0.0
        if atm_opt:
            atm_iv = calculate_implied_volatility(
                target_price=atm_opt[0].close_price,
                S=underlying_close,
                K=closest_atm_opt.strike_price,
                T=T_years,
                r=self.risk_free_rate,
                option_type="call"
            )

        # Skew
        vol = atm_iv if atm_iv > 0 else (proxy_vol if proxy_vol > 0 else 0.20)

        closest_call_25d = None
        closest_put_25d = None
        call_min_diff = 1.0
        put_min_diff = 1.0

        for opt in options_data:
            opt_type = "call" if opt.option_type == 'CE' else "put"
            greeks = calculate_option_greeks(
                S=underlying_close,
                K=opt.strike_price,
                T=T_years,
                r=self.risk_free_rate,
                sigma=vol,
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

        call_25d_iv = 0.0
        put_25d_iv = 0.0

        if closest_call_25d:
            call_25d_iv = calculate_implied_volatility(
                target_price=closest_call_25d.close_price, S=underlying_close, K=closest_call_25d.strike_price,
                T=T_years, r=self.risk_free_rate, option_type="call"
            )
        if closest_put_25d:
            put_25d_iv = calculate_implied_volatility(
                target_price=closest_put_25d.close_price, S=underlying_close, K=closest_put_25d.strike_price,
                T=T_years, r=self.risk_free_rate, option_type="put"
            )

        skew = put_25d_iv - call_25d_iv
        return atm_iv, skew

    def calculate_for_date(self, target_date: date) -> Dict[str, Any]:
        symbols_query = self.db.query(BhavcopyFO.ticker_symb).filter(
            BhavcopyFO.trade_date == target_date,
            BhavcopyFO.instrument_type.in_(['FUTSTK', 'FUTIDX', 'STF', 'IDF'])
        ).with_entities(BhavcopyFO.ticker_symb).distinct().all()

        symbols = [s[0] for s in symbols_query]
        print(f"[{target_date}] Found {len(symbols)} active F&O symbols.")

        nifty_hist = self._fetch_nifty_history(target_date)
        processed_count = 0

        # Helper to safely cast numpy floats to native python floats
        def c_f(val):
            if val is None: return 0.0
            v = float(val)
            return 0.0 if np.isnan(v) or np.isinf(v) else v

        def c_i(val):
            if val is None: return 0
            v = float(val)
            return 0 if np.isnan(v) or np.isinf(v) else int(v)

        for symbol in symbols:
            # Get All Futures for the symbol
            futs = self.db.query(BhavcopyFO).filter(
                BhavcopyFO.trade_date == target_date,
                BhavcopyFO.ticker_symb == symbol,
                BhavcopyFO.instrument_type.in_(['FUTSTK', 'FUTIDX', 'STF', 'IDF']),
                BhavcopyFO.expiry_date >= target_date
            ).order_by(BhavcopyFO.expiry_date.asc()).all()

            if not futs:
                continue

            near_fut = futs[0]
            next_fut = futs[1] if len(futs) > 1 else None
            far_fut = futs[2] if len(futs) > 2 else None

            # Underlying Cash Close
            eq_record = self.db.query(BhavcopyEQ).filter(
                BhavcopyEQ.trade_date == target_date,
                BhavcopyEQ.symbol == symbol,
                BhavcopyEQ.series == 'EQ'
            ).first()
            cash_close = eq_record.close_price if eq_record else near_fut.close_price
            if cash_close <= 0: continue

            # Spreads & Basis (bps)
            basis_1 = (near_fut.close_price - cash_close) / cash_close * 10000
            basis_2 = (next_fut.close_price - cash_close) / cash_close * 10000 if next_fut else 0.0
            cal_spread_1 = (next_fut.close_price - near_fut.close_price) / near_fut.close_price * 10000 if next_fut else 0.0
            cal_spread_2 = (far_fut.close_price - next_fut.close_price) / next_fut.close_price * 10000 if far_fut and next_fut else 0.0

            # Volume & OI
            total_vol = sum(f.total_trading_vol for f in futs)
            total_oi = sum(f.open_interest for f in futs)
            rollover_pct = (sum(f.open_interest for f in futs[1:]) / total_oi * 100) if total_oi > 0 else 0.0

            # Options (PCR)
            all_opts = self.db.query(BhavcopyFO).filter(
                BhavcopyFO.trade_date == target_date,
                BhavcopyFO.ticker_symb == symbol,
                BhavcopyFO.instrument_type.in_(['OPTSTK', 'OPTIDX', 'STO', 'IDO'])
            ).all()

            put_oi = sum(o.open_interest for o in all_opts if o.option_type == 'PE')
            call_oi = sum(o.open_interest for o in all_opts if o.option_type == 'CE')
            pcr_oi = (put_oi / call_oi) if call_oi > 0 else 0.0

            # Find Highest OI Strikes for PE and CE
            highest_pe_strike = 0.0
            highest_pe_oi = 0
            highest_ce_strike = 0.0
            highest_ce_oi = 0

            for o in all_opts:
                if o.option_type == 'PE' and o.open_interest > highest_pe_oi:
                    highest_pe_oi = o.open_interest
                    highest_pe_strike = o.strike_price
                if o.option_type == 'CE' and o.open_interest > highest_ce_oi:
                    highest_ce_oi = o.open_interest
                    highest_ce_strike = o.strike_price

            chg_oi_opts = sum(o.change_in_oi for o in all_opts if o.change_in_oi is not None)
            chg_oi_futs = sum(f.change_in_oi for f in futs if f.change_in_oi is not None)

            # Volatility & Skew
            daily_vol = self._get_daily_vol(target_date, symbol)
            # Proxy annual vol for the root of BS solver (rough approximation using daily_vol * sqrt(365))
            proxy_ann_vol = daily_vol * np.sqrt(365) if daily_vol else 0.20

            near_opts = [o for o in all_opts if o.expiry_date == near_fut.expiry_date]
            next_opts = [o for o in all_opts if next_fut and o.expiry_date == next_fut.expiry_date]
            far_opts = [o for o in all_opts if far_fut and o.expiry_date == far_fut.expiry_date]

            atm_iv_near, skew_near = self.calculate_iv_and_skew(near_opts, cash_close, near_fut.expiry_date, target_date, proxy_ann_vol)
            atm_iv_next, _ = self.calculate_iv_and_skew(next_opts, cash_close, next_fut.expiry_date, target_date, proxy_ann_vol) if next_fut else (0.0, 0.0)
            _, skew_far = self.calculate_iv_and_skew(far_opts, cash_close, far_fut.expiry_date, target_date, proxy_ann_vol) if far_fut else (0.0, 0.0)

            # Other Metrics
            mwpl_arr = self._get_mwpl_array(target_date, symbol)
            pe_val = self._get_pe_ratio(target_date, symbol)

            stock_hist = self._fetch_cash_history(target_date, symbol)
            betas = self._calculate_betas_and_rsquared(stock_hist, nifty_hist)
            techs = self._calculate_technicals(stock_hist)
            deliv = self._get_delivery_averages(target_date, symbol)

            # Save
            record = self.db.query(DailyDerivativesAnalysis).filter(
                DailyDerivativesAnalysis.trade_date == target_date,
                DailyDerivativesAnalysis.symbol == symbol
            ).first()

            if not record:
                record = DailyDerivativesAnalysis(trade_date=target_date, symbol=symbol)
                self.db.add(record)

            record.close_price = c_f(near_fut.close_price)
            record.futures_total_vol = c_i(total_vol)
            record.futures_total_oi = c_i(total_oi)
            record.pcr_oi = c_f(pcr_oi)
            record.highest_oi_strike_pe = c_f(highest_pe_strike)
            record.highest_oi_strike_ce = c_f(highest_ce_strike)
            record.chg_oi_options = c_i(chg_oi_opts)
            record.chg_oi_futures = c_i(chg_oi_futs)
            record.total_options_call_oi = c_i(call_oi)
            record.total_options_put_oi = c_i(put_oi)
            record.atm_iv_near = c_f(atm_iv_near)
            record.atm_iv_next = c_f(atm_iv_next)
            record.skew_25d_near = c_f(skew_near)
            record.skew_25d_far = c_f(skew_far)
            record.rollover_pct = c_f(rollover_pct)
            record.daily_volatility = c_f(daily_vol)
            record.mwpl_array = mwpl_arr
            record.basis_1_bps = c_f(basis_1)
            record.basis_2_bps = c_f(basis_2)
            record.calendar_spread_1_bps = c_f(cal_spread_1)
            record.calendar_spread_2_bps = c_f(cal_spread_2)
            record.pe_ratio = c_f(pe_val)
            record.beta_252 = c_f(betas['beta_252'])
            record.beta_500 = c_f(betas['beta_500'])
            record.r_squared_252 = c_f(betas['r_squared_252'])
            record.r_squared_500 = c_f(betas['r_squared_500'])
            record.atr_14_cash = c_f(techs['atr_14'])
            record.ema_20_cash = c_f(techs['ema_20'])
            record.ema_50_cash = c_f(techs['ema_50'])
            record.ema_100_cash = c_f(techs['ema_100'])
            record.ema_200_cash = c_f(techs['ema_200'])
            record.mavg_delivery_vol_pct_5d = c_f(deliv['5d'])
            record.mavg_delivery_vol_pct_10d = c_f(deliv['10d'])
            record.mavg_delivery_vol_pct_20d = c_f(deliv['20d'])
            record.mavg_delivery_vol_pct_30d = c_f(deliv['30d'])

            processed_count += 1

        self.db.commit()
        return {"status": "success", "processed_symbols": processed_count, "date": str(target_date)}
