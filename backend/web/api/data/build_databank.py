from fastapi import APIRouter, Query
from backend.ingest.tasks import build_dividend_databank_task

router = APIRouter()

@router.post("/api/data/dividends/build-databank")
def build_dividend_databank(force: bool = Query(False)):
    """
    Rebuilds the DividendDatabank table asynchronously via Celery.
    """
    task = build_dividend_databank_task(force=force)
    return {"message": "Dividend Databank built successfully", "task_id": "sync"}
