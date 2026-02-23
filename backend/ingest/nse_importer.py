"""NSE Data Importer - Direct-to-TimescaleDB"""
import io, gzip, zipfile, logging
from datetime import datetime, date
from typing import Any, Callable, Dict, List
from contextlib import contextmanager

import pandas as pd
import requests
from sqlalchemy.orm import Session

from backend.config.defaults.nse import NSE_FILE_PATTERNS
from backend.infrastructure.db import SessionLocal
from backend.ingest import nse_models as models
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

    def _build_url(self, pattern_key: str, dt: date) -> str | None:
        if pattern_key not in NSE_FILE_PATTERNS:
            return None
        url_pattern, date_fmt, _ = NSE_FILE_PATTERNS[pattern_key]
        formatted = format_nse_date(dt, date_fmt)
        from backend.config.defaults.nse import NSE_ARCHIVES_BASE
        return f"{NSE_ARCHIVES_BASE}{url_pattern.format(formatted)}"

    def _parse_response(self, resp: requests.Response, pattern_key: str) -> pd.DataFrame | None:
        """Parse response based on file type in pattern key or content."""
        try:
            # Handle specific known zip/gz patterns first
            if pattern_key == 'fno_bhav':
                 with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
                    # Usually just one CSV in there
                    csv_name = [n for n in zf.namelist() if n.lower().endswith('.csv')][0]
                    with zf.open(csv_name) as f:
                        return pd.read_csv(f, low_memory=False)

            elif pattern_key == 'nse_security':
                with gzip.GzipFile(fileobj=io.BytesIO(resp.content)) as gz:
                    return pd.read_csv(gz, low_memory=False)

            # Content-type based fallback or extension based
            # But we know the patterns from config

            # Excel files
            if pattern_key in ['fii_stats', 'mwpl_cli']:
                 # nselib uses read_excel
                 return pd.read_excel(io.BytesIO(resp.content))

            # Default CSV / DAT (often CSV-like)
            # Some DAT files are fixed width? But user said MTO is DAT.
            # Let's try read_csv first. MTO usually comma separated or pipe.
            # If MTO fails with read_csv, we might need specific handling.
            # nselib treats MTO as CSV (skiprows might be needed for headers)
            return pd.read_csv(io.StringIO(resp.text), low_memory=False)

        except Exception as e:
            logger.error(f"Failed to parse response for {pattern_key}: {e}")
            return None

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

        # Simple bulk insert for now, real upsert needs unique constraint handling
        # For TimescaleDB/Postgres, we can use ON CONFLICT
        # But for SQLA ORM generic, we iterate.
        # Optimization: Use bulk_save_objects or core insert().on_conflict_do_update()
        # For now, keeping the loop logic from memory but might be slow for large datasets.
        # Let's try to do a faster check.

        # If we assume daily clean import for a date, we could delete and insert?
        # But we want upsert.

        # Actually, let's use the core upsert if we are on Postgres (which we are)
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        if not records:
            return 0, 0

        try:
            table = model_class.__table__
            stmt = pg_insert(table).values(records)

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
            # Rowcount for upsert is weird (often inserts + updates combined or just affected rows)
            # Postgres: rowcount is number of rows processed
            # We will just return total processed.
            return result.rowcount, 0 # Precise count distinction is hard with bulk upsert

        except Exception as e:
            logger.error(f"Batch upsert failed: {e}")
            # Fallback to slow loop if bulk fails? Or just raise.
            raise e

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
                    url = self._build_url(pattern_key, trade_date)
                    if not url:
                        results[pattern_key] = {'status': 'ERROR', 'error': 'Invalid pattern'}
                        failed_files.append({"name": pattern_key, "error": "Invalid pattern"})
                        continue

                    logger.debug(f"Downloading {pattern_key} from {url}")
                    resp = self.http.get(url)

                    if not resp:
                        results[pattern_key] = {'status': 'FAILED', 'error': 'Download failed'}
                        logger.error(f"Download failed: {pattern_key}")
                        failed_files.append({"name": pattern_key, "error": "Download failed"})
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

                    # Upsert
                    inserted, updated = self._upsert_batch(db, model_class, records, unique_fields)

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
