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

router = APIRouter()

# Allowed series and segments
ALLOWED_SERIES = ['EQ', 'BE']  # For CM segment
ALLOWED_SEGMENTS = ['CM', 'FO']  # Both segments

# Instrument type mappings
INSTRUMENT_TYPES = {
    'CM': ['STK'],  # Only stocks in CM
    'FO': ['FUTSTK', 'OPTSTK', 'FUTIDX', 'OPTIDX']  # All FO instruments
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
    """Parse UDIFF date format (DD-MMM-YYYY)"""
    if pd.isna(date_str):
        return None
    if isinstance(date_str, datetime):
        return date_str.date()
    if isinstance(date_str, date):
        return date_str
    try:
        return datetime.strptime(str(date_str).strip(), "%d-%b-%Y").date()
    except:
        return None

def validate_headers(headers: List[str]) -> bool:
    """Check if CSV has required UDIFF headers"""
    required = ['TradDt', 'Sgmt', 'FinInstrmTp', 'TckrSymb']
    return all(req in headers for req in required)

def parse_bhavcopy_df(df: pd.DataFrame) -> pd.DataFrame:
    """Parse and clean dataframe with proper types"""
    # Parse dates
    df['parsed_trade_date'] = df['TradDt'].apply(parse_udiff_date)
    # BizDt is not always present or same as TradDt
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
    db: Session = Depends(get_db)
):
    """
    Upload and preview bhavcopy ZIP file - shows both CM and FO data
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
        if not validate_headers(df.columns.tolist()):
            raise HTTPException(400, f"Invalid CSV format. Expected UDIFF headers.")

        # Parse data
        df = parse_bhavcopy_df(df)

        # Get file date from filename or data
        file_date = None
        if len(df) > 0:
            file_date = df['parsed_trade_date'].iloc[0]

        # Check if this date already exists in DB
        existing_dates = []
        if file_date:
            existing = db.query(Bhavcopy).filter(
                Bhavcopy.trade_date == file_date
            ).first()
            if existing:
                existing_dates = [file_date]

        # Check if this file was imported before
        existing_import = None
        if file_date:
            existing_import = check_existing_import(db, file.filename, file_date)

        # Prepare stats by segment
        stats = {}
        preview_by_segment = {}

        for segment in ALLOWED_SEGMENTS:
            segment_df = df[df['Sgmt'] == segment]

            if segment == 'CM':
                # For CM: filter instrument type STK and series EQ/BE
                segment_df = segment_df[
                    (segment_df['FinInstrmTp'] == 'STK') &
                    (segment_df['SctySrs'].isin(ALLOWED_SERIES))
                ]
            else:  # FO
                # For FO: include all instrument types
                segment_df = segment_df[
                    segment_df['FinInstrmTp'].isin(INSTRUMENT_TYPES['FO'])
                ]

            stats[segment] = {
                'total_rows': len(segment_df),
                'unique_symbols': segment_df['TckrSymb'].nunique() if len(segment_df) > 0 else 0,
                'instrument_types': segment_df['FinInstrmTp'].value_counts().to_dict() if len(segment_df) > 0 else {}
            }

            # Get preview (first 5 rows)
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

                # Add FO specific fields
                if segment == 'FO':
                    expiry = row.get('parsed_expiry_date')
                    preview_row.update({
                        'expiry': expiry.strftime("%Y-%m-%d") if pd.notna(expiry) else None,
                        'strike': float(row['StrkPric']) if pd.notna(row.get('StrkPric')) else None,
                        'option_type': row.get('OptnTp') if pd.notna(row.get('OptnTp')) else 'XX',
                        'open_interest': int(row['OpnIntrst']) if pd.notna(row.get('OpnIntrst')) else 0
                    })
                else:
                    preview_row.update({
                        'series': row['SctySrs'],
                        'volume': int(row['TtlTradgVol']) if pd.notna(row.get('TtlTradgVol')) else 0
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

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Error processing file: {str(e)}")
    finally:
        # Cleanup
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        if csv_path and os.path.exists(csv_path):
            os.unlink(csv_path)

@router.post("/api/data/upload/bhavcopy/import")
async def import_bhavcopy(
    file: UploadFile = File(...),
    file_date: str = Form(...),
    overwrite_existing: bool = Form(...),
    segments: str = Form(...), # JSON string
    db: Session = Depends(get_db)
):
    """
    Import bhavcopy data with overwrite option
    """
    segments_list = json.loads(segments)

    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name

    csv_path = None
    try:
        # Extract and parse
        with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
            csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
            csv_path = zip_ref.extract(csv_files[0], tempfile.gettempdir())

        df = pd.read_csv(csv_path)
        df = parse_bhavcopy_df(df)

        parsed_file_date = datetime.strptime(file_date, "%Y-%m-%d").date()

        # If overwrite is enabled, delete existing data for this date and segments
        if overwrite_existing:
            deleted = db.query(Bhavcopy).filter(
                Bhavcopy.trade_date == parsed_file_date,
                Bhavcopy.segment.in_(segments_list)
            ).delete(synchronize_session=False)
            db.commit()
            print(f"Deleted {deleted} existing rows for {parsed_file_date}")

        # Insert data
        inserted = 0
        skipped = 0
        errors = []

        objects = []

        for _, row in df.iterrows():
            segment = row['Sgmt']

            # Skip if segment not requested
            if segment not in segments_list:
                continue

            # Apply filtering based on segment
            if segment == 'CM':
                if row['FinInstrmTp'] != 'STK' or row['SctySrs'] not in ALLOWED_SERIES:
                    continue
            elif segment == 'FO':
                if row['FinInstrmTp'] not in INSTRUMENT_TYPES['FO']:
                    continue
            else:
                continue

            try:
                bhavcopy = Bhavcopy(
                    trade_date=row['parsed_trade_date'],
                    segment=segment,
                    instrument_type=row['FinInstrmTp'],
                    symbol=row['TckrSymb'],

                    # Common fields
                    series=row.get('SctySrs'),
                    isin=row.get('ISIN'),

                    # FO specific
                    expiry_date=row.get('parsed_expiry_date'),
                    strike_price=float(row['StrkPric']) if pd.notna(row.get('StrkPric')) else None,
                    option_type=row.get('OptnTp') if pd.notna(row.get('OptnTp')) else None,
                    underlying=row.get('UndrlygPric'),

                    # Prices
                    open=float(row['OpnPric']) if pd.notna(row.get('OpnPric')) else None,
                    high=float(row['HghPric']) if pd.notna(row.get('HghPric')) else None,
                    low=float(row['LwPric']) if pd.notna(row.get('LwPric')) else None,
                    close=float(row['ClsPric']) if pd.notna(row.get('ClsPric')) else None,
                    last=float(row['LastPric']) if pd.notna(row.get('LastPric')) else None,
                    prev_close=float(row['PrvsClsgPric']) if pd.notna(row.get('PrvsClsgPric')) else None,
                    settlement_price=float(row['SttlmPric']) if pd.notna(row.get('SttlmPric')) else None,

                    # Volume & OI
                    total_traded_qty=int(row['TtlTradgVol']) if pd.notna(row.get('TtlTradgVol')) else None,
                    total_traded_val=float(row['TtlTrfVal']) if pd.notna(row.get('TtlTrfVal')) else None,
                    total_trades=int(row['TtlNbOfTxsExctd']) if pd.notna(row.get('TtlNbOfTxsExctd')) else None,
                    open_interest=int(row['OpnIntrst']) if pd.notna(row.get('OpnIntrst')) else None,
                    change_in_oi=int(row['ChngInOpnIntrst']) if pd.notna(row.get('ChngInOpnIntrst')) else None
                )

                objects.append(bhavcopy)

            except Exception as e:
                errors.append(f"Row error: {str(e)}")

        # Bulk Save
        # Note: bulk_save_objects is faster but doesn't return inserted IDs.
        try:
            if objects:
                db.bulk_save_objects(objects)
                db.commit()
                inserted = len(objects)
        except IntegrityError as e:
            db.rollback()
            # If overwrite was false, this means we hit duplicates.
            # Without overwrite, we can't easily skip individual rows in bulk without raw SQL 'INSERT OR IGNORE'
            # For now, fail the batch or try row-by-row if critical.
            # Assuming overwrite handles the mass update case.
            raise HTTPException(400, "Integrity Error: Data likely exists. Use Overwrite option.")
        except Exception as e:
            db.rollback()
            raise HTTPException(500, f"Database commit error: {str(e)}")

        # Record this import
        import_record = ImportHistory(
            file_name=file.filename,
            file_date=parsed_file_date,
            segment=','.join(segments_list),
            rows_imported=inserted,
            import_date=datetime.now().date()
        )
        try:
            db.add(import_record)
            db.commit()
        except IntegrityError:
            db.rollback()
            # History already exists, ignore or update?
            pass

        return {
            'success': True,
            'inserted': inserted,
            'skipped': skipped,
            'errors': errors[:10],  # First 10 errors
            'date': file_date,
            'segments': segments_list
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        import traceback
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
    """
    Check if data for a specific date already exists
    """
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
