import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.auth.routes import get_current_user
from backend.domain.common.user import User
from backend.dependencies import get_db
from backend.ingest.data_vault import DataVault
from backend.domain.audit.models import AuditTrail

router = APIRouter(prefix="/api/ingest", tags=["Data Ingestion"])

@router.post("/derivative-data")
async def ingest_data(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ingests exchange data (CSV) via DataVault.
    Populates 'market_data' hypertable and maps tickers in 'instruments'.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    content = await file.read()
    try:
        vault = DataVault(db)
        records_count = vault.process_csv(content)

        # Audit Log
        audit = AuditTrail(
            user_id=current_user.id,
            action_type="DATA_INGEST_CSV",
            entity_type="DATA_VAULT",
            entity_id="BULK_UPLOAD",
            after_state={"file": file.filename, "records": records_count},
            timestamp=datetime.utcnow()
        )
        db.add(audit)
        db.commit()

        return {
            "status": "success",
            "message": f"Successfully processed {records_count} records via DataVault.",
            "file": file.filename
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
