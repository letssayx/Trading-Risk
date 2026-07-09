from fastapi import APIRouter, Query
from backend.ingest.tasks import build_dividend_databank_task

router = APIRouter()

@router.post("/api/data/dividends/build-databank")
def build_dividend_databank(force: bool = Query(False)):
    """
    Rebuilds the DividendDatabank table asynchronously via Celery.
    """
    task = build_dividend_databank_task.delay(force)
    return {"message": "Dividend Databank build triggered in background via Celery", "task_id": str(task.id)}
