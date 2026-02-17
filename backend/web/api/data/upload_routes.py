import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List, Dict, Any
import io
import zipfile
from datetime import datetime
from sqlalchemy.orm import Session
from backend.infrastructure.db import get_db
from backend.domain.market.models import Bhavcopy

router = APIRouter()

# Temporary storage for parsed data (in memory for this phase)
# In production, use Redis or a temp table
PENDING_IMPORTS: Dict[str, List[Dict]] = {}

def parse_date(date_str: str) -> datetime.date:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        # Try DD-MMM-YYYY
        try:
            return datetime.strptime(date_str, "%d-%b-%Y").date()
        except ValueError:
            return None

@router.post("/api/data/upload/bhavcopy")
async def upload_bhavcopy(file: UploadFile = File(...)):
    """
    Accepts: ZIP file containing UDIFF CSV (e.g., BhavCopy_NSE_CM_0_0_0_20260206_F_0000.csv.zip)
    """
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are supported")

    try:
        contents = await file.read()
        with zipfile.ZipFile(io.BytesIO(contents)) as z:
            # Find the CSV file
            csv_filename = None
            for name in z.namelist():
                if name.endswith('.csv'):
                    csv_filename = name
                    break

            if not csv_filename:
                raise HTTPException(status_code=400, detail="No CSV found inside ZIP")

            with z.open(csv_filename) as f:
                df = pd.read_csv(f)

        # UDIFF Headers check
        required_cols = ['Sgmt', 'FinInstrmTp', 'SctySrs', 'TckrSymb', 'TradDt']
        if not all(col in df.columns for col in required_cols):
             raise HTTPException(status_code=400, detail="Invalid UDIFF format. Missing columns.")

        # Stats
        total_rows = len(df)

        # Filter Logic
        # Sgmt = 'CM', FinInstrmTp = 'STK', SctySrs in ['EQ', 'BE']
        filtered_df = df[
            (df['Sgmt'] == 'CM') &
            (df['FinInstrmTp'] == 'STK') &
            (df['SctySrs'].isin(['EQ', 'BE']))
        ].copy()

        filtered_count = len(filtered_df)

        if filtered_count == 0:
            return {
                "preview": [],
                "stats": {
                    "total_rows": total_rows,
                    "filtered_rows": 0,
                    "date": "N/A"
                }
            }

        # Extract Date (from first row)
        trade_date_str = filtered_df.iloc[0]['TradDt'] # e.g. 2026-02-06

        # Prepare rows for DB
        rows_to_insert = []
        for _, row in filtered_df.iterrows():
            rows_to_insert.append({
                "trade_date": row['TradDt'],
                "business_date": row['BizDt'],
                "segment": row['Sgmt'],
                "instrument_type": row['FinInstrmTp'],
                "symbol": row['TckrSymb'],
                "series": row['SctySrs'],
                "isin": row.get('ISIN', ''),
                "open": row.get('OpnPric', 0.0),
                "high": row.get('HghPric', 0.0),
                "low": row.get('LwPric', 0.0),
                "close": row.get('ClsPric', 0.0),
                "last": row.get('LastPric', 0.0),
                "prev_close": row.get('PrvsClsgPric', 0.0),
                "total_traded_qty": row.get('TtlTradgVol', 0),
                "total_traded_val": row.get('TtlTrfVal', 0.0),
                "total_trades": row.get('TtlNbOfTxsExctd', 0)
            })

        # Cache for confirmation step
        import_id = f"import_{datetime.now().timestamp()}"
        PENDING_IMPORTS[import_id] = rows_to_insert

        # Generate Preview (First 5)
        preview = rows_to_insert[:5]

        return {
            "import_id": import_id,
            "preview": preview,
            "stats": {
                "total_rows": total_rows,
                "filtered_rows": filtered_count,
                "date": trade_date_str
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/data/import/bhavcopy/confirm")
async def confirm_import(payload: Dict[str, str], db: Session = Depends(get_db)):
    import_id = payload.get("import_id")
    if not import_id or import_id not in PENDING_IMPORTS:
        raise HTTPException(status_code=404, detail="Import session expired or not found")

    rows = PENDING_IMPORTS[import_id]

    try:
        # Bulk Insert
        # Using simple loop with merge or insert. For bulk, core insert is faster.
        # But we need to handle duplicates (INSERT OR IGNORE or UPSERT).
        # SQLAlchemy merge is slow for bulk.
        # Let's verify if date exists first?

        # Check if date exists to warn? (Optional)

        objects = []
        for r in rows:
            # Parse dates
            t_date = parse_date(r['trade_date'])
            b_date = parse_date(r['business_date'])

            obj = Bhavcopy(
                trade_date=t_date,
                business_date=b_date,
                segment=r['segment'],
                instrument_type=r['instrument_type'],
                symbol=r['symbol'],
                series=r['series'],
                isin=r['isin'],
                open=r['open'],
                high=r['high'],
                low=r['low'],
                close=r['close'],
                last=r['last'],
                prev_close=r['prev_close'],
                total_traded_qty=r['total_traded_qty'],
                total_traded_val=r['total_traded_val'],
                total_trades=r['total_trades']
            )
            objects.append(obj)

        # Use bulk_save_objects (faster than add_all)
        # Note: This doesn't handle duplicates gracefully by default in SQLite without strict unique constraints handling.
        # We added UniqueConstraint. If duplicate, it will raise IntegrityError.
        # For 'INSERT OR IGNORE', we'd need raw SQL or specific dialect support.
        # Let's wrap in try-except for now or delete existing for that day?
        # Safe strategy: Delete existing data for this day if re-importing?
        # Or just fail if exists.

        # Simple Approach: Try to insert. If fails, user knows.
        db.bulk_save_objects(objects)
        db.commit()

        # Cleanup
        del PENDING_IMPORTS[import_id]

        return {"status": "success", "imported_count": len(objects)}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
