"""NSE Data Importer - Direct-to-TimescaleDB"""
import io, gzip, zipfile, logging
from datetime import datetime, date
from typing import Any, Callable, Dict, List
from contextlib import contextmanager

import pandas as pd
import requests
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.config.defaults.nse import NSE_FILE_PATTERNS
from backend.infrastructure.db import SessionLocal
from backend.ingest import nse_models as models
from backend.domain.market.models import Bhavcopy
from backend.models.audit import SystemLog
from backend.ingest.timescale import setup_all_timescale_policies
from backend.ingest.nse_session import NSESessionManager
from backend.ingest.date_utils import NSEHolidayCalendar, format_nse_date
from backend.ingest.field_mapper import FieldMapper

logger = logging.getLogger(__name__)

class NSEDataImporter:
    """Main importer: downloads → parses → inserts to TimescaleDB."""

    def __init__(self, db_session: Session | None = None):
        self.http = NSESessionManager()
        self.holidays = NSEHolidayCalendar()
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

    def _get_candidate_urls(self, pattern_key: str, dt: date) -> List[str]:
        """Generate list of candidate URLs for a given pattern key and date."""
        if pattern_key not in NSE_FILE_PATTERNS:
            return []

        # New structure: (List[(url_fmt, date_fmt)], table_name)
        config_entry = NSE_FILE_PATTERNS[pattern_key]

        # Handle legacy structure if config hasn't been fully migrated (safety check)
        if isinstance(config_entry[0], str):
            # Legacy: (url_pattern, date_fmt, table_name)
            # Adapt to new structure temporarily
            url_pattern, date_fmt, _ = config_entry
            patterns_list = [(url_pattern, date_fmt)]
        else:
            # New structure
            patterns_list, _ = config_entry

        from backend.config.defaults.nse import NSE_ARCHIVES_BASE, NSE_BASE_URL

        candidates = []
        for url_fmt, date_fmt in patterns_list:
            formatted_date = format_nse_date(dt, date_fmt)
            path = url_fmt.format(formatted_date)

            # Determine base URL
            # If path starts with /archives, usually use ARCHIVES_BASE
            # If path starts with /content or /products, usually use MAIN_URL or ARCHIVES_BASE?
            # User instructions implied most failures were 404 on archives.
            # nselib uses NSE_ARCHIVES_URL for most historical data.
            # We will try ARCHIVES_BASE for all standard downloads as per config.

            full_url = f"{NSE_ARCHIVES_BASE}{path}"
            candidates.append(full_url)

            # If it's a "product" or "report", maybe try main URL too?
            # For now, let's stick to the explicit paths in config.

        return candidates

    def _parse_response(self, resp: requests.Response, pattern_key: str) -> pd.DataFrame | None:
        """Parse response object (wrapper around _parse_content)."""
        return self._parse_content(resp.content, pattern_key)

    def _parse_content(self, content: bytes, pattern_key: str) -> pd.DataFrame | None:
        """Parse raw content based on file type."""
        try:
            # Handle specific known zip/gz patterns first
            if pattern_key in ['fno_bhav', 'margin_trading']:
                 with zipfile.ZipFile(io.BytesIO(content)) as zf:
                    # Usually just one CSV in there
                    csv_name = [n for n in zf.namelist() if n.lower().endswith('.csv')][0]
                    with zf.open(csv_name) as f:
                        return pd.read_csv(f, low_memory=False)

            elif pattern_key == 'nse_security':
                with gzip.GzipFile(fileobj=io.BytesIO(content)) as gz:
                    return pd.read_csv(gz, low_memory=False)

            # MWPL: Special header handling (Headers in Row 2)
            if pattern_key == 'mwpl_cli':
                 df_raw = pd.read_excel(io.BytesIO(content), header=None)
                 if len(df_raw) < 2:
                     return pd.DataFrame()
                 # Use row 2 (index 1) as headers
                 headers = df_raw.iloc[1].fillna('').astype(str).tolist()
                 # Data starts from row 3 (index 2)
                 data = df_raw.iloc[2:].copy()
                 data.columns = headers
                 return data

            # FII Stats: Often has metadata in first few rows
            if pattern_key == 'fii_stats':
                 return pd.read_excel(io.BytesIO(content))

            # Default CSV / DAT (often CSV-like)
            # Try to decode as text
            try:
                text_content = content.decode('utf-8')
            except UnicodeDecodeError:
                text_content = content.decode('latin-1')

            # MTO: Skip first 2 lines
            if pattern_key == 'mto':
                lines = text_content.strip().split('\n')
                if len(lines) < 3:
                     return pd.DataFrame()
                # Skip first 2 header rows, use 3rd row as headers (lines[2])
                header_line = lines[2]
                data_lines = lines[3:]
                csv_str = header_line + '\n' + '\n'.join(data_lines)
                return pd.read_csv(io.StringIO(csv_str), low_memory=False)

            # Special handling for fao_participant_oi (skip metadata header)
            skiprows = 0
            if pattern_key == 'fao_participant_oi':
                # Check if first line is metadata
                first_line = text_content.split('\n')[0]
                if 'Participant wise Open Interest' in first_line:
                    skiprows = 1

            return pd.read_csv(io.StringIO(text_content), skiprows=skiprows, low_memory=False)

        except Exception as e:
            logger.error(f"Failed to parse content for {pattern_key}: {e}")
            try:
                # Log snippet for debugging
                snippet = content[:200]
                logger.error(f"Content snippet (first 200 bytes): {snippet}")
            except:
                pass
            return None

    def _log_import(self, db: Session, import_date: date, table_name: str,
                   status: str, rows_inserted: int, rows_updated: int = 0,
                   error_msg: str | None = None):
        # 1. Log to ImportLog table (Structured Audit)
        log = models.ImportLog(
            import_date=import_date,
            table_name=table_name,
            status=status,
            rows_inserted=rows_inserted,
            rows_updated=rows_updated,
            error_msg=error_msg
        )
        db.add(log)

        # 2. Log to SystemLog (Visible in Audit Trail UI)
        # Only log failures or significant completions to reduce noise
        level = "ERROR" if status in ["FAILED", "ERROR"] else "INFO"
        msg = f"NSE Import: {table_name} for {import_date} - {status}"
        if error_msg:
            msg += f" | Error: {error_msg}"
        else:
            msg += f" | Rows: {rows_inserted + rows_updated}"

        sys_log = SystemLog(
            timestamp=datetime.now(),
            level=level,
            source="NSE_Importer",
            event_type="Data_Import",
            message=msg,
            meta_data={"rows": rows_inserted + rows_updated, "table": table_name}
        )
        db.add(sys_log)

    def _upsert_batch(self, db: Session, model_class, records: list[dict[str, Any]],
                     unique_fields: list[str]) -> tuple[int, int]:
        if not records:
            return 0, 0

        # Actually, let's use the core upsert if we are on Postgres (which we are)
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        try:
            table = model_class.__table__

            # Filter records to only include columns that exist in the table
            valid_cols = set(c.name for c in table.columns)
            cleaned_records = [{k: v for k, v in r.items() if k in valid_cols} for r in records]

            if not cleaned_records:
                return 0, 0

            stmt = pg_insert(table).values(cleaned_records)

            # Prepare update dict for on_conflict
            # update all columns except primary key and unique fields
            update_cols = {c.name: c for c in table.columns
                          if c.name not in unique_fields and c.name != 'id' and c.name != 'created_at'}

            if update_cols:
                stmt = stmt.on_conflict_do_update(
                    index_elements=unique_fields,
                    set_=update_cols
                )
            else:
                stmt = stmt.on_conflict_do_nothing(index_elements=unique_fields)

            result = db.execute(stmt)
            return result.rowcount, 0

        except Exception as e:
            logger.error(f"Batch upsert failed: {e}")
            raise e

    def _upsert_legacy_bhavcopy(self, db: Session, records: list[dict[str, Any]], segment: str):
        """Dual-write to legacy Bhavcopy table for backward compatibility."""
        if not records:
            return

        try:
            legacy_records = []
            for r in records:
                lr = {
                    'trade_date': r['trade_date'],
                    'segment': segment,
                    'symbol': r.get('symbol') or r.get('ticker_symb'),
                    'instrument_type': r.get('instrument_type', 'EQ' if segment == 'CM' else 'XX'),

                    # Prices
                    'open': r.get('open_price'),
                    'high': r.get('high_price'),
                    'low': r.get('low_price'),
                    'close': r.get('close_price'),
                    'last': r.get('last_price'),
                    'prev_close': r.get('prev_close'),
                    'settlement_price': r.get('settle_price'),

                    # Volume/OI
                    'total_traded_qty': r.get('total_traded_qty') or r.get('total_trading_vol'),
                    'total_traded_val': r.get('turnover_lacs') or r.get('total_trf_val'),
                    'total_trades': r.get('no_of_trades'),
                    'open_interest': r.get('open_interest'),
                    'change_in_oi': r.get('change_in_oi'),

                    # CM Specific
                    'series': r.get('series'),
                    'deliverable_qty': r.get('deliverable_qty'),
                    'deliverable_pct': r.get('deliverable_pct'),

                    # FO Specific
                    'expiry_date': r.get('expiry_date'),
                    'strike_price': r.get('strike_price'),
                    'option_type': r.get('option_type'),
                    'instrument_name': r.get('instrument_name'),
                }
                legacy_records.append(lr)

            # Using Delete-Insert strategy for reliability on daily data
            trade_date = records[0]['trade_date']
            db.query(Bhavcopy).filter(
                Bhavcopy.trade_date == trade_date,
                Bhavcopy.segment == segment
            ).delete(synchronize_session=False)

            db.bulk_insert_mappings(Bhavcopy, legacy_records)
            logger.info(f"Synced {len(legacy_records)} rows to legacy Bhavcopy ({segment})")

        except Exception as e:
            logger.error(f"Legacy sync failed for {segment}: {e}")
            # Non-blocking error

    def _get_model_class(self, pattern_key: str):
        # Map pattern key to DB model
        mapping = {
            'sec_bhavdata': models.BhavcopyEQ,
            'fno_bhav': models.BhavcopyFO,
            'fao_participant_oi': models.FAOParticipantOI,
            'fovolt': models.FOVolatility,
            'block_deals': models.BlockDeal,
            'bulk_deals': models.BulkDeal,
            'fii_stats': models.FIIDerivativesStat,
            'mto': models.MTODelivery,
            'mwpl_cli': models.MWPLClientPosition,
            'nse_security': models.SecurityMaster,
            'pe_ratio': models.PERatio,
            'var_begin': models.VaRStat,
            'var_end': models.VaRStat,
            'contract_delta': models.ContractDelta,
            'margin_trading': models.MarginTrading,
        }
        return mapping.get(pattern_key)

    def _get_unique_fields(self, pattern_key: str) -> List[str]:
        mapping = {
            'sec_bhavdata': ['symbol', 'series', 'trade_date'],
            'fno_bhav': ['trade_date', 'ticker_symb', 'expiry_date', 'strike_price', 'option_type'],
            'fao_participant_oi': ['trade_date', 'client_type'],
            'fovolt': ['trade_date', 'symbol'],
            'block_deals': ['date', 'symbol', 'client_name', 'buy_sell'],
            'bulk_deals': ['date', 'symbol', 'client_name', 'buy_sell'],
            'fii_stats': ['date', 'instrument_type'],
            'mto': ['trade_date', 'security_name'],
            'mwpl_cli': ['date', 'underlying_stock', 'client_position_num'],
            'nse_security': ['fin_instrm_id'],
            'pe_ratio': ['date', 'symbol'],
            'var_begin': ['date', 'symbol', 'series', 'file_type'],
            'var_end': ['date', 'symbol', 'series', 'file_type'],
            'contract_delta': ['date', 'symbol', 'expiry_date', 'strike_price', 'option_type'],
            'margin_trading': ['date', 'symbol'],
        }
        return mapping.get(pattern_key, [])

    def import_date(self, trade_date: date, patterns: list[str] | None = None,
                   force: bool = False, progress_callback: Callable[[dict[str, Any]], None] | None = None) -> dict[str, Any]:
        """Import all configured files for a given date with progress tracking."""
        if not self.holidays.is_trading_day(trade_date):
            return {
                'status': 'SKIPPED',
                'reason': f'{trade_date} is not a trading day',
                'previous_trading_day': self.holidays.get_previous_trading_day(trade_date).isoformat()
            }

        results = {}
        patterns_to_run = patterns or list(NSE_FILE_PATTERNS.keys())
        total_files = len(patterns_to_run)

        completed_files = []
        failed_files = []

        with self.get_db() as db:
            for idx, pattern_key in enumerate(patterns_to_run):
                # Report progress start
                progress = {
                    'current_file': pattern_key,
                    'file_number': idx + 1,
                    'total_files': total_files,
                    'percent': int((idx / total_files) * 100),
                    'status': 'in_progress',
                    'files_completed': completed_files,
                    'files_failed': failed_files,
                    'timestamp': datetime.now().isoformat()
                }
                logger.info(f"[{idx+1}/{total_files}] Processing {pattern_key}...")

                if progress_callback:
                    progress_callback(progress)

                try:
                    candidates = self._get_candidate_urls(pattern_key, trade_date)
                    if not candidates:
                         results[pattern_key] = {'status': 'ERROR', 'error': 'Invalid pattern configuration'}
                         failed_files.append({"name": pattern_key, "error": "Invalid pattern configuration"})
                         continue

                    # Try candidates in order (Fallback Logic)
                    resp = None
                    success_url = None
                    last_error = None

                    for url in candidates:
                        logger.info(f"Trying {pattern_key} at {url}")
                        resp = self.http.get(url)

                        if resp and resp.status_code == 200:
                            success_url = url
                            logger.info(f"✓ Downloaded {pattern_key} from {url}")
                            break
                        else:
                            code = resp.status_code if resp else 'No Response'
                            logger.warning(f"Failed {pattern_key} at {url} (HTTP {code})")
                            last_error = f"HTTP {code}"

                    if not success_url:
                        error_msg = f'All candidates failed. Last error: {last_error}'
                        results[pattern_key] = {'status': 'FAILED', 'error': error_msg}
                        failed_files.append({"name": pattern_key, "error": error_msg})
                        continue

                    # Parse
                    df = self._parse_response(resp, pattern_key)

                    if df is None or df.empty:
                        results[pattern_key] = {'status': 'EMPTY', 'rows': 0}
                        logger.info(f"Empty file: {pattern_key}")
                        completed_files.append(pattern_key)
                        continue

                    # Detect format and Map
                    format_info = FieldMapper.detect_format(df)
                    # For deals, pass the target table name
                    if pattern_key in ['bulk_deals', 'block_deals']:
                         format_info['target_table'] = pattern_key

                    # Override format detection if we know the file source strongly?
                    # Ideally detection is robust enough.
                    # Fallback if detection fails but we know the pattern?
                    if format_info['type'] == 'unknown':
                        logger.warning(f"Could not auto-detect format for {pattern_key}. File headers: {df.columns.tolist()}")
                        # Maybe try to force based on pattern_key?
                        # This would be a future improvement.

                    records = FieldMapper.map_to_records(df, format_info, trade_date)

                    model_class = self._get_model_class(pattern_key)
                    unique_fields = self._get_unique_fields(pattern_key)

                    if not model_class or not unique_fields:
                        logger.error(f"No model/unique fields configured for {pattern_key}")
                        continue

                    # Upsert to TimescaleDB
                    inserted, updated = self._upsert_batch(db, model_class, records, unique_fields)

                    # Dual-write to Legacy Bhavcopy
                    if pattern_key == 'sec_bhavdata':
                        self._upsert_legacy_bhavcopy(db, records, 'CM')
                    elif pattern_key == 'fno_bhav':
                        self._upsert_legacy_bhavcopy(db, records, 'FO')

                    results[pattern_key] = {
                        'status': 'SUCCESS',
                        'rows_processed': inserted + updated
                    }
                    self._log_import(db, trade_date, pattern_key, 'SUCCESS', inserted, updated)
                    logger.info(f"✓ {pattern_key}: {inserted+updated} processed")
                    completed_files.append(pattern_key)

                except Exception as e:
                    logger.exception(f"Error importing {pattern_key}: {e}")
                    results[pattern_key] = {'status': 'ERROR', 'error': str(e)}
                    self._log_import(db, trade_date, pattern_key, 'FAILED', 0, 0, str(e))
                    failed_files.append({"name": pattern_key, "error": str(e)})

        # Final progress update
        if progress_callback:
            progress_callback({
                'current_file': 'Done',
                'file_number': total_files,
                'total_files': total_files,
                'percent': 100,
                'status': 'success',
                'files_completed': completed_files,
                'files_failed': failed_files,
                'timestamp': datetime.now().isoformat()
            })

        success_count = sum(1 for r in results.values() if r.get('status') == 'SUCCESS')

        logger.info(f"Import completed. Success: {success_count}/{total_files}")

        return {
            'status': 'COMPLETED',
            'date': trade_date.isoformat(),
            'files_processed': total_files,
            'successful': success_count,
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
