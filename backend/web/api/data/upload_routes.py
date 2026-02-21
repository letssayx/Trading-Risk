from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query, Form
import os
import zipfile
import tempfile
import pandas as pd
import hashlib
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
import json
import logging
import traceback

from backend.infrastructure.db import get_db
from backend.domain.market.models import Bhavcopy, ImportHistory

logger = logging.getLogger(__name__)

router = APIRouter()

# Allowed series and segments
ALLOWED_SERIES = ['EQ', 'BE']  # For CM segment
ALLOWED_SEGMENTS = ['CM', 'FO']  # Both segments

# Instrument type mappings
INSTRUMENT_TYPES = {
    'CM': ['STK'],  # Only stocks in CM
    'FO': ['FUTSTK', 'OPTSTK', 'FUTIDX', 'OPTIDX', 'STO', 'STF', 'IDO', 'IDF']  # All FO instruments
}

class ImportPreviewRequest(BaseModel):
    file_date: Optional[str] = None
    overwrite_existing: bool = False

class ImportConfirmRequest(BaseModel):
    file_date: str
    overwrite_existing: bool = False
    segments: List[str] = ['CM', 'FO']  # Which segments to import

def calculate_file_checksum(file_path: str) -> str:
    """Calculate MD5 checksum of file"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def parse_udiff_date(date_str) -> Optional[date]:
    """Parse UDIFF date format (DD-MMM-YYYY) or YYYYMMDD"""
    if pd.isna(date_str) or str(date_str).lower() == 'null' or str(date_str).strip() == '':
        return None
    if isinstance(date_str, datetime):
        return date_str.date()
    if isinstance(date_str, date):
        return date_str

    s = str(date_str).strip()
    # Try DD-MMM-YYYY
    try:
        return datetime.strptime(s, "%d-%b-%Y").date()
    except:
        pass

    # Try YYYYMMDD
    try:
        return datetime.strptime(s, "%Y%m%d").date()
    except:
        pass

    # Try YYYY-MM-DD
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except:
        pass

    # Try DD-MM-YYYY (e.g., 18-02-2026)
    try:
        return datetime.strptime(s, "%d-%m-%Y").date()
    except:
        pass

    return None

def validate_headers(headers: List[str], expected_segment: str = 'BOTH') -> bool:
    """Check if CSV has required UDIFF headers based on segment"""
    # Common headers
    required = ['TradDt', 'TckrSymb'] # Minimal set

    # If Sgmt column exists, it's better, but some files might not have it if they are purely one type?
    # Actually UDIFF spec usually has Sgmt.
    if 'Sgmt' not in headers:
         # If strict UDIFF, this is fail. But maybe we can relax.
         pass

    return all(req in headers for req in required)

def parse_bhavcopy_df(df: pd.DataFrame) -> pd.DataFrame:
    """Parse and clean dataframe with proper types"""
    # Parse dates
    if 'TradDt' in df.columns:
        df['parsed_trade_date'] = df['TradDt'].apply(parse_udiff_date)

    if 'BizDt' in df.columns:
        df['parsed_business_date'] = df['BizDt'].apply(parse_udiff_date)

    if 'XpryDt' in df.columns:
        df['parsed_expiry_date'] = df['XpryDt'].apply(parse_udiff_date)
    else:
        df['parsed_expiry_date'] = None

    # Convert numeric fields
    numeric_fields = ['OpnPric', 'HghPric', 'LwPric', 'ClsPric', 'LastPric',
                      'PrvsClsgPric', 'SttlmPric', 'StrkPric', 'UndrlygPric',
                      'TtlTradgVol', 'TtlTrfVal', 'TtlNbOfTxsExctd',
                      'OpnIntrst', 'ChngInOpnIntrst']

    for field in numeric_fields:
        if field in df.columns:
            df[field] = pd.to_numeric(df[field], errors='coerce')

    return df

def get_existing_dates(db: Session, segments: List[str]) -> List[datetime.date]:
    """Get all dates that already have data for given segments"""
    result = db.query(Bhavcopy.trade_date).filter(
        Bhavcopy.segment.in_(segments)
    ).distinct().all()
    return [r[0] for r in result]

def check_existing_import(db: Session, file_name: str, file_date: date) -> Optional[ImportHistory]:
    """Check if this file has been imported before"""
    return db.query(ImportHistory).filter(
        ImportHistory.file_name == file_name,
        ImportHistory.file_date == file_date
    ).first()

@router.post("/api/data/upload/bhavcopy/preview")
async def preview_bhavcopy(
    file: UploadFile = File(...),
    file_segment_type: str = Form("BOTH"), # CM, FO, or BOTH
    db: Session = Depends(get_db)
):
    """
    Upload and preview bhavcopy ZIP file
    """
    if not file.filename.endswith('.zip'):
        raise HTTPException(400, "Please upload a ZIP file")

    # Save temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name

    csv_path = None
    try:
        # Calculate checksum
        checksum = calculate_file_checksum(tmp_path)

        # Extract ZIP
        with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
            csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
            if not csv_files:
                raise HTTPException(400, "No CSV found in ZIP")

            csv_path = zip_ref.extract(csv_files[0], tempfile.gettempdir())

        # Read CSV
        df = pd.read_csv(csv_path)

        # Validate headers
        if not validate_headers(df.columns.tolist(), file_segment_type):
            raise HTTPException(400, f"Invalid CSV format. Missing required columns.")

        # Parse data
        df = parse_bhavcopy_df(df)

        # Get file date
        file_date = None
        if len(df) > 0 and 'parsed_trade_date' in df.columns:
            file_date = df['parsed_trade_date'].iloc[0]

        # Check existing date
        existing_dates = []
        if file_date:
            existing = db.query(Bhavcopy).filter(
                Bhavcopy.trade_date == file_date
            ).first()
            if existing:
                existing_dates = [file_date]

        existing_import = None
        if file_date:
            existing_import = check_existing_import(db, file.filename, file_date)

        # Prepare stats
        stats = {}
        preview_by_segment = {}

        segments_to_process = []
        if file_segment_type == 'BOTH':
            segments_to_process = ['CM', 'FO']
        else:
            segments_to_process = [file_segment_type]

        for segment in segments_to_process:
            # Filter by segment if column exists
            if 'Sgmt' in df.columns:
                segment_df = df[df['Sgmt'] == segment]
            else:
                # If no Sgmt column, assume the whole file is the requested segment
                segment_df = df

            if segment == 'CM':
                if 'FinInstrmTp' in segment_df.columns:
                    segment_df = segment_df[segment_df['FinInstrmTp'] == 'STK']
                if 'SctySrs' in segment_df.columns:
                    segment_df = segment_df[segment_df['SctySrs'].isin(ALLOWED_SERIES)]
            elif segment == 'FO':
                if 'FinInstrmTp' in segment_df.columns:
                    segment_df = segment_df[segment_df['FinInstrmTp'].isin(INSTRUMENT_TYPES['FO'])]

            stats[segment] = {
                'total_rows': len(segment_df),
                'unique_symbols': segment_df['TckrSymb'].nunique() if len(segment_df) > 0 and 'TckrSymb' in segment_df.columns else 0,
                'instrument_types': segment_df['FinInstrmTp'].value_counts().to_dict() if len(segment_df) > 0 and 'FinInstrmTp' in segment_df.columns else {}
            }

            # Get preview
            preview = []
            for _, row in segment_df.head(5).iterrows():
                preview_row = {
                    'symbol': row.get('TckrSymb', ''),
                    'instrument_type': row.get('FinInstrmTp', ''),
                    'open': float(row['OpnPric']) if 'OpnPric' in row and pd.notna(row['OpnPric']) else 0,
                    'high': float(row['HghPric']) if 'HghPric' in row and pd.notna(row['HghPric']) else 0,
                    'low': float(row['LwPric']) if 'LwPric' in row and pd.notna(row['LwPric']) else 0,
                    'close': float(row['ClsPric']) if 'ClsPric' in row and pd.notna(row['ClsPric']) else 0,
                }

                if segment == 'FO':
                    expiry = row.get('parsed_expiry_date')
                    preview_row.update({
                        'expiry': expiry.strftime("%Y-%m-%d") if pd.notna(expiry) else None,
                        'strike': float(row['StrkPric']) if 'StrkPric' in row and pd.notna(row['StrkPric']) else None,
                        'option_type': row.get('OptnTp') if pd.notna(row.get('OptnTp')) else 'XX',
                        'open_interest': int(row['OpnIntrst']) if 'OpnIntrst' in row and pd.notna(row['OpnIntrst']) else 0
                    })
                else:
                    preview_row.update({
                        'series': row.get('SctySrs', ''),
                        'volume': int(row['TtlTradgVol']) if 'TtlTradgVol' in row and pd.notna(row['TtlTradgVol']) else 0
                    })

                preview.append(preview_row)

            preview_by_segment[segment] = preview

        return {
            'success': True,
            'filename': file.filename,
            'file_date': file_date.strftime("%Y-%m-%d") if file_date else None,
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

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Preview Error: {e}")
        traceback.print_exc()
        raise HTTPException(500, f"Error processing file: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        if csv_path and os.path.exists(csv_path):
            os.unlink(csv_path)

@router.post("/api/data/upload/bhavcopy/import")
async def import_bhavcopy(
    file: UploadFile = File(...),
    file_date: Optional[str] = Form(None),
    overwrite_existing: bool = Form(False),
    segments: str = Form(...), # JSON string
    mode: str = Form("daily"), # daily or historical
    db: Session = Depends(get_db)
):
    """
    Import bhavcopy data with overwrite option. Supports Historical Backfill (multiple files).
    """
    segments_list = json.loads(segments)

    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name

    extracted_files = []
    total_inserted = 0
    total_errors = []
    total_skipped = 0
    skipped_reasons = {}

    def log_skip(reason):
        nonlocal total_skipped
        total_skipped += 1
        key = reason[:50] # truncated key
        skipped_reasons[key] = skipped_reasons.get(key, 0) + 1

    try:
        # Extract all CSVs if historical, or just the first if daily
        with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
            all_csvs = [f for f in zip_ref.namelist() if f.endswith('.csv')]

            if mode == 'historical':
                # Process all files
                for f in all_csvs:
                    extracted_path = zip_ref.extract(f, tempfile.gettempdir())
                    extracted_files.append(extracted_path)
            else:
                # Process first file
                if all_csvs:
                    extracted_path = zip_ref.extract(all_csvs[0], tempfile.gettempdir())
                    extracted_files.append(extracted_path)

        if not extracted_files:
            raise HTTPException(400, "No CSV files found in ZIP")

        # Process each file
        for csv_path in extracted_files:
            try:
                df = pd.read_csv(csv_path)
            except Exception as e:
                total_errors.append(f"Failed to read CSV {os.path.basename(csv_path)}: {str(e)}")
                continue

            # Relaxed column check
            # required_cols = ['TradDt', 'Sgmt', 'FinInstrmTp']
            # missing_cols = [c for c in required_cols if c not in df.columns]
            # if missing_cols:
            #     total_errors.append(f"Skipped {os.path.basename(csv_path)}: Missing columns {missing_cols}")
            #     continue

            df = parse_bhavcopy_df(df)

            # Determine date for THIS file
            parsed_file_date = None

            # 1. Try from input if single file
            if len(extracted_files) == 1 and file_date and file_date.lower() != 'null' and file_date.strip() != '':
                try:
                    parsed_file_date = datetime.strptime(file_date, "%Y-%m-%d").date()
                except ValueError:
                    pass

            # 2. Try from content (Most reliable for historical bulk)
            if not parsed_file_date:
                if len(df) > 0 and 'parsed_trade_date' in df.columns:
                    valid_dates = df['parsed_trade_date'].dropna()
                    if not valid_dates.empty:
                        parsed_file_date = valid_dates.iloc[0]

            # 3. Try from filename
            if not parsed_file_date:
                import re
                filename = os.path.basename(csv_path)
                match = re.search(r'(\d{8})|(\d{2}-[A-Za-z]{3}-\d{4})', filename)
                if match:
                    d_str = match.group(0)
                    parsed_file_date = parse_udiff_date(d_str)

            if not parsed_file_date:
                total_errors.append(f"Skipped {os.path.basename(csv_path)}: Could not determine date.")
                continue

            # Overwrite logic
            if overwrite_existing:
                db.query(Bhavcopy).filter(
                    Bhavcopy.trade_date == parsed_file_date,
                    Bhavcopy.segment.in_(segments_list)
                ).delete(synchronize_session=False)
                db.commit()

            # Insert objects
            objects = []
            for _, row in df.iterrows():
                # Determine segment if Sgmt column missing
                segment = row.get('Sgmt')

                # If segment missing, try to infer or assume based on user selection
                if not segment:
                    # Heuristic: if has option fields, FO, else CM?
                    # Or rely on what user said passed in 'segments_list' if it's single choice
                    if len(segments_list) == 1:
                        segment = segments_list[0]
                    else:
                        # Ambiguous
                        log_skip("Missing Sgmt column")
                        continue

                # Skip if segment not requested
                if segment not in segments_list:
                    # log_skip(f"Segment {segment} excluded")
                    continue

                # Apply filtering based on segment
                if segment == 'CM':
                    if 'FinInstrmTp' in row and row['FinInstrmTp'] != 'STK':
                        log_skip(f"CM Filter: {row['FinInstrmTp']}")
                        continue
                    if 'SctySrs' in row and row['SctySrs'] not in ALLOWED_SERIES:
                        log_skip(f"CM Series: {row['SctySrs']}")
                        continue
                elif segment == 'FO':
                    # robust check with strip
                    inst_type = str(row.get('FinInstrmTp', '')).strip()
                    if inst_type not in INSTRUMENT_TYPES['FO']:
                        log_skip(f"FO Filter: {inst_type}")
                        continue

                try:
                    bhavcopy = Bhavcopy(
                        trade_date=row.get('parsed_trade_date') or parsed_file_date,
                        segment=segment,
                        instrument_type=row.get('FinInstrmTp'),
                        symbol=row.get('TckrSymb'),

                        # Common fields
                        series=row.get('SctySrs'),
                        isin=row.get('ISIN'),

                        # FO specific
                        expiry_date=row.get('parsed_expiry_date'),
                        strike_price=float(row['StrkPric']) if 'StrkPric' in row and pd.notna(row['StrkPric']) else None,
                        option_type=row.get('OptnTp') if 'OptnTp' in row and pd.notna(row['OptnTp']) else None,
                        underlying=row.get('UndrlygPric') if 'UndrlygPric' in row else None,

                        # Prices
                        open=float(row['OpnPric']) if 'OpnPric' in row and pd.notna(row['OpnPric']) else None,
                        high=float(row['HghPric']) if 'HghPric' in row and pd.notna(row['HghPric']) else None,
                        low=float(row['LwPric']) if 'LwPric' in row and pd.notna(row['LwPric']) else None,
                        close=float(row['ClsPric']) if 'ClsPric' in row and pd.notna(row['ClsPric']) else None,
                        last=float(row['LastPric']) if 'LastPric' in row and pd.notna(row['LastPric']) else None,
                        prev_close=float(row['PrvsClsgPric']) if 'PrvsClsgPric' in row and pd.notna(row['PrvsClsgPric']) else None,
                        settlement_price=float(row['SttlmPric']) if 'SttlmPric' in row and pd.notna(row['SttlmPric']) else None,

                        # Volume & OI
                        total_traded_qty=int(row['TtlTradgVol']) if 'TtlTradgVol' in row and pd.notna(row['TtlTradgVol']) else None,
                        total_traded_val=float(row['TtlTrfVal']) if 'TtlTrfVal' in row and pd.notna(row['TtlTrfVal']) else None,
                        total_trades=int(row['TtlNbOfTxsExctd']) if 'TtlNbOfTxsExctd' in row and pd.notna(row['TtlNbOfTxsExctd']) else None,
                        open_interest=int(row['OpnIntrst']) if 'OpnIntrst' in row and pd.notna(row['OpnIntrst']) else None,
                        change_in_oi=int(row['ChngInOpnIntrst']) if 'ChngInOpnIntrst' in row and pd.notna(row['ChngInOpnIntrst']) else None
                    )

                    objects.append(bhavcopy)

                except Exception as e:
                    total_errors.append(f"Row error: {str(e)}")

            # Bulk Save per file
            try:
                if objects:
                    db.bulk_save_objects(objects)
                    db.commit()
                    total_inserted += len(objects)
            except IntegrityError:
                db.rollback()
                total_errors.append(f"Integrity Error in {os.path.basename(csv_path)}")
            except Exception as e:
                db.rollback()
                total_errors.append(f"Error in {os.path.basename(csv_path)}: {str(e)}")

            # Record history
            try:
                import_record = ImportHistory(
                    file_name=os.path.basename(csv_path),
                    file_date=parsed_file_date,
                    segment=','.join(segments_list),
                    rows_imported=len(objects),
                    import_date=datetime.now().date()
                )
                db.add(import_record)
                db.commit()
            except:
                db.rollback()

        return {
            'success': True,
            'inserted': total_inserted,
            'skipped': total_skipped,
            'skipped_reasons': skipped_reasons,
            'errors': total_errors[:20],
            'mode': mode
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        logger.error(f"Import Error: {e}")
        traceback.print_exc()
        raise HTTPException(500, f"Error importing data: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        if csv_path and os.path.exists(csv_path):
            os.unlink(csv_path)

@router.get("/api/data/upload/bhavcopy/check-date/{date}")
async def check_date_exists(
    date: str,
    segment: str = Query("CM", regex="^(CM|FO|BOTH)$"),
    db: Session = Depends(get_db)
):
    # Same as before
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()

        segments = ['CM', 'FO'] if segment == 'BOTH' else [segment]

        # Get count by segment
        result = {}
        for seg in segments:
            count = db.query(Bhavcopy).filter(
                Bhavcopy.trade_date == target_date,
                Bhavcopy.segment == seg
            ).count()

            if count > 0:
                # Get sample symbols
                samples = db.query(Bhavcopy.symbol).filter(
                    Bhavcopy.trade_date == target_date,
                    Bhavcopy.segment == seg
                ).limit(5).all()

                result[seg] = {
                    'exists': True,
                    'count': count,
                    'samples': [s[0] for s in samples]
                }
            else:
                result[seg] = {
                    'exists': False,
                    'count': 0
                }

        return {
            'date': date,
            'exists': any(r['exists'] for r in result.values()),
            'segments': result
        }

    except ValueError:
        raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD")
