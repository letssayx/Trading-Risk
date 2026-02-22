"""NSE Data Importer - Direct-to-TimescaleDB"""
import io, gzip, zipfile, logging, time
from datetime import datetime, timedelta, date
from typing import Any
from contextlib import contextmanager

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from sqlalchemy.orm import Session

from backend.config.defaults.nse import (
    NSE_ARCHIVES_BASE, NSE_MAIN_URL, NSE_FILE_PATTERNS,
    REQUEST_TIMEOUT, RATE_LIMIT_DELAY, MAX_RETRIES,
    RETRY_BACKOFF_FACTOR, USER_AGENT
)
from backend.infrastructure.db import SessionLocal
from backend.ingest import nse_models as models
from backend.ingest.timescale import setup_all_timescale_policies

logger = logging.getLogger(__name__)


class NSESessionManager:
    """HTTP session with NSE-compatible headers."""

    def __init__(self):
        self.session = self._create_session()
        self._init_cookies()

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        retry = Retry(total=MAX_RETRIES, backoff_factor=RETRY_BACKOFF_FACTOR,
                     status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('https://', adapter)
        return session

    def _init_cookies(self):
        try:
            self.session.get(NSE_MAIN_URL, timeout=15)
        except Exception as e:
            logger.warning(f"Session init warning: {e}")

    def get(self, url: str, **kwargs) -> requests.Response | None:
        time.sleep(RATE_LIMIT_DELAY)
        try:
            resp = self.session.get(url, timeout=kwargs.pop('timeout', REQUEST_TIMEOUT), **kwargs)
            resp.raise_for_status()
            return resp
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP {e.response.status_code}: {url}")
            return None
        except Exception as e:
            logger.error(f"Request failed: {url} - {e}")
            return None


class HolidayManager:
    """NSE trading calendar."""

    def __init__(self, custom_holidays: set[str] | None = None):
        from backend.config.defaults.nse import DEFAULT_NSE_HOLIDAYS
        self.holidays = custom_holidays or DEFAULT_NSE_HOLIDAYS.copy()

    def is_trading_day(self, dt: date) -> bool:
        if dt.weekday() >= 5:
            return False
        return dt.strftime("%Y-%m-%d") not in self.holidays

    def get_previous_trading_day(self, dt: date) -> date:
        prev = dt - timedelta(days=1)
        while not self.is_trading_day(prev):
            prev -= timedelta(days=1)
        return prev


class NSEDataImporter:
    """Main importer: downloads → parses → inserts to TimescaleDB."""

    def __init__(self, db_session: Session | None = None):
        self.http = NSESessionManager()
        self.holidays = HolidayManager()
        self._db_session = db_session

    @contextmanager
    def get_db(self) -> Session:
        if self._db_session:
            yield self._db_session
        else:
            db = SessionLocal()
            try:
                yield db
                db.commit()
            except:
                db.rollback()
                raise
            finally:
                db.close()

    def _format_date(self, dt: date, pattern: str) -> str:
        formats = {
            'ddmmyy': dt.strftime("%d%m%y"),
            'ddmmyyyy': dt.strftime("%d%m%Y"),
            'yyyymmdd': dt.strftime("%Y%m%d"),
            'dd-MMM-yyyy': dt.strftime("%d-%b-%Y"),
        }
        return formats.get(pattern, dt.strftime(pattern))

    def _build_url(self, pattern_key: str, dt: date) -> str | None:
        if pattern_key not in NSE_FILE_PATTERNS:
            return None
        url_pattern, date_fmt, _ = NSE_FILE_PATTERNS[pattern_key]
        formatted = self._format_date(dt, date_fmt)
        return f"{NSE_ARCHIVES_BASE}{url_pattern.format(date=formatted)}"

    def _parse_date_field(self, value: Any, fallback: date | None = None) -> date | None:
        if pd.isna(value) or not value:
            return fallback
        value = str(value).strip()
        for fmt in ['%d-%m-%Y', '%d-%b-%Y', '%d-%b-%y', '%Y-%m-%d', '%d%m%Y']:
            try:
                return datetime.strptime(value, fmt).date()
            except:
                continue
        return fallback

    def _clean_numeric(self, value: Any) -> float | None:
        if pd.isna(value) or str(value).strip() == '':
            return None
        try:
            return float(str(value).replace(',', '').strip())
        except:
            return None

    def _clean_integer(self, value: Any) -> int | None:
        cleaned = self._clean_numeric(value)
        return int(cleaned) if cleaned is not None else None

    def _parse_csv_response(self, resp: requests.Response, **kwargs) -> pd.DataFrame:
        return pd.read_csv(io.StringIO(resp.text), **kwargs)

    def _parse_xls_response(self, resp: requests.Response, **kwargs) -> pd.DataFrame:
        return pd.read_excel(io.BytesIO(resp.content), **kwargs)

    def _parse_zip_csv(self, resp: requests.Response, **kwargs) -> pd.DataFrame:
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            csv_name = [n for n in zf.namelist() if n.endswith('.csv')][0]
            with zf.open(csv_name) as f:
                return pd.read_csv(f, **kwargs)

    def _parse_gz_csv(self, resp: requests.Response, **kwargs) -> pd.DataFrame:
        with gzip.GzipFile(fileobj=io.BytesIO(resp.content)) as gz:
            return pd.read_csv(gz, **kwargs)

    def _log_import(self, db: Session, import_date: date, table_name: str,
                   status: str, rows_inserted: int, rows_updated: int = 0,
                   error_msg: str | None = None):
        log = models.ImportLog(
            import_date=import_date,
            table_name=table_name,
            status=status,
            rows_inserted=rows_inserted,
            rows_updated=rows_updated,
            error_msg=error_msg
        )
        db.add(log)

    def _upsert_batch(self, db: Session, model_class, records: list[dict[str, Any]],
                     unique_fields: list[str]) -> tuple[int, int]:
        if not records:
            return 0, 0
        inserted, updated = 0, 0
        for record in records:
            from sqlalchemy import and_
            filters = [getattr(model_class, field) == record[field] for field in unique_fields]
            existing = db.query(model_class).filter(and_(*filters)).first()
            if existing:
                for key, value in record.items():
                    if key != 'id':
                        setattr(existing, key, value)
                updated += 1
            else:
                db.add(model_class(**record))
                inserted += 1
        return inserted, updated

    def _insert_bhavcopy_eq(self, df: pd.DataFrame, trade_date: date, db: Session) -> tuple[int, int]:
        if df.empty:
            return 0, 0
        if 'SERIES' in df.columns:
            df = df[df['SERIES'] == 'EQ'].copy()
        if df.empty:
            return 0, 0

        records = []
        for _, row in df.iterrows():
            records.append({
                'symbol': str(row.get('SYMBOL', '')).strip(),
                'series': row.get('SERIES', 'EQ'),
                'trade_date': trade_date,
                'prev_close': self._clean_numeric(row.get('PREV_CLOSE')),
                'open_price': self._clean_numeric(row.get('OPEN_PRICE')),
                'high_price': self._clean_numeric(row.get('HIGH_PRICE')),
                'low_price': self._clean_numeric(row.get('LOW_PRICE')),
                'last_price': self._clean_numeric(row.get('LAST_PRICE')),
                'close_price': self._clean_numeric(row.get('CLOSE_PRICE')),
                'avg_price': self._clean_numeric(row.get('AVG_PRICE')),
                'total_traded_qty': self._clean_integer(row.get('TTL_TRD_QNTY')),
                'turnover_lacs': self._clean_numeric(row.get('TURNOVER_LACS')),
                'no_of_trades': self._clean_integer(row.get('NO_OF_TRADES')),
                'deliverable_qty': self._clean_integer(row.get('DELIV_QTY')),
                'deliverable_pct': self._clean_numeric(row.get('DELIV_PER')),
            })
        return self._upsert_batch(db, models.BhavcopyEQ, records, ['symbol', 'series', 'trade_date'])

    def _insert_bhavcopy_fo(self, df: pd.DataFrame, trade_date: date, db: Session) -> tuple[int, int]:
        if df.empty:
            return 0, 0
        records = []
        for _, row in df.iterrows():
            records.append({
                'trade_date': trade_date,
                'ticker_symb': str(row.get('TckrSymb', '')).strip(),
                'expiry_date': self._parse_date_field(row.get('XpryDt')),
                'strike_price': self._clean_numeric(row.get('StrkPric')),
                'option_type': row.get('OptnTp', ''),
                'instrument_name': row.get('FinInstrmNm', ''),
                'open_price': self._clean_numeric(row.get('OpnPric')),
                'high_price': self._clean_numeric(row.get('HghPric')),
                'low_price': self._clean_numeric(row.get('LwPric')),
                'close_price': self._clean_numeric(row.get('ClsPric')),
                'settle_price': self._clean_numeric(row.get('SttlmPric')),
                'open_interest': self._clean_integer(row.get('OpnIntrst')),
                'change_in_oi': self._clean_integer(row.get('ChngInOpnIntrst')),
                'total_trading_vol': self._clean_integer(row.get('TtlTradgVol')),
                'total_trf_val': self._clean_numeric(row.get('TtlTrfVal')),
            })
        return self._upsert_batch(db, models.BhavcopyFO, records,
                                 ['trade_date', 'ticker_symb', 'expiry_date', 'strike_price', 'option_type'])

    def _insert_fao_participant_oi(self, df: pd.DataFrame, trade_date: date, db: Session) -> tuple[int, int]:
        if df.empty:
            return 0, 0
        records = []
        for _, row in df.iterrows():
            records.append({
                'trade_date': trade_date,
                'client_type': str(row.get('Client Type', '')).strip(),
                'future_index_long': self._clean_integer(row.get('Future Index Long')),
                'future_index_short': self._clean_integer(row.get('Future Index Short')),
                'future_stock_long': self._clean_integer(row.get('Future Stock Long')),
                'future_stock_short': self._clean_integer(row.get('Future Stock Short')),
                'option_index_call_long': self._clean_integer(row.get('Option Index Call Long')),
                'option_index_put_long': self._clean_integer(row.get('Option Index Put Long')),
                'option_index_call_short': self._clean_integer(row.get('Option Index Call Short')),
                'option_index_put_short': self._clean_integer(row.get('Option Index Put Short')),
                'option_stock_call_long': self._clean_integer(row.get('Option Stock Call Long')),
                'option_stock_put_long': self._clean_integer(row.get('Option Stock Put Long')),
                'option_stock_call_short': self._clean_integer(row.get('Option Stock Call Short')),
                'option_stock_put_short': self._clean_integer(row.get('Option Stock Put Short')),
                'total_long_contracts': self._clean_integer(row.get('Total Long Contracts')),
                'total_short_contracts': self._clean_integer(row.get('Total Short Contracts')),
            })
        return self._upsert_batch(db, models.FAOParticipantOI, records, ['trade_date', 'client_type'])

    def _insert_fo_volatility(self, df: pd.DataFrame, trade_date: date, db: Session) -> tuple[int, int]:
        if df.empty:
            return 0, 0
        records = []
        for _, row in df.iterrows():
            records.append({
                'trade_date': self._parse_date_field(row.get('Date'), trade_date) or trade_date,
                'symbol': str(row.get('Symbol', '')).strip(),
                'underlying_close_price': self._clean_numeric(row.get('Underlying Close Price (A)')),
                'underlying_annualised_vol': self._clean_numeric(row.get('Underlying Annualised Volatility (F) = E*sqrt(365)')),
                'futures_close_price': self._clean_numeric(row.get('Futures Close Price (G)')),
                'futures_annualised_vol': self._clean_numeric(row.get('Futures Annualised Volatility (L) = K*sqrt(365)')),
                'applicable_daily_vol': self._clean_numeric(row.get('Applicable Daily Volatility (M) = Max (E or K)')),
                'applicable_annualised_vol': self._clean_numeric(row.get('Applicable Annualised Volatility (N) = Max (F or L)')),
            })
        return self._upsert_batch(db, models.FOVolatility, records, ['trade_date', 'symbol'])

    def _insert_deals(self, df: pd.DataFrame, trade_date: date, db: Session,
                     model_class, unique_fields: list[str]) -> tuple[int, int]:
        if df.empty:
            return 0, 0
        records = []
        for _, row in df.iterrows():
            records.append({
                'date': trade_date,
                'symbol': str(row.get('SYMBOL', row.get('Symbol', ''))).strip(),
                'security_name': row.get('SECURITY NAME', row.get('Security Name', '')),
                'client_name': row.get('CLIENT NAME', row.get('Client Name', '')),
                'buy_sell': row.get('BUY/SELL', row.get('Buy/Sell', '')),
                'quantity_traded': self._clean_integer(row.get('QUANTITY TRADED', row.get('Quantity Traded'))),
                'trade_price': self._clean_numeric(row.get('TRADE PRICE/ WEIGHTED. AVG. PRICE',
                                                          row.get('Trade Price / Wght. Avg. Price'))),
                'remarks': row.get('REMARKS', row.get('Remarks', '')),
            })
        return self._upsert_batch(db, model_class, records, unique_fields)

    def _insert_fii_stats(self, df: pd.DataFrame, trade_date: date, db: Session) -> tuple[int, int]:
        if df.empty:
            return 0, 0
        records = []
        for _, row in df.iterrows():
            instrument = row.iloc[0] if len(row) > 0 else ''
            if not instrument or pd.isna(instrument) or 'FII DERIVATIVES' in str(instrument):
                continue
            records.append({
                'date': trade_date,
                'instrument_type': str(instrument).strip(),
                'buy_contracts': self._clean_integer(row.iloc[1] if len(row) > 1 else None),
                'buy_amt_crores': self._clean_numeric(row.iloc[2] if len(row) > 2 else None),
                'sell_contracts': self._clean_integer(row.iloc[3] if len(row) > 3 else None),
                'sell_amt_crores': self._clean_numeric(row.iloc[4] if len(row) > 4 else None),
                'oi_contracts': self._clean_integer(row.iloc[5] if len(row) > 5 else None),
                'oi_amt_crores': self._clean_numeric(row.iloc[6] if len(row) > 6 else None),
            })
        return self._upsert_batch(db, models.FIIDerivativesStat, records, ['date', 'instrument_type'])

    def _insert_mto_delivery(self, df: pd.DataFrame, trade_date: date, db: Session) -> tuple[int, int]:
        if df.empty:
            return 0, 0
        records = []
        for _, row in df.iterrows():
            records.append({
                'trade_date': trade_date,
                'settlement_type': 'N',
                'sr_no': self._clean_integer(row.iloc[1] if len(row) > 1 else None),
                'security_name': str(row.iloc[2] if len(row) > 2 else '').strip(),
                'quantity_traded': self._clean_integer(row.iloc[3] if len(row) > 3 else None),
                'deliverable_qty': self._clean_integer(row.iloc[4] if len(row) > 4 else None),
                'deliverable_pct': self._clean_numeric(row.iloc[5] if len(row) > 5 else None),
            })
        return self._upsert_batch(db, models.MTODelivery, records, ['trade_date', 'security_name'])

    def _insert_mwpl_position(self, df: pd.DataFrame, trade_date: date, db: Session) -> tuple[int, int]:
        if df.empty:
            return 0, 0
        records = []
        for _, row in df.iterrows():
            underlying = str(row.iloc[1] if len(row) > 1 else '').strip()
            if not underlying:
                continue
            for i in range(1, 16):
                col = f'Client {i}'
                if col in row and pd.notna(row[col]):
                    records.append({
                        'date': trade_date,
                        'underlying_stock': underlying,
                        'client_position_num': i,
                        'position_pct': self._clean_numeric(row[col]),
                    })
        return self._upsert_batch(db, models.MWPLClientPosition, records, ['date', 'underlying_stock', 'client_position_num'])

    def _insert_security_master(self, df: pd.DataFrame, db: Session) -> tuple[int, int]:
        if df.empty:
            return 0, 0
        if 'SctySrs' in df.columns:
            df = df[df['SctySrs'] == 'EQ'].copy()
        if df.empty:
            return 0, 0
        records = []
        for _, row in df.iterrows():
            records.append({
                'fin_instrm_id': str(row.get('FinInstrmId', '')).strip(),
                'ticker_symb': str(row.get('TckrSymb', '')).strip(),
                'security_series': row.get('SctySrs', ''),
                'instrument_name': row.get('FinInstrmNm', ''),
                'isin': row.get('ISIN', ''),
                'new_brd_lot_qty': self._clean_integer(row.get('NewBrdLotQty')),
                'par_val': self._clean_numeric(row.get('ParVal')),
                'issued_capital': self._clean_numeric(row.get('IssdCptl')),
                'listed_date': self._parse_date_field(row.get('ListgDt')),
                'additional_info': row.get('AddtlInf', ''),
                'special_ex_date': self._parse_date_field(row.get('SpclExDt')),
                'status': row.get('Sts', ''),
            })
        return self._upsert_batch(db, models.SecurityMaster, records, ['fin_instrm_id'])

    def _insert_pe_ratio(self, df: pd.DataFrame, trade_date: date, db: Session) -> tuple[int, int]:
        if df.empty:
            return 0, 0
        records = []
        for _, row in df.iterrows():
            records.append({
                'date': trade_date,
                'symbol': str(row.get('SYMBOL', '')).strip(),
                'symbol_pe': self._clean_numeric(row.get('SYMBOL P/E')),
                'adjusted_pe': self._clean_numeric(row.get('ADJUSTED P/E')),
            })
        return self._upsert_batch(db, models.PERatio, records, ['date', 'symbol'])

    def _get_handler_for_pattern(self, pattern_key: str):
        handlers = {
            'sec_bhavdata': self._insert_bhavcopy_eq,
            'fno_bhav': self._insert_bhavcopy_fo,
            'fao_participant_oi': self._insert_fao_participant_oi,
            'fovolt': self._insert_fo_volatility,
            'block_deals': lambda df, dt, db: self._insert_deals(df, dt, db, models.BlockDeal,
                                                                  ['date', 'symbol', 'client_name', 'buy_sell']),
            'bulk_deals': lambda df, dt, db: self._insert_deals(df, dt, db, models.BulkDeal,
                                                                 ['date', 'symbol', 'client_name', 'buy_sell']),
            'fii_stats': self._insert_fii_stats,
            'mto': self._insert_mto_delivery,
            'mwpl_cli': self._insert_mwpl_position,
            'nse_security': self._insert_security_master,
            'pe_ratio': self._insert_pe_ratio,
        }
        return handlers.get(pattern_key, lambda df, dt, db: (0, 0))

    def import_date(self, trade_date: date, patterns: list[str] | None = None,
                   force: bool = False) -> dict[str, Any]:
        """Import all configured files for a given date."""
        if not self.holidays.is_trading_day(trade_date):
            return {
                'status': 'SKIPPED',
                'reason': f'{trade_date} is not a trading day',
                'previous_trading_day': self.holidays.get_previous_trading_day(trade_date).isoformat()
            }

        results = {}
        patterns_to_run = patterns or list(NSE_FILE_PATTERNS.keys())

        with self.get_db() as db:
            for pattern_key in patterns_to_run:
                try:
                    url = self._build_url(pattern_key, trade_date)
                    if not url:
                        results[pattern_key] = {'status': 'ERROR', 'error': 'Invalid pattern'}
                        continue

                    logger.info(f"Fetching {pattern_key} for {trade_date}")
                    resp = self.http.get(url)

                    if not resp:
                        results[pattern_key] = {'status': 'FAILED', 'error': 'Download failed'}
                        continue

                    # Parse based on file type
                    if pattern_key == 'fno_bhav':
                        df = self._parse_zip_csv(resp, low_memory=False)
                    elif pattern_key == 'nse_security':
                        df = self._parse_gz_csv(resp, low_memory=False)
                    elif pattern_key in ['fii_stats', 'mwpl_cli']:
                        df = self._parse_xls_response(resp)
                    else:
                        df = self._parse_csv_response(resp, low_memory=False)

                    if df is None or df.empty:
                        results[pattern_key] = {'status': 'EMPTY', 'rows': 0}
                        continue

                    handler = self._get_handler_for_pattern(pattern_key)
                    inserted, updated = handler(df, trade_date, db)

                    results[pattern_key] = {
                        'status': 'SUCCESS',
                        'rows_inserted': inserted,
                        'rows_updated': updated
                    }
                    self._log_import(db, trade_date, pattern_key, 'SUCCESS', inserted, updated)

                except Exception as e:
                    logger.exception(f"Error importing {pattern_key}: {e}")
                    results[pattern_key] = {'status': 'ERROR', 'error': str(e)}
                    self._log_import(db, trade_date, pattern_key, 'FAILED', 0, 0, str(e))

        success = sum(1 for r in results.values() if r.get('status') == 'SUCCESS')
        return {
            'status': 'COMPLETED',
            'date': trade_date.isoformat(),
            'files_processed': len(patterns_to_run),
            'successful': success,
            'details': results
        }

    def setup_timescale(self) -> dict[str, Any]:
        """Initialize TimescaleDB hypertables and policies."""
        with self.get_db() as db:
            return setup_all_timescale_policies(db)

    def get_import_stats(self, start_date: date | None = None, end_date: date | None = None) -> dict[str, Any]:
        """Get import statistics."""
        from backend.ingest.queries import get_import_stats as query_stats
        with self.get_db() as db:
            return query_stats(db, start_date, end_date)
