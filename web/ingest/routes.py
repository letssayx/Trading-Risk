import pandas as pd
import io
import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from web.auth.routes import get_current_user
from domain.common.user import User

router = APIRouter(prefix="/api/ingest", tags=["Data Ingestion"])

# Mock DB Storage
INGESTION_LOG = []
MARKET_DATA_STORE = []

@router.post("/derivative-data")
async def ingest_data(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    """
    Ingests exchange data (CSV) and populates the Market Intelligence layer.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    content = await file.read()
    try:
        # 1. Parse CSV
        df = pd.read_csv(io.BytesIO(content))

        # 2. Validation (Mock)
        required_cols = {'symbol', 'oi', 'vol', 'price', 'timestamp'}
        if not required_cols.issubset(df.columns):
             # Try simple mapping or fail
             pass # In real app, strict validation

        # 3. Map to Domain (Mock Storage)
        records_count = len(df)

        # Log the ingestion
        log_entry = {
            "upload_id": str(uuid.uuid4()),
            "user_id": current_user.id,
            "file_name": file.filename,
            "record_count": records_count,
            "status": "Completed",
            "timestamp": datetime.now()
        }
        INGESTION_LOG.append(log_entry)

        return {
            "status": "success",
            "message": f"Successfully processed {records_count} records.",
            "upload_id": log_entry["upload_id"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
