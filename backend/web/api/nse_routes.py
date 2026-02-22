from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Literal, Any
from datetime import date

from backend.infrastructure.db import get_db
from backend.schemas.nse import (
    NSEImportRequest, NSEImportResponse, TimeseriesQuery,
    OITrendResponse, VolatilityCompareRequest, ImportStatsResponse
)
from backend.ingest import queries
from backend.ingest.tasks import (
    import_nse_date, import_nse_range, import_nse_latest, setup_timescale_policies
)

router = APIRouter()

@router.post("/ingest/import", response_model=dict[str, Any])
async def trigger_import(
    request: NSEImportRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger an async import for a specific date.
    """
    task = import_nse_date.delay(request.date, request.patterns, request.force)
    return {"success": True, "task_id": str(task.id), "message": "Import started in background"}

@router.post("/ingest/import/range")
async def trigger_import_range(
    start_date: str = Query(..., regex=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: str = Query(..., regex=r"^\d{4}-\d{2}-\d{2}$"),
    patterns: list[str] | None = Query(None)
):
    """
    Trigger an async import for a date range.
    """
    task = import_nse_range.delay(start_date, end_date, patterns)
    return {"success": True, "task_id": str(task.id), "message": "Range import started in background"}

@router.post("/ingest/import/latest")
async def trigger_import_latest(
    patterns: list[str] | None = Query(None)
):
    """
    Trigger an async import for the latest trading day.
    """
    task = import_nse_latest.delay(patterns)
    return {"success": True, "task_id": str(task.id), "message": "Latest import started in background"}

@router.post("/ingest/timescale/setup")
async def setup_timescale():
    """
    Initialize TimescaleDB policies (One-time setup).
    """
    task = setup_timescale_policies.delay()
    return {"success": True, "task_id": str(task.id), "message": "TimescaleDB setup started"}

@router.get("/ingest/stats", response_model=ImportStatsResponse)
async def get_stats(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db)
):
    """
    Get statistics about import jobs.
    """
    return queries.get_import_stats(db, start_date, end_date)

@router.get("/market/bhavcopy/eq/timeseries")
async def get_eq_timeseries(
    symbol: str,
    start_date: date,
    end_date: date,
    resample: Literal['1h', '1d', '1w', '1m'] = '1d',
    db: Session = Depends(get_db)
):
    """
    Get equity timeseries data with resampling.
    """
    data = queries.get_bhavcopy_eq_timeseries(db, symbol, start_date, end_date, resample)
    if not data:
        raise HTTPException(status_code=404, detail="No data found for criteria")
    return {"success": True, "data": data}

@router.get("/market/fno/oi/trend/{symbol}", response_model=OITrendResponse)
async def get_oi_trend(
    symbol: str,
    expiry: date | None = None,
    lookback_days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Get Open Interest trend for a symbol.
    """
    result = queries.get_fno_oi_trend(db, symbol, expiry, lookback_days)
    if not result:
        raise HTTPException(status_code=404, detail="No data found")

    return OITrendResponse(
        symbol=symbol,
        expiry=result.get('expiry'),
        source=result.get('source', 'unknown'),
        data=result.get('data', []),
        meta={}
    )

@router.get("/market/fno/volatility/compare")
async def compare_volatility(
    symbols: str = Query(..., description="Comma-separated list of symbols"),
    days: int = 90,
    db: Session = Depends(get_db)
):
    """
    Compare volatility across multiple symbols.
    """
    symbol_list = [s.strip() for s in symbols.split(',')]
    if len(symbol_list) > 10:
        raise HTTPException(status_code=400, detail="Max 10 symbols allowed")

    df = queries.get_volatility_comparison(db, symbol_list, days)
    return {"success": True, "data": df.to_dict(orient="records")}

@router.get("/market/fno/oi/participant/heatmap")
async def get_participant_heatmap(
    date: date | None = None,
    db: Session = Depends(get_db)
):
    """
    Get Participant-wise Open Interest Heatmap.
    """
    result = queries.get_participant_oi_heatmap(db, date)
    return {"success": True, "data": result}
