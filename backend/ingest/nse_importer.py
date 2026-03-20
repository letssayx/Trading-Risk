"""NSE Data Importer - Direct-to-TimescaleDB (Refactored using backend.nselib)"""
import logging
from datetime import datetime, date
from typing import Any, Callable, Dict, List
from contextlib import contextmanager

import pandas as pd
import io
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import text, delete

from backend.infrastructure.db import SessionLocal
from backend.ingest import nse_models as models
from backend.domain.market.models import Bhavcopy
from backend.models.audit import SystemLog
from backend.ingest.timescale import setup_all_timescale_policies
from backend.ingest.date_utils import NSEHolidayCalendar
from backend.ingest.field_mapper import FieldMapper
from backend.ingest.nse_lib import NSELib # Use hardened internal library

logger = logging.getLogger(__name__)

class NSEDataImporter:
    """Main importer: downloads → parses → inserts to TimescaleDB."""

    def __init__(self, db_session: Session | None = None):
        self.lib = NSELib()
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
            finally:
                db.close()

    def _get_model_class(self, key: str):
        mapping = {
            'bhavcopy_eq': models.BhavcopyEQ,
            'bhavcopy_fo': models.BhavcopyFO,
            'fao_participant_oi': models.FAOParticipantOI,
            'fo_volatility': models.FOVolatility,
            'block_deals': models.BlockDeal,
            'bulk_deals': models.BulkDeal,
            'fii_derivatives_stats': models.FIIDerivativesStat,
            'mto': models.MTODelivery,
            'mwpl_cli': models.MWPLClientPosition,
            'nse_security': models.SecurityMaster,
            'pe_ratio': models.PERatio,
            'pe_ratio_idx': models.IndexPERatio,
            'india_vix': models.IndiaVIX,
            'var_stats': models.VaRStat,
            'contract_delta': models.ContractDelta,
            'margin_trading': models.MarginTrading,
            'fii_dii_cash': models.FIIDIICash,
            'historical_index_data': models.HistoricalIndexData,
        }
        if key == 'corporate_actions' and hasattr(models, 'CorporateAction'):
            return getattr(models, 'CorporateAction')
        if key == 'board_meetings' and hasattr(models, 'BoardMeeting'):
            return getattr(models, 'BoardMeeting')

        return mapping.get(key)

    def _get_unique_fields(self, key: str) -> List[str]:
        mapping = {
            'bhavcopy_eq': ['symbol', 'series', 'trade_date'],
            'bhavcopy_fo': ['trade_date', 'ticker_symb', 'instrument_type', 'expiry_date', 'strike_price', 'option_type'],
            'fao_participant_oi': ['trade_date', 'client_type'],
            'fo_volatility': ['trade_date', 'symbol'],
            # Bulk/Block deals: No unique fields for upsert anymore (we do delete-insert)
            'block_deals': [],
            'bulk_deals': [],
            'fii_derivatives_stats': ['date', 'instrument_type'],
            'mto': ['trade_date', 'security_name'],
            'mwpl_cli': ['date', 'underlying_stock', 'client_position_num'],
            'nse_security': ['fin_instrm_id'],
            'pe_ratio': ['date', 'symbol'],
            'pe_ratio_idx': ['date', 'symbol'],
            'india_vix': ['date'],
            'var_stats': ['date', 'symbol', 'series', 'file_type'],
            'contract_delta': ['date', 'symbol', 'expiry_date', 'strike_price', 'option_type'],
            'margin_trading': ['date', 'symbol'],
            # Bulk/Block deals and Corporate Actions/Board Meetings:
            # No unique fields for upsert anymore (we do delete-insert)
            'corporate_actions': ['date', 'symbol', 'purpose'],
            'board_meetings': ['date', 'symbol', 'purpose'],
            'fii_dii_cash': ['trade_date', 'category'],
            'historical_index_data': ['trade_date', 'index_name'],
        }
        return mapping.get(key, [])

    def _parse_content(self, content: bytes, key: str) -> pd.DataFrame:
        """
        Parse raw content into a DataFrame based on file key.
        Used for manual uploads and fallback parsing.
        """
        if not content:
            return pd.DataFrame()

        try:
            if key == 'mwpl_cli':
                return self.lib.parse_mwpl(content)
            elif key == 'mto':
                return self.lib.parse_mto(content)
            elif key == 'fao_participant_oi':
                return self.lib.parse_fao_participant_oi(content)
            elif key == 'fii_derivatives_stats':
                return self.lib.parse_fii_derivatives_stats(content)
            elif key == 'pe_ratio':
                return self.lib.parse_pe_ratio(content)
            elif key == 'pe_ratio_idx':
                return self.lib.parse_pe_ratio_idx(content)
            elif key == 'india_vix':
                return self.lib.parse_india_vix(content)
            elif key == 'corporate_actions':
                return self.lib.parse_corporate_actions(content)
            elif key == 'historical_index_data':
                return pd.read_csv(io.BytesIO(content), low_memory=False)

            # Default CSV Parsing for standard files
            # Check if content is bytes, decode if needed for CSV
            try:
                # Try reading as Excel first if it looks like Excel (magic numbers)
                if content.startswith(b'\xd0\xcf\x11\xe0') or content.startswith(b'PK\x03\x04'):
                     return self.lib._read_excel_robust(content)
            except Exception:
                pass

            # Fallback to CSV
            try:

                return pd.read_csv(io.BytesIO(content), low_memory=False)
            except Exception as e:
                logger.warning(f"Default CSV parse failed for {key}: {e}")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error parsing content for {key}: {e}")
            return pd.DataFrame()

    def _fetch_data(self, key: str, trade_date: date) -> pd.DataFrame:
        """Route to appropriate NSELibClient method."""
        if key == 'bhavcopy_eq':
            return self.lib.get_bhavcopy_eq(trade_date)
        elif key == 'bhavcopy_fo':
            return self.lib.get_bhavcopy_fo(trade_date)
        elif key == 'bulk_deals':
            return self.lib.get_bulk_deals(trade_date)
        elif key == 'block_deals':
            return self.lib.get_block_deals(trade_date)
        elif key == 'fao_participant_oi':
            return self.lib.get_fao_participant_oi(trade_date)
        elif key == 'fii_derivatives_stats':
            return self.lib.get_fii_derivatives_stats(trade_date)
        elif key == 'fo_volatility':
            return self.lib.get_fo_volatility(trade_date)
        elif key == 'mto':
            return self.lib.get_mto_delivery(trade_date)
        elif key == 'mwpl_cli':
            return self.lib.get_mwpl(trade_date)
        elif key == 'pe_ratio':
            return self.lib.get_pe_ratio(trade_date)
        elif key == 'pe_ratio_idx':
            return self.lib.get_pe_ratio_idx(trade_date)
        elif key == 'india_vix':
            return self.lib.get_india_vix(trade_date)
        elif key == 'nse_security':
            return self.lib.get_security_master(trade_date)
        elif key == 'fii_dii_cash':
            return self.lib.get_fii_dii_cash(trade_date)
        elif key == 'var_stats':
            # For simplicity, fetch BEGIN day only for now, or merge?
            # Importer usually runs once per day. Let's default to BEGIN.
            # Ideally should run both.
            return self.lib.get_var_stats(trade_date, 'BEGIN')
        elif key == 'contract_delta':
            return self.lib.get_contract_delta(trade_date)
        elif key == 'margin_trading':
            return self.lib.get_margin_trading(trade_date)
        elif key == 'corporate_actions':
            return self.lib.get_corporate_actions(trade_date)
        elif key == 'board_meetings':
            return self.lib.get_board_meetings(trade_date)
        elif key == 'historical_index_data':
            return self.lib.get_historical_index_data(trade_date)

        return pd.DataFrame()

    def _deduplicate_mto(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Deduplicate MTO data.
        """
        if df.empty:
            return df

        # Normalize columns just in case
        df.columns = [str(c).strip() for c in df.columns]
        cols = df.columns.tolist()

        sec_col = next((c for c in cols if 'Name of Security' in c), None)
        qty_col = next((c for c in cols if 'Quantity Traded' in c), None)
        deliv_col = next((c for c in cols if 'Deliverable Quantity' in c and '%' not in c), None)

        if not sec_col:
            logger.warning("MTO Deduplication: 'Name of Security' column not found. Skipping deduplication.")
            return df

        agg_dict = {}
        for c in df.columns:
            if c == sec_col:
                continue
            if c in [qty_col, deliv_col] and c is not None:
                agg_dict[c] = 'sum'
            else:
                agg_dict[c] = 'first'

        try:
            df_dedup = df.groupby(sec_col, as_index=False).agg(agg_dict)
            return df_dedup
        except Exception as e:
            logger.error(f"MTO Deduplication failed: {e}")
            return df

    def _is_already_imported(self, db: Session, trade_date: date, key: str, force: bool = False) -> bool:
        """Check if a file type for a date is already successfully imported with data."""
        if force:
            return False

        from sqlalchemy import or_
        exists = db.query(models.ImportLog).filter(
            models.ImportLog.import_date == trade_date,
            models.ImportLog.table_name == key,
            models.ImportLog.status == 'SUCCESS',
            or_(models.ImportLog.rows_inserted > 0, models.ImportLog.rows_updated > 0)
        ).first()
        return exists is not None

    def _deduplicate_records(self, records: List[Dict[str, Any]], unique_fields: List[str]) -> List[Dict[str, Any]]:
        """
        Deduplicate a list of records based on unique_fields.
        Keeps the LAST occurrence.
        """
        if not records or not unique_fields:
            return records

        seen = {}
        duplicates_count = 0

        for record in records:
            # Create a tuple key from the values of unique fields
            key = tuple(record.get(f) for f in unique_fields)

            # If key exists, it will be overwritten by the current (later) record
            # effectively implementing "keep last"
            if key in seen:
                duplicates_count += 1
            seen[key] = record

        deduped_records = list(seen.values())

        if duplicates_count > 0:
            logger.info(f"Deduplicated {duplicates_count} records. Original: {len(records)}, Final: {len(deduped_records)}")

        return deduped_records

    def import_date(self, trade_date: date, patterns: list[str] | None = None,
                   force: bool = False, progress_callback: Callable[[dict[str, Any]], None] | None = None,
                   check_cancel: Callable[[], bool] | None = None, include_non_fo: bool = False, specific_symbol: str | None = None) -> dict[str, Any]:
        """Import all configured files for a given date."""
        if not force and not self.holidays.is_trading_day(trade_date):
            return {
                'status': 'SKIPPED',
                'reason': f'{trade_date} is not a trading day',
                'previous_trading_day': self.holidays.get_previous_trading_day(trade_date).isoformat()
            }

        available_keys = [
            'bhavcopy_eq', 'bhavcopy_fo', 'fao_participant_oi', 'fo_volatility',
            'block_deals', 'bulk_deals', 'fii_derivatives_stats', 'mto', 'mwpl_cli',
            'pe_ratio', 'pe_ratio_idx', 'india_vix', 'var_stats', 'contract_delta', 'margin_trading', 'corporate_actions', 'board_meetings',
            'nse_security', 'fii_dii_cash', 'historical_index_data'
        ]

        patterns_to_run = patterns or available_keys
        patterns_to_run = [p for p in patterns_to_run if p in available_keys]

        total_files = len(patterns_to_run)
        results = {}
        completed_files = []
        failed_files = []

        # We manage the session manually here to allow per-file transaction handling
        db = SessionLocal() if not self._db_session else self._db_session
        should_close = not self._db_session

        try:
            for idx, key in enumerate(patterns_to_run):
                if check_cancel and check_cancel():
                    logger.info("Import aborted by user request.")
                    return {
                        'status': 'ABORTED',
                        'date': trade_date.isoformat(),
                        'files_processed': len(completed_files) + len(failed_files),
                        'successful': len(completed_files),
                        'details': results
                    }

                progress = {
                    'current_file': key,
                    'file_number': idx + 1,
                    'total_files': total_files,
                    'percent': int((idx / total_files) * 100),
                    'status': 'in_progress',
                    'timestamp': datetime.now().isoformat()
                }
                if progress_callback: progress_callback(progress)

                # SKIP CHECK: If not forced, check if already imported successfully
                if self._is_already_imported(db, trade_date, key, force=force):
                    logger.info(f"Skipping {key} for {trade_date} (Already Imported)")
                    results[key] = {'status': 'SKIPPED', 'reason': 'Already Imported'}
                    completed_files.append(key)
                    continue

                logger.info(f"[{idx+1}/{total_files}] Processing {key}...")

                # ISOLATION: Start a nested transaction block (savepoint) for each file
                # If using pure SQLAlchemy session, we can rely on begin_nested()
                try:
                    with db.begin_nested():
                        self._process_file(db, key, trade_date, results, completed_files, force, include_non_fo, specific_symbol)

                    # If we reach here, the nested transaction committed successfully.
                    # We commit the outer transaction periodically or at the end to persist logs.
                    db.commit()

                except Exception as e:
                    logger.exception(f"Error importing {key}: {e}")
                    # If we hit an exception outside of the begin_nested (or it failed to clean up), explicitly rollback to be safe
                    db.rollback()
                    results[key] = {'status': 'ERROR', 'error': str(e)}
                    # Log failure (needs its own transaction to persist even if file failed)
                    try:
                         # We need a new transaction for logging since the previous one rolled back
                        self._log_import(db, trade_date, key, 'FAILED', 0, 0, str(e))
                        db.commit()
                    except:
                        db.rollback()
                        pass
                    failed_files.append(key)

        finally:
            if should_close:
                db.close()

        return {
            'status': 'COMPLETED',
            'date': trade_date.isoformat(),
            'files_processed': total_files,
            'successful': len(completed_files),
            'details': results
        }

    def _process_file(self, db: Session, key: str, trade_date: date, results: dict, completed_files: list, force: bool = False, include_non_fo: bool = False, specific_symbol: str | None = None):
        df = self._fetch_data(key, trade_date)

        if df.empty:
            results[key] = {'status': 'EMPTY_DOWNLOAD', 'rows': 0}
            # If forced (e.g., on a holiday), treat missing files as SUCCESS since NSE might simply not publish them.
            # Otherwise, log as FAILED so it can be retried.
            if force:
                logger.warning(f"File {key} missing on forced import for {trade_date}. Marking as EMPTY_DOWNLOAD.")
                self._log_import(db, trade_date, key, 'SUCCESS', 0, 0, 'Downloaded file was empty or missing (Forced Import)')
                completed_files.append(key)
            else:
                self._log_import(db, trade_date, key, 'FAILED', 0, 0, 'Downloaded file was empty or missing')
            return

        if key == 'mto':
            df = self._deduplicate_mto(df)

        format_info = FieldMapper.detect_format(df)
        if format_info['type'] == 'unknown' and key == 'fii_dii_cash':
            format_info = {'type': 'fii_dii_cash', 'target_table': 'fii_dii_cash'}
        if format_info['type'] == 'unknown':
            # Fallback based on expected file type
            if key == 'mto':
                format_info = {'type': 'mto'}
            elif key == 'bulk_deals' or key == 'block_deals':
                format_info = {'type': 'deals', 'target_table': key}
            elif key == 'fao_participant_oi':
                format_info = {'type': 'participant_oi'}
            elif key == 'bhavcopy_eq':
                # Try to force check if columns seem reasonable even if exact match failed
                if len(df.columns) > 5: # Minimal sanity check
                    format_info = {'type': 'cm_udiff'} # Assume new format
            elif key == 'bhavcopy_fo':
                if len(df.columns) > 5:
                    format_info = {'type': 'fo_udiff'}
            elif key == 'board_meetings':
                format_info = {'type': 'board_meetings'}
            elif key == 'corporate_actions':
                format_info = {'type': 'corporate_actions'}

        if format_info['type'] == 'unknown':
            cols = df.columns.tolist()[:10] # Log first 10 cols
            error_msg = f"Unknown format for {key}. Columns found: {cols}"
            logger.error(error_msg)
            results[key] = {'status': 'UNKNOWN_FORMAT', 'error': error_msg}
            self._log_import(db, trade_date, key, 'FAILED', 0, 0, error_msg)
            return

        if format_info.get('target_table') is None and key in ['bulk_deals', 'block_deals']:
                format_info['target_table'] = key

        # Special override: ind_close_all is used for both pe_ratio_idx and india_vix.
        # FieldMapper defaults to pe_ratio_idx. If the caller specifically requested india_vix, override it.
        # However, if it was identified as 'india_vix_historical' natively, keep that type so it maps correctly.
        if key == 'india_vix' and format_info['type'] != 'india_vix_historical':
            format_info['type'] = 'india_vix'

        # Another override: If the importer requested 'pe_ratio_idx' but FieldMapper natively mapped
        # it to 'historical_index_data' (because the new ind_close_all has OHLCV), we MUST force the
        # format_info back to 'pe_ratio_idx' so that map_to_records generates the correct dict keys
        # (like 'pe', 'pb') that the index_pe_ratio database table expects.
        if key == 'pe_ratio_idx' and format_info['type'] == 'historical_index_data':
            format_info['type'] = 'pe_ratio_idx'

        records = FieldMapper.map_to_records(df, format_info, trade_date)

        if not records:
            results[key] = {'status': 'EMPTY_PARSE', 'rows': 0}
            self._log_import(db, trade_date, key, 'SUCCESS', 0, 0, 'Parsed empty')
            return

        model_class = self._get_model_class(key)
        unique_fields = self._get_unique_fields(key)

        if not model_class:
            results[key] = {'status': 'CONFIG_ERROR'}
            self._log_import(db, trade_date, key, 'FAILED', 0, 0, f'No DB model configured for {key}')
            return

        # INTRA-BATCH DEDUPLICATION
        # Ensure that the records list itself doesn't contain duplicates for unique keys
        # This prevents "ON CONFLICT DO UPDATE command cannot affect row a second time"
        if unique_fields:
            records = self._deduplicate_records(records, unique_fields)

        # Special handling for Deals, Actions, Meetings: Delete & Insert
        if key in ['bulk_deals', 'block_deals']:
            deleted = self._delete_for_date(db, model_class, trade_date)
            inserted = self._insert_batch(db, model_class, records)
            updated = 0
            logger.info(f"{key}: Deleted {deleted} old records, Inserted {inserted} new records.")
        elif key == 'nse_security':
            # Security Master doesn't have a date column and isn't a hypertable. We upsert on fin_instrm_id.
            inserted, updated = self._upsert_batch(db, model_class, records, unique_fields)
        elif key in ['corporate_actions', 'board_meetings']:
            # Corporate Actions and Board Meetings don't have a unique constraint on date, symbol, purpose
            # so we must delete and insert them for the date.
            deleted = self._delete_for_date(db, model_class, trade_date)
            inserted = self._insert_batch(db, model_class, records)
            updated = 0
            logger.info(f"{key}: Deleted {deleted} old records, Inserted {inserted} new records.")
        else:
            inserted, updated = self._upsert_batch(db, model_class, records, unique_fields)

        # Legacy Sync
        if key == 'bhavcopy_eq':
            self._upsert_legacy_bhavcopy(db, records, 'CM')
        elif key == 'bhavcopy_fo':
            self._upsert_legacy_bhavcopy(db, records, 'FO')

        results[key] = {'status': 'SUCCESS', 'rows_processed': inserted + updated}
        self._log_import(db, trade_date, key, 'SUCCESS', inserted, updated)
        completed_files.append(key)

    def _insert_batch(self, db: Session, model_class, records: list[dict[str, Any]], batch_size: int = 1000) -> int:
        if not records: return 0
        total_inserted = 0
        try:
            table = model_class.__table__
            valid_cols = set(c.name for c in table.columns)
            cleaned = [{k: v for k, v in r.items() if k in valid_cols} for r in records]

            # Simple Insert in chunks. Use ON CONFLICT DO NOTHING to handle edge cases
            # where delete_for_date might not have caught unique constraint overlaps from
            # a different date insertion process.
            for i in range(0, len(cleaned), batch_size):
                chunk = cleaned[i:i + batch_size]
                stmt = pg_insert(table).values(chunk)
                stmt = stmt.on_conflict_do_nothing()
                result = db.execute(stmt)
                total_inserted += result.rowcount
            return total_inserted
        except Exception as e:
            logger.error(f"Insert failed: {e}")
            raise

    def _delete_for_date(self, db: Session, model_class, trade_date: date) -> int:
        try:
            stmt = delete(model_class).where(model_class.date == trade_date)
            result = db.execute(stmt)
            return result.rowcount
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            raise

    def _upsert_batch(self, db: Session, model_class, records: list[dict[str, Any]],
                     unique_fields: list[str], batch_size: int = 1000) -> tuple[int, int]:
        if not records: return 0, 0
        total_processed = 0
        try:
            table = model_class.__table__
            valid_cols = set(c.name for c in table.columns)
            cleaned = [{k: v for k, v in r.items() if k in valid_cols} for r in records]

            # Upsert in chunks to avoid massive SQL statements that bog down Postgres
            for i in range(0, len(cleaned), batch_size):
                chunk = cleaned[i:i + batch_size]
                stmt = pg_insert(table).values(chunk)
                update_cols = {c.name: c for c in stmt.excluded
                              if c.name not in unique_fields and c.name not in ['id', 'created_at']}

                if unique_fields:
                    if update_cols:
                        stmt = stmt.on_conflict_do_update(index_elements=unique_fields, set_=update_cols)
                    else:
                        stmt = stmt.on_conflict_do_nothing(index_elements=unique_fields)
                else:
                    # Fallback to simple insert if no unique fields (shouldn't happen for upsert path)
                    pass

                result = db.execute(stmt)
                total_processed += result.rowcount

            return total_processed, 0
        except Exception as e:
            logger.error(f"Upsert failed: {e}")
            raise

    def _log_import(self, db: Session, import_date: date, table_name: str,
                   status: str, rows_inserted: int, rows_updated: int = 0,
                   error_msg: str | None = None):
        log = models.ImportLog(
            import_date=import_date, table_name=table_name, status=status,
            rows_inserted=rows_inserted, rows_updated=rows_updated, error_msg=error_msg
        )
        db.add(log)

        level = "ERROR" if status in ["FAILED", "ERROR"] else "INFO"
        msg = f"NSE Import: {table_name} for {import_date} - {status} | Rows: {rows_inserted + rows_updated}"
        if error_msg: msg += f" | Error: {error_msg}"

        sys_log = SystemLog(
            timestamp=datetime.now(), level=level, source="NSE_Importer",
            event_type="Data_Import", message=msg,
            meta_data={"rows": rows_inserted + rows_updated, "table": table_name}
        )
        db.add(sys_log)

    def _upsert_legacy_bhavcopy(self, db: Session, records: list[dict[str, Any]], segment: str, batch_size: int = 1000):
        if not records: return
        try:
            legacy_records = []
            for r in records:
                lr = {
                    'trade_date': r['trade_date'],
                    'segment': segment,
                    'symbol': r.get('symbol') or r.get('ticker_symb'),
                    'instrument_type': r.get('instrument_type', 'EQ' if segment == 'CM' else 'XX'),
                    'open': r.get('open_price'), 'high': r.get('high_price'),
                    'low': r.get('low_price'), 'close': r.get('close_price'),
                    'last': r.get('last_price'), 'prev_close': r.get('prev_close'),
                    'settlement_price': r.get('settle_price'),
                    'total_traded_qty': r.get('total_traded_qty') or r.get('total_trading_vol'),
                    'total_traded_val': r.get('turnover_lacs') or r.get('total_trf_val'),
                    'total_trades': r.get('no_of_trades'),
                    'open_interest': r.get('open_interest'),
                    'change_in_oi': r.get('change_in_oi'),
                    'series': r.get('series'),
                    'deliverable_qty': r.get('deliverable_qty'),
                    'deliverable_pct': r.get('deliverable_pct'),
                    'expiry_date': r.get('expiry_date'),
                    'strike_price': r.get('strike_price'),
                    'option_type': r.get('option_type'),
                    'instrument_name': r.get('instrument_name'),
                }
                legacy_records.append(lr)

            trade_date = records[0]['trade_date']
            db.query(Bhavcopy).filter(Bhavcopy.trade_date == trade_date, Bhavcopy.segment == segment).delete(synchronize_session=False)

            # Chunk the legacy insert as well
            for i in range(0, len(legacy_records), batch_size):
                chunk = legacy_records[i:i + batch_size]
                db.bulk_insert_mappings(Bhavcopy, chunk)

        except Exception as e:
            logger.error(f"Legacy sync failed: {e}")

    def setup_timescale(self) -> dict[str, Any]:
        with self.get_db() as db:
            return setup_all_timescale_policies(db)

    def get_import_stats(self, start_date: date | None = None, end_date: date | None = None) -> dict[str, Any]:
        from backend.ingest.queries import get_import_stats as query_stats
        with self.get_db() as db:
            return query_stats(db, start_date, end_date)
