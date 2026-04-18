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
            PERatio.date <= target_date,
            PERatio.symbol == symbol
        ).order_by(PERatio.date.desc()).first()

        return record.symbol_pe if record and record.symbol_pe is not None else 0.0

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
            SELECT trade_date, close_price, high_price, low_price, total_traded_qty as volume
            FROM bhavcopy_eq
            WHERE symbol = :sym AND series = 'EQ' AND trade_date <= :dt
            ORDER BY trade_date DESC
            LIMIT :lmt
        """)
        result = self.db.execute(query, {"sym": symbol, "dt": target_date, "lmt": days}).fetchall()
        if result:
            df = pd.DataFrame(result, columns=['date', 'close', 'high', 'low', 'volume'])
            for col in ['close', 'high', 'low', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            df = df.sort_values('date').reset_index(drop=True)
            return df

        # Check for historical index data (for indices) first
        query_idx = text("""
            SELECT trade_date, close_price, high_price, low_price, total_traded_qty as volume
            FROM historical_index_data
            WHERE index_name = :sym AND trade_date <= :dt
            ORDER BY trade_date DESC
            LIMIT :lmt
        """)
        result = self.db.execute(query_idx, {"sym": symbol, "dt": target_date, "lmt": days}).fetchall()
        if result:
            df = pd.DataFrame(result, columns=['date', 'close', 'high', 'low', 'volume'])
            for col in ['close', 'high', 'low', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            df = df.sort_values('date').reset_index(drop=True)
            return df

        # Fallback to near futures for stocks without EQ data
        query_fo = text("""
            SELECT * FROM (
                SELECT DISTINCT ON (trade_date) trade_date, close_price, high_price, low_price, total_trading_vol as volume
                FROM bhavcopy_fo
                WHERE ticker_symb = :sym AND instrument_type IN ('FUTIDX', 'FUTSTK') AND trade_date <= :dt
                ORDER BY trade_date DESC, expiry_date ASC
            ) AS distinct_dates
            ORDER BY trade_date DESC
            LIMIT :lmt
        """)
        result = self.db.execute(query_fo, {"sym": symbol, "dt": target_date, "lmt": days}).fetchall()

        if not result:
            return pd.DataFrame()

        df = pd.DataFrame(result, columns=['date', 'close', 'high', 'low', 'volume'])

        # Replace string/object with float
        for col in ['close', 'high', 'low', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

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
        df['close'] = pd.to_numeric(df['close'], errors='coerce').fillna(0.0)
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

        # Ensure values are float and > 0 before taking log
        df['close_stock'] = pd.to_numeric(df['close_stock'], errors='coerce').fillna(0)
        df['close_nifty'] = pd.to_numeric(df['close_nifty'], errors='coerce').fillna(0)
        df = df[(df['close_stock'] > 0) & (df['close_nifty'] > 0)].copy()

        # Calculate log returns: ln(P_t / P_{t-1})
        df['ret_stock'] = np.log(df['close_stock'] / df['close_stock'].shift(1))
        df['ret_nifty'] = np.log(df['close_nifty'] / df['close_nifty'].shift(1))

        # Replace inf with nan, then drop nan
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df = df.dropna()

        def run_regression(window_df):
            if len(window_df) < 2: return 0.0, 0.0

            try:
                cov_matrix = np.cov(window_df['ret_stock'], window_df['ret_nifty'])
                var_nifty = np.var(window_df['ret_nifty'], ddof=1)
                if var_nifty == 0: return 0.0, 0.0

                beta = float(cov_matrix[0, 1] / var_nifty)
                corr_matrix = np.corrcoef(window_df['ret_stock'], window_df['ret_nifty'])
                r_squared = float(corr_matrix[0, 1] ** 2)

                if np.isnan(beta) or np.isinf(beta): beta = 0.0
                if np.isnan(r_squared) or np.isinf(r_squared): r_squared = 0.0
                return beta, r_squared
            except Exception:
                return 0.0, 0.0

        b252, r252 = run_regression(df.tail(252))
        b500, r500 = run_regression(df.tail(500))

        return {
            "beta_252": b252,
            "beta_500": b500,
            "r_squared_252": r252,
            "r_squared_500": r500
        }

    def _calculate_technicals(self, df: pd.DataFrame) -> dict:
        """Calculates 14-day ATR, EMAs, Price % Change, Z-Score, and Relative Volume."""
        res = {
            "atr_14": 0.0, "ema_20": 0.0, "ema_50": 0.0, "ema_100": 0.0, "ema_200": 0.0,
            "price_pct_change": 0.0, "rel_vol_20d": 0.0, "z_score": 0.0
        }
        if df.empty:
            return res

        close = df['close']

        if len(df) >= 2:
            prev_c = close.iloc[-2]
            if prev_c != 0:
                res['price_pct_change'] = ((close.iloc[-1] - prev_c) / prev_c) * 100

        if len(df) >= 20:
            res['ema_20'] = close.ewm(span=20, adjust=False).mean().iloc[-1]

            # 20-Day Z-Score
            roll_mean = close.rolling(window=20).mean().iloc[-1]
            roll_std = close.rolling(window=20).std().iloc[-1]
            if roll_std > 0:
                res['z_score'] = (close.iloc[-1] - roll_mean) / roll_std

            if 'volume' in df.columns:
                vol_sma_20 = df['volume'].rolling(window=20).mean().iloc[-1]
                if vol_sma_20 > 0:
                    res['rel_vol_20d'] = df['volume'].iloc[-1] / vol_sma_20

        if len(df) >= 50: res['ema_50'] = close.ewm(span=50, adjust=False).mean().iloc[-1]
        if len(df) >= 100: res['ema_100'] = close.ewm(span=100, adjust=False).mean().iloc[-1]
        if len(df) >= 200: res['ema_200'] = close.ewm(span=200, adjust=False).mean().iloc[-1]

        # ATR
        if len(df) > 1 and 'high' in df.columns and 'low' in df.columns:
            high = pd.to_numeric(df['high'], errors='coerce').fillna(0)
            low = pd.to_numeric(df['low'], errors='coerce').fillna(0)
            c = pd.to_numeric(close, errors='coerce').fillna(0)

            prev_close = c.shift(1)
            tr1 = high - low
            tr2 = (high - prev_close).abs()
            tr3 = (low - prev_close).abs()
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

            if len(tr) >= 14:
                atr_14_abs = tr.rolling(window=14).mean().iloc[-1]
                if c.iloc[-1] > 0 and not np.isnan(atr_14_abs):
                    res['atr_14'] = (atr_14_abs / c.iloc[-1]) * 100

        # Cast all results to float safely
        for k in res:
            try:
                res[k] = float(res[k]) if not np.isnan(res[k]) else 0.0
            except:
                res[k] = 0.0

        return res

    def _get_delivery_averages(self, target_date: date, symbol: str) -> dict:
        # Increase limit to 500 to fetch long term delivery averages
        query = text("""
            SELECT trade_date, quantity_traded, deliverable_qty
            FROM mto_delivery
            WHERE security_name = :sym AND trade_date <= :dt
            ORDER BY trade_date DESC
            LIMIT 500
        """)
        # Fallback to symbol matching if security_name isn't perfectly mapped (MTO sometimes uses full names or symbols)
        # Assuming security_name matches symbol for now.
        result = self.db.execute(query, {"sym": symbol, "dt": target_date}).fetchall()

        res = {"5d": 0.0, "10d": 0.0, "20d": 0.0, "30d": 0.0, "avg": 0.0, "high": 0.0}
        if not result:
            return res

        df = pd.DataFrame(result, columns=['date', 'traded', 'delivered'])

        # Ensure numeric to avoid string divisions
        df['traded'] = pd.to_numeric(df['traded'], errors='coerce').fillna(0)
        df['delivered'] = pd.to_numeric(df['delivered'], errors='coerce').fillna(0)

        # Avoid 100% bugs if delivered accidentally exceeds or equals traded indiscriminately
        df['pct'] = np.where((df['traded'] > 0) & (df['delivered'] >= 0), (df['delivered'] / df['traded']) * 100, 0)

        # Cap at 100 in case of dirty data
        df['pct'] = np.where(df['pct'] > 100, 100, df['pct'])

        res['5d'] = float(df['pct'].head(5).mean()) if len(df) >= 1 else 0.0
        res['10d'] = float(df['pct'].head(10).mean()) if len(df) >= 10 else res['5d']
        res['20d'] = float(df['pct'].head(20).mean()) if len(df) >= 20 else res['10d']
        res['30d'] = float(df['pct'].head(30).mean()) if len(df) >= 30 else res['20d']
        res['avg'] = float(df['pct'].mean()) if not df.empty else 0.0
        res['high'] = float(df['pct'].max()) if not df.empty else 0.0

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

    def _calculate_iv_rank_percentile(self, symbol: str, target_date: date, current_iv: float) -> tuple:
        """Calculates 252-day IV Rank and IV Percentile using historical DailyDerivativesAnalysis data."""
        if current_iv == 0.0:
            return 0.0, 0.0

        hist_records = self.db.query(DailyDerivativesAnalysis.atm_iv_near).filter(
            DailyDerivativesAnalysis.symbol == symbol,
            DailyDerivativesAnalysis.trade_date <= target_date,
            DailyDerivativesAnalysis.atm_iv_near > 0.0
        ).order_by(DailyDerivativesAnalysis.trade_date.desc()).limit(252).all()

        ivs = [r[0] for r in hist_records]
        if current_iv not in ivs: # ensure current is in there if it's new
            ivs.append(current_iv)

        if len(ivs) < 10: # Need at least some history for a meaningful rank
            return 0.0, 0.0

        min_iv = min(ivs)
        max_iv = max(ivs)

        iv_rank = ((current_iv - min_iv) / (max_iv - min_iv) * 100.0) if max_iv > min_iv else 0.0

        lower_iv_count = sum(1 for iv in ivs if iv < current_iv)
        iv_pctile = (lower_iv_count / len(ivs)) * 100.0

        return iv_rank, iv_pctile


    def _safe_float(self, val: Any) -> Any:
        import numpy as np
        import math
        if val is None:
            return None
        if isinstance(val, (int, float)):
            if math.isnan(val) or math.isinf(val):
                return 0.0
            return float(val)
        if isinstance(val, (np.floating, np.integer)):
            v = float(val)
            if math.isnan(v) or math.isinf(v):
                return 0.0
            return v
        return val

    def _safe_float(self, val):
        import numpy as np
        import math
        if val is None: return None
        try:
            v = float(val)
            if math.isnan(v) or math.isinf(v):
                return None
            return v
        except (ValueError, TypeError):
            return val

    def _safe_float(self, val):
        import numpy as np
        import math
        if val is None: return None
        try:
            v = float(val)
            if math.isnan(v) or math.isinf(v):
                return None
            return v
        except (ValueError, TypeError):
            return val

    def _safe_float(self, val):
        import numpy as np
        import math
        if val is None: return None
        try:
            v = float(val)
            if math.isnan(v) or math.isinf(v):
                return None
            return v
        except (ValueError, TypeError):
            return val

    def _safe_float(self, val):
        import numpy as np
        import math
        if val is None: return None
        try:
            v = float(val)
            if math.isnan(v) or math.isinf(v):
                return None
            return v
        except (ValueError, TypeError):
            return val

    def _safe_float(self, val):
        import numpy as np
        import math
        if val is None: return None
        try:
            v = float(val)
            if math.isnan(v) or math.isinf(v):
                return None
            return v
        except (ValueError, TypeError):
            return val

    def calculate_for_date(self, target_date: date) -> Dict[str, Any]:
        symbols_query = self.db.query(BhavcopyFO.ticker_symb).filter(
            BhavcopyFO.trade_date == target_date,
            BhavcopyFO.instrument_type.in_(['FUTSTK', 'FUTIDX', 'STF', 'IDF'])
        ).with_entities(BhavcopyFO.ticker_symb).distinct().all()

        symbols = [s[0] for s in symbols_query]
        print(f"[{target_date}] Found {len(symbols)} active F&O symbols.")

        nifty_hist = self._fetch_nifty_history(target_date)
        processed_count = 0

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

            # Identify unique expiry dates to avoid duplicate weekly contracts throwing off the month logic
            unique_expiries = []
            for f in futs:
                if f.expiry_date not in unique_expiries:
                    unique_expiries.append(f.expiry_date)

            near_fut = next((f for f in futs if f.expiry_date == unique_expiries[0]), None) if len(unique_expiries) > 0 else None
            next_fut = next((f for f in futs if f.expiry_date == unique_expiries[1]), None) if len(unique_expiries) > 1 else None
            far_fut = next((f for f in futs if f.expiry_date == unique_expiries[2]), None) if len(unique_expiries) > 2 else None

            if not near_fut:
                continue

            # Underlying Cash Close
            eq_record = self.db.query(BhavcopyEQ).filter(
                BhavcopyEQ.trade_date == target_date,
                BhavcopyEQ.symbol == symbol,
                BhavcopyEQ.series == 'EQ'
            ).first()

            cash_close = 0.0
            if eq_record and eq_record.close_price > 0:
                cash_close = eq_record.close_price
            else:
                # Check for historical index data (for indices)
                from backend.ingest.nse_models import HistoricalIndexData
                idx_record = self.db.query(HistoricalIndexData).filter(
                    HistoricalIndexData.trade_date == target_date,
                    HistoricalIndexData.index_name == symbol
                ).first()
                if idx_record and idx_record.close_price:
                    cash_close = idx_record.close_price
                else:
                    cash_close = near_fut.close_price

            if cash_close <= 0: continue

            # Spreads & Basis (bps)
            basis_1 = (near_fut.close_price - cash_close) / cash_close * 10000
            basis_2 = (next_fut.close_price - cash_close) / cash_close * 10000 if next_fut else 0.0
            cal_spread_1 = (next_fut.close_price - near_fut.close_price) / near_fut.close_price * 10000 if next_fut else 0.0
            cal_spread_2 = (far_fut.close_price - next_fut.close_price) / next_fut.close_price * 10000 if far_fut and next_fut else 0.0

            # Volume & OI
            total_vol = sum(f.total_trading_vol for f in futs)
            total_oi = sum(f.open_interest for f in futs)
            rollover_pct = (sum(f.open_interest for f in futs[1:]) / total_oi) if total_oi > 0 else 0.0

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
            # Exclude today's expiry if today is the expiry day
            valid_opts = [o for o in all_opts if o.expiry_date != target_date]
            if not valid_opts:
                valid_opts = all_opts

            near_opts = [o for o in all_opts if near_fut and o.expiry_date == near_fut.expiry_date]
            next_opts = [o for o in all_opts if next_fut and o.expiry_date == next_fut.expiry_date]
            far_opts = [o for o in all_opts if far_fut and o.expiry_date == far_fut.expiry_date]

            # Highest OI: Sum open_interest by strike across all valid options (excluding today's expiry).
            # The true picture of support/resistance is the summation of OI across all active series for a strike.

            pe_strike_oi_map = {}
            ce_strike_oi_map = {}

            for o in valid_opts:
                if o.open_interest is not None:
                    if o.option_type == 'PE':
                        pe_strike_oi_map[o.strike_price] = pe_strike_oi_map.get(o.strike_price, 0) + o.open_interest
                    elif o.option_type == 'CE':
                        ce_strike_oi_map[o.strike_price] = ce_strike_oi_map.get(o.strike_price, 0) + o.open_interest

            highest_pe_strike = max(pe_strike_oi_map, key=pe_strike_oi_map.get) if pe_strike_oi_map else 0.0
            highest_ce_strike = max(ce_strike_oi_map, key=ce_strike_oi_map.get) if ce_strike_oi_map else 0.0

            highest_pe_oi = pe_strike_oi_map.get(highest_pe_strike, 0)
            highest_ce_oi = ce_strike_oi_map.get(highest_ce_strike, 0)

            # For premium (Highest OI Value), we look at the near month premium for that strike.
            highest_pe_value = next((o.close_price for o in near_opts if o.strike_price == highest_pe_strike and o.option_type == 'PE'), 0.0)
            highest_ce_value = next((o.close_price for o in near_opts if o.strike_price == highest_ce_strike and o.option_type == 'CE'), 0.0)

            chg_oi_opts = sum(o.change_in_oi for o in all_opts if o.change_in_oi is not None)
            chg_oi_futs = sum(f.change_in_oi for f in futs if f.change_in_oi is not None)

            # Volatility & Skew
            daily_vol = self._get_daily_vol(target_date, symbol)
            # Proxy annual vol for the root of BS solver (rough approximation using daily_vol * sqrt(365))
            proxy_ann_vol = daily_vol * np.sqrt(365) if daily_vol else 0.20

            # Values at highest OI strikes (using near month premium)
            # ATM Straddle calculation (Near Month)
            # Find the closest strike to the cash close (or near fut close if cash not available)
            # If today is expiry, use next month for 'Near Month' calculation
            atm_straddle_near_month = 0.0
            straddle_near_opts = near_opts
            if near_fut and near_fut.expiry_date == target_date and next_opts:
                straddle_near_opts = next_opts

            ref_price = cash_close if cash_close > 0 else (near_fut.close_price if near_fut else 0.0)

            if straddle_near_opts and ref_price > 0:
                unique_strikes = list(set([o.strike_price for o in straddle_near_opts]))
                if unique_strikes:
                    # Closest strike to spot with 0.5 delta logic
                    atm_strike = min(unique_strikes, key=lambda x: abs(x - ref_price))
                    atm_ce_price = next((o.close_price for o in straddle_near_opts if o.strike_price == atm_strike and o.option_type in ['CE', 'OPTIDX_CE', 'OPTSTK_CE']), 0.0)
                    atm_pe_price = next((o.close_price for o in straddle_near_opts if o.strike_price == atm_strike and o.option_type in ['PE', 'OPTIDX_PE', 'OPTSTK_PE']), 0.0)
                    if not atm_ce_price and not atm_pe_price: # try strip/upper matching
                        atm_ce_price = next((o.close_price for o in straddle_near_opts if o.strike_price == atm_strike and o.option_type and o.option_type.strip().upper() == 'CE'), 0.0)
                        atm_pe_price = next((o.close_price for o in straddle_near_opts if o.strike_price == atm_strike and o.option_type and o.option_type.strip().upper() == 'PE'), 0.0)
                    atm_straddle_near_month = atm_ce_price + atm_pe_price

            # Weekly NIFTY Straddle
            atm_straddle_weekly_nifty = 0.0
            if ref_price > 0:
                # Find all active expiries for options strictly after today if today is an expiry
                sym_expiries = list(set([o.expiry_date for o in all_opts if o.expiry_date >= target_date]))
                sym_expiries.sort()

                # If today is the closest expiry, use the next one (next week)
                if sym_expiries and sym_expiries[0] == target_date and len(sym_expiries) > 1:
                    closest_weekly_expiry = sym_expiries[1]
                elif sym_expiries:
                    closest_weekly_expiry = sym_expiries[0]
                else:
                    closest_weekly_expiry = None

                if closest_weekly_expiry:
                    weekly_opts = [o for o in all_opts if o.expiry_date == closest_weekly_expiry]
                    if weekly_opts:
                        weekly_strikes = list(set([o.strike_price for o in weekly_opts]))
                        if weekly_strikes:
                            weekly_atm_strike = min(weekly_strikes, key=lambda x: abs(x - ref_price))
                            w_ce_price = next((o.close_price for o in weekly_opts if o.strike_price == weekly_atm_strike and o.option_type in ['CE', 'OPTIDX_CE', 'OPTSTK_CE']), 0.0)
                            w_pe_price = next((o.close_price for o in weekly_opts if o.strike_price == weekly_atm_strike and o.option_type in ['PE', 'OPTIDX_PE', 'OPTSTK_PE']), 0.0)
                            if not w_ce_price and not w_pe_price:
                                w_ce_price = next((o.close_price for o in weekly_opts if o.strike_price == weekly_atm_strike and o.option_type and o.option_type.strip().upper() == 'CE'), 0.0)
                                w_pe_price = next((o.close_price for o in weekly_opts if o.strike_price == weekly_atm_strike and o.option_type and o.option_type.strip().upper() == 'PE'), 0.0)
                            atm_straddle_weekly_nifty = w_ce_price + w_pe_price

            atm_iv_near, skew_near = self.calculate_iv_and_skew(near_opts, ref_price, near_fut.expiry_date, target_date, proxy_ann_vol)
            atm_iv_next, _ = self.calculate_iv_and_skew(next_opts, ref_price, next_fut.expiry_date, target_date, proxy_ann_vol) if next_fut else (0.0, 0.0)
            _, skew_far = self.calculate_iv_and_skew(far_opts, ref_price, far_fut.expiry_date, target_date, proxy_ann_vol) if far_fut else (0.0, 0.0)

            # Other Metrics
            mwpl_arr = self._get_mwpl_array(target_date, symbol)
            pe_val = self._get_pe_ratio(target_date, symbol)

            iv_rank, iv_pctile = self._calculate_iv_rank_percentile(symbol, target_date, atm_iv_near)

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

            record.close_price = self._safe_float(near_fut.close_price)
            record.eq_close_price = self._safe_float(cash_close)
            record.vwap = self._safe_float(eq_record.avg_price if eq_record and hasattr(eq_record, 'avg_price') else 0.0)
            record.total_eq_volume = self._safe_float(eq_record.total_traded_qty if eq_record and hasattr(eq_record, 'total_traded_qty') else 0)

            # Fetch delivery percentage for the day
            mto_record = self.db.query(MTODelivery).filter(
                MTODelivery.trade_date == target_date,
                MTODelivery.security_name.in_([symbol, getattr(eq_record, 'series', '')])
            ).first()
            record.delivery_pct = self._safe_float(mto_record.deliverable_pct if mto_record else 0.0)

            record.futures_total_vol = self._safe_float(total_vol)
            record.futures_total_oi = self._safe_float(total_oi)
            record.pcr_oi = self._safe_float(pcr_oi)
            record.highest_oi_strike_pe = self._safe_float(highest_pe_strike)
            record.highest_oi_strike_ce = self._safe_float(highest_ce_strike)
            record.highest_oi_pe_value = self._safe_float(highest_pe_value)
            record.highest_oi_ce_value = self._safe_float(highest_ce_value)
            record.highest_oi_pe_oi = self._safe_float(highest_pe_oi)
            record.highest_oi_ce_oi = self._safe_float(highest_ce_oi)
            record.atm_straddle_near_month = self._safe_float(atm_straddle_near_month)
            record.atm_straddle_weekly_nifty = self._safe_float(atm_straddle_weekly_nifty)
            record.pct_away_highest_pe = self._safe_float(((highest_pe_strike - ref_price) / ref_price) * 100 if highest_pe_strike and ref_price else None)
            record.pct_away_highest_ce = self._safe_float(((highest_ce_strike - ref_price) / ref_price) * 100 if highest_ce_strike and ref_price else None)
            record.chg_oi_options = self._safe_float(chg_oi_opts)
            record.chg_oi_futures = self._safe_float(chg_oi_futs)
            record.near_expiry_date = near_fut.expiry_date if near_fut else None
            record.next_expiry_date = next_fut.expiry_date if next_fut else None
            record.far_expiry_date = far_fut.expiry_date if far_fut else None
            record.near_fut_close = self._safe_float(near_fut.close_price) if near_fut else None
            record.next_fut_close = self._safe_float(next_fut.close_price) if next_fut else None
            record.far_fut_close = self._safe_float(far_fut.close_price) if far_fut else None
            record.total_options_call_oi = self._safe_float(call_oi)
            record.total_options_put_oi = self._safe_float(put_oi)
            record.atm_iv_near = self._safe_float(atm_iv_near)
            record.atm_iv_next = self._safe_float(atm_iv_next)
            record.iv_rank_252 = self._safe_float(iv_rank)
            record.iv_percentile_252 = self._safe_float(iv_pctile)
            record.skew_25d_near = self._safe_float(skew_near)
            record.skew_25d_far = self._safe_float(skew_far)
            record.rollover_pct = self._safe_float(rollover_pct)
            record.daily_volatility = self._safe_float(daily_vol)
            record.z_score = self._safe_float(techs.get('z_score', 0.0))
            record.mwpl_array = mwpl_arr
            record.basis_1_bps = self._safe_float(basis_1)
            record.basis_2_bps = self._safe_float(basis_2)
            record.calendar_spread_1_bps = self._safe_float(cal_spread_1)
            record.calendar_spread_2_bps = self._safe_float(cal_spread_2)
            record.pe_ratio = self._safe_float(pe_val)
            record.beta_252 = self._safe_float(betas['beta_252'])
            record.beta_500 = self._safe_float(betas['beta_500'])
            record.r_squared_252 = self._safe_float(betas['r_squared_252'])
            record.r_squared_500 = self._safe_float(betas['r_squared_500'])
            record.price_pct_change = self._safe_float(techs.get('price_pct_change', 0.0))
            record.relative_volume_20d = self._safe_float(techs.get('rel_vol_20d', 0.0))
            record.atr_14_cash = self._safe_float(techs['atr_14'])
            record.ema_20_cash = self._safe_float(techs['ema_20'])
            record.ema_50_cash = self._safe_float(techs['ema_50'])
            record.ema_100_cash = self._safe_float(techs['ema_100'])
            record.ema_200_cash = self._safe_float(techs['ema_200'])
            record.mavg_delivery_vol_pct_5d = self._safe_float(deliv['5d'])
            record.mavg_delivery_vol_pct_10d = self._safe_float(deliv['10d'])
            record.mavg_delivery_vol_pct_20d = self._safe_float(deliv['20d'])
            record.mavg_delivery_vol_pct_30d = self._safe_float(deliv['30d'])

            # Store New Historical Stats
            record.delivery_pct_avg = self._safe_float(deliv.get('avg', 0.0))
            record.highest_delivery_pct = self._safe_float(deliv.get('high', 0.0))
            record.eq_vol_avg = self._safe_float(stock_hist['volume'].mean()) if stock_hist is not None and not stock_hist.empty else 0.0
            record.highest_eq_vol = self._safe_float(stock_hist['volume'].max()) if stock_hist is not None and not stock_hist.empty else 0.0

            processed_count += 1

        self.db.commit()
        return {"status": "success", "processed_symbols": processed_count, "date": str(target_date)}
