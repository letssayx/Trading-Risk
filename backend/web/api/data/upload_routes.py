"""
Enhanced upload endpoints for both CM and FO segments
"""
import os
import zipfile
import tempfile
import pandas as pd
import hashlib
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query, Form
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
import json

from backend.infrastructure.db import get_db
from backend.domain.market.models import Bhavcopy, ImportHistory
from backend.ingest.nse_importer import NSEDataImporter
from backend.ingest.field_mapper import FieldMapper
from backend.ingest import nse_models as models

router = APIRouter()

# Allowed series and segments
ALLOWED_SERIES = ['EQ', 'BE', 'GB', 'IV', 'SM']  # Expanded for CM
ALLOWED_SEGMENTS = ['CM', 'FO']

# Instrument type mappings
INSTRUMENT_TYPES = {
    'CM': ['STK', 'ETF', 'IDX'],
    'FO': ['FUTSTK', 'OPTSTK', 'FUTIDX', 'OPTIDX', 'STO', 'STF', 'IDO', 'IDF']
}

class ImportPreviewRequest(BaseModel):
    file_date: Optional[str] = None
    overwrite_existing: bool = False

class ImportConfirmRequest(BaseModel):
    file_date: str
    overwrite_existing: bool = False
    segments: List[str] = ['CM', 'FO']

def calculate_file_checksum(file_path: str) -> str:
    """Calculate MD5 checksum of file"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def parse_udiff_date(date_str) -> Optional[date]:
    """Parse UDIFF date. Prioritize DD-MM-YYYY then DD-MMM-YYYY"""
    if pd.isna(date_str) or str(date_str).strip().lower() in ['nan', 'null', 'none', '']:
        return None

    if isinstance(date_str, (datetime, date)):
        return date_str if isinstance(date_str, date) else date_str.date()

    s = str(date_str).strip()

    # Try DD-MM-YYYY (User requested)
    try:
        return datetime.strptime(s, "%d-%m-%Y").date()
    except ValueError:
        pass

    # Try DD-MMM-YYYY (Standard UDIFF)
    try:
        return datetime.strptime(s, "%d-%b-%Y").date()
    except ValueError:
        pass

    return None

def validate_headers(headers: List[str]) -> bool:
    """Check if CSV has required UDIFF headers"""
    required = ['TradDt', 'Sgmt', 'FinInstrmTp', 'TckrSymb']
    return all(req in headers for req in required)

def parse_bhavcopy_df(df: pd.DataFrame) -> pd.DataFrame:
    """Parse and clean dataframe with proper types"""
    # Parse dates
    df['parsed_trade_date'] = df['TradDt'].apply(parse_udiff_date)

    if 'BizDt' in df.columns:
        df['parsed_biz_date'] = df['BizDt'].apply(parse_udiff_date)

    if 'XpryDt' in df.columns:
        df['parsed_expiry_date'] = df['XpryDt'].apply(parse_udiff_date)

    if 'FininstrmActlXpryDt' in df.columns:
        df['parsed_actl_expiry_date'] = df['FininstrmActlXpryDt'].apply(parse_udiff_date)

    # Convert numeric fields
    numeric_fields = ['OpnPric', 'HghPric', 'LwPric', 'ClsPric', 'LastPric',
                      'PrvsClsgPric', 'SttlmPric', 'StrkPric', 'UndrlygPric',
                      'TtlTradgVol', 'TtlTrfVal', 'TtlNbOfTxsExctd',
                      'OpnIntrst', 'ChngInOpnIntrst', 'NewBrdLotQty']

    for field in numeric_fields:
        if field in df.columns:
            df[field] = pd.to_numeric(df[field], errors='coerce')

    return df

def check_existing_import(db: Session, file_name: str, file_date: date) -> Optional[ImportHistory]:
    return db.query(ImportHistory).filter(
        ImportHistory.file_name == file_name,
        ImportHistory.file_date == file_date
    ).first()

@router.post("/api/data/upload/bhavcopy/preview")
async def preview_bhavcopy(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith('.zip'):
        raise HTTPException(400, "Please upload a ZIP file")

    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name

    csv_path = None
    try:
        checksum = calculate_file_checksum(tmp_path)
        with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
            csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
            if not csv_files:
                raise HTTPException(400, "No CSV found in ZIP")
            csv_path = zip_ref.extract(csv_files[0], tempfile.gettempdir())

        df = pd.read_csv(csv_path)
        if not validate_headers(df.columns.tolist()):
            raise HTTPException(400, f"Invalid CSV format. Expected UDIFF headers.")

        df = parse_bhavcopy_df(df)

        file_date = None
        if len(df) > 0:
            file_date = df['parsed_trade_date'].iloc[0]

        existing_dates = []
        if file_date:
            existing = db.query(Bhavcopy).filter(Bhavcopy.trade_date == file_date).first()
            if existing: existing_dates = [file_date]

        existing_import = check_existing_import(db, file.filename, file_date) if file_date else None

        stats = {}
        preview_by_segment = {}

        for segment in ALLOWED_SEGMENTS:
            segment_df = df[df['Sgmt'] == segment]

            # Simple Filter: Just use segment. UDIFF is standard.

            stats[segment] = {
                'total_rows': len(segment_df),
                'unique_symbols': segment_df['TckrSymb'].nunique() if len(segment_df) > 0 else 0,
                'instrument_types': segment_df['FinInstrmTp'].value_counts().to_dict() if len(segment_df) > 0 else {}
            }

            preview = []
            for _, row in segment_df.head(5).iterrows():
                preview_row = {
                    'symbol': row['TckrSymb'],
                    'instrument_type': row['FinInstrmTp'],
                    'open': float(row['OpnPric']) if pd.notna(row['OpnPric']) else 0,
                    'high': float(row['HghPric']) if pd.notna(row['HghPric']) else 0,
                    'low': float(row['LwPric']) if pd.notna(row['LwPric']) else 0,
                    'close': float(row['ClsPric']) if pd.notna(row['ClsPric']) else 0,
                }
                if segment == 'FO':
                    expiry = row.get('parsed_expiry_date')
                    preview_row.update({
                        'expiry': expiry.strftime("%Y-%m-%d") if pd.notna(expiry) else None,
                        'strike': float(row['StrkPric']) if pd.notna(row.get('StrkPric')) else None,
                        'option_type': row.get('OptnTp'),
                        'open_interest': int(row['OpnIntrst']) if pd.notna(row.get('OpnIntrst')) else 0
                    })
                else:
                    preview_row.update({
                        'series': row.get('SctySrs'),
                        'volume': int(row['TtlTradgVol']) if pd.notna(row.get('TtlTradgVol')) else 0
                    })
                preview.append(preview_row)
            preview_by_segment[segment] = preview

        return {
            'success': True,
            'filename': file.filename,
            'file_date': file_date.strftime("%d-%m-%Y") if file_date else None,
            'checksum': checksum,
            'total_rows': len(df),
            'stats': stats,
            'preview': preview_by_segment,
            'warnings': {
                'date_exists': len(existing_dates) > 0,
                'existing_dates': [d.strftime("%Y-%m-%d") for d in existing_dates],
                'already_imported': existing_import is not None,
                'previous_import_date': existing_import.import_date.strftime("%Y-%m-%d") if existing_import else None
            }
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Error processing file: {str(e)}")
    finally:
        if os.path.exists(tmp_path): os.unlink(tmp_path)
        if csv_path and os.path.exists(csv_path): os.unlink(csv_path)

@router.post("/api/data/upload/generic")
async def upload_generic_file(
    file: UploadFile = File(...),
    file_type: str = Form(..., description="Type key from NSE_FILE_PATTERNS (e.g. fao_participant_oi)"),
    file_date: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Generic upload handler for all NSE file types supported by the importer.
    """
    content = await file.read()

    # Initialize Importer
    importer = NSEDataImporter(db_session=db)

    # 1. Parse Date from Input or Filename or Content?
    # Importer usually expects date to be known from filename URL pattern in auto-mode.
    # Here manual upload, we rely on user input OR filename parsing if possible.
    # But for parsing content, we just need the content.

    import_date = None
    if file_date:
        try:
            import_date = datetime.strptime(file_date, "%Y-%m-%d").date()
        except:
            pass

    if not import_date:
        # Try to infer from filename if possible?
        # e.g. fao_participant_oi_06022026.csv
        # This is tricky without strict pattern matching.
        # User MUST provide date if filename is random.
        # For now, require date if not deducible.
        pass

    # 2. Parse Content
    try:
        df = importer._parse_content(content, file_type)
        if df is None or df.empty:
             raise HTTPException(400, "Parsed file is empty or invalid format.")

        # 3. Detect Format (Optional double check)
        format_info = FieldMapper.detect_format(df)
        # If unknown, force it if we trust file_type?
        if format_info['type'] == 'unknown':
            # Map file_type to format_type manually if needed
            # FieldMapper needs an update to support forced types?
            # Actually map_to_records uses format_info['type'].
            # We can construct a fake format_info based on file_type.
            mapping = {
                'fao_participant_oi': 'participant_oi',
                'fii_stats': 'fii_stats',
                'fo_volatility': 'volatility',
                'mto': 'mto',
                'mwpl_cli': 'mwpl',
                'pe_ratio': 'pe_ratio',
                'var_begin': 'var_stats',
                'var_end': 'var_stats',
                'contract_delta': 'contract_delta',
                'margin_trading': 'margin_trading',
                'bulk_deals': 'deals',
                'block_deals': 'deals',
            }
            mapped_type = mapping.get(file_type)
            if mapped_type:
                format_info = {'type': mapped_type, 'name': file_type}
                if file_type in ['bulk_deals', 'block_deals']:
                    format_info['target_table'] = file_type
            else:
                 raise HTTPException(400, f"Could not auto-detect format for {file_type}")

        # 4. Map Records
        # We need a trade_date for mapping.
        if not import_date:
            # Try to get from DF if column exists
            # Some mappers look for date column.
            # But FieldMapper map_to_records takes trade_date as arg.
            # If DF has date, it uses it. If not, it uses arg.
            # If arg is None and DF has no date, it fails or sets None.
            # We should require date from user.
            if not import_date:
                 # Last resort: today? No.
                 raise HTTPException(400, "Date is required.")

        records = FieldMapper.map_to_records(df, format_info, import_date)

        if not records:
             raise HTTPException(400, "No valid records found after mapping.")

        # 5. Upsert
        model_class = importer._get_model_class(file_type)
        unique_fields = importer._get_unique_fields(file_type)

        if not model_class:
            raise HTTPException(400, f"No model configured for {file_type}")

        inserted, updated = importer._upsert_batch(db, model_class, records, unique_fields)

        # Dual write for legacy if needed
        if file_type == 'sec_bhavdata':
            importer._upsert_legacy_bhavcopy(db, records, 'CM')
        elif file_type == 'fno_bhav':
            importer._upsert_legacy_bhavcopy(db, records, 'FO')

        # Log
        importer._log_import(db, import_date, file_type, 'SUCCESS', inserted, updated, f"Manual Upload: {file.filename}")
        db.commit()

        return {
            "success": True,
            "rows_processed": inserted + updated,
            "date": import_date.isoformat(),
            "type": file_type
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Upload failed: {str(e)}")

@router.post("/api/data/upload/bhavcopy/import")
async def import_bhavcopy(
    file: UploadFile = File(...),
    file_date: str = Form(...),
    overwrite_existing: bool = Form(...),
    segments: str = Form(...),
    db: Session = Depends(get_db)
):
    segments_list = json.loads(segments)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name

    csv_path = None
    try:
        with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
            csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
            csv_path = zip_ref.extract(csv_files[0], tempfile.gettempdir())

        df = pd.read_csv(csv_path)
        df = parse_bhavcopy_df(df)

        # Robust Date Parsing for Form Input
        parsed_file_date = None
        if file_date and file_date.lower() not in ['null', 'none', '']:
            try:
                parsed_file_date = datetime.strptime(file_date, "%d-%m-%Y").date()
            except ValueError:
                try:
                    parsed_file_date = datetime.strptime(file_date, "%Y-%m-%d").date()
                except:
                    pass

        if not parsed_file_date:
             if 'parsed_trade_date' in df.columns and len(df) > 0 and pd.notna(df['parsed_trade_date'].iloc[0]):
                 parsed_file_date = df['parsed_trade_date'].iloc[0]
             else:
                 raise HTTPException(400, "Could not determine date from file or input.")

        if overwrite_existing:
            def delete_existing():
                db.query(Bhavcopy).filter(
                    Bhavcopy.trade_date == parsed_file_date,
                    Bhavcopy.segment.in_(segments_list)
                ).delete(synchronize_session=False)
                db.commit()
            from fastapi.concurrency import run_in_threadpool
            await run_in_threadpool(delete_existing)

        objects = []
        errors = []

        for _, row in df.iterrows():
            if row['Sgmt'] not in segments_list:
                continue

            try:
                bhavcopy = Bhavcopy(
                    # Core
                    trade_date=row['parsed_trade_date'],
                    segment=row['Sgmt'],
                    instrument_type=row['FinInstrmTp'],
                    symbol=row['TckrSymb'],

                    # Additional
                    biz_date=row.get('parsed_biz_date'),
                    source=row.get('Src'),
                    fin_instrm_id=str(row.get('FinInstrmId', '')),
                    isin=row.get('ISIN'),
                    instrument_name=row.get('FinInstrmNm'),
                    session_id=row.get('SsnId'),
                    remarks=row.get('Rmks'),
                    lot_size=int(row['NewBrdLotQty']) if pd.notna(row.get('NewBrdLotQty')) else None,

                    # CM
                    series=row.get('SctySrs'),

                    # FO
                    expiry_date=row.get('parsed_expiry_date'),
                    actual_expiry_date=row.get('parsed_actl_expiry_date'),
                    strike_price=float(row['StrkPric']) if pd.notna(row.get('StrkPric')) else None,
                    option_type=row.get('OptnTp'),
                    underlying_price=float(row['UndrlygPric']) if pd.notna(row.get('UndrlygPric')) else None,

                    # Prices
                    open=float(row['OpnPric']) if pd.notna(row.get('OpnPric')) else None,
                    high=float(row['HghPric']) if pd.notna(row.get('HghPric')) else None,
                    low=float(row['LwPric']) if pd.notna(row.get('LwPric')) else None,
                    close=float(row['ClsPric']) if pd.notna(row.get('ClsPric')) else None,
                    last=float(row['LastPric']) if pd.notna(row.get('LastPric')) else None,
                    prev_close=float(row['PrvsClsgPric']) if pd.notna(row.get('PrvsClsgPric')) else None,
                    settlement_price=float(row['SttlmPric']) if pd.notna(row.get('SttlmPric')) else None,

                    # Volume
                    total_traded_qty=int(row['TtlTradgVol']) if pd.notna(row.get('TtlTradgVol')) else None,
                    total_traded_val=float(row['TtlTrfVal']) if pd.notna(row.get('TtlTrfVal')) else None,
                    total_trades=int(row['TtlNbOfTxsExctd']) if pd.notna(row.get('TtlNbOfTxsExctd')) else None,
                    open_interest=int(row['OpnIntrst']) if pd.notna(row.get('OpnIntrst')) else None,
                    change_in_oi=int(row['ChngInOpnIntrst']) if pd.notna(row.get('ChngInOpnIntrst')) else None
                )
                objects.append(bhavcopy)
            except Exception as e:
                errors.append(f"Row error: {str(e)}")

        if objects:
            def save_objects():
                try:
                    db.bulk_save_objects(objects)
                    db.commit()
                except Exception as e:
                    db.rollback()
                    raise HTTPException(500, f"DB Error: {str(e)}")
            await run_in_threadpool(save_objects)

        # History
        try:
            hist = ImportHistory(
                file_name=file.filename,
                file_date=parsed_file_date,
                segment=','.join(segments_list),
                rows_imported=len(objects),
                import_date=datetime.now().date()
            )
            db.add(hist)
            db.commit()
        except:
            db.rollback()

        return {
            'success': True,
            'inserted': len(objects),
            'skipped': 0,
            'errors': errors[:10],
            'date': parsed_file_date.strftime("%d-%m-%Y")
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Import failed: {str(e)}")
    finally:
        if os.path.exists(tmp_path): os.unlink(tmp_path)
        if csv_path and os.path.exists(csv_path): os.unlink(csv_path)
