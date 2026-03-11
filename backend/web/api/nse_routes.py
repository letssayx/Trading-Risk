from fastapi import APIRouter, Depends, HTTPException, Query, Request, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Literal, Any
from datetime import date, datetime
import logging

from backend.infrastructure.db import get_db
from backend.schemas.nse import (
    NSEImportRequest, NSEImportResponse, TimeseriesQuery,
    OITrendResponse, VolatilityCompareRequest, ImportStatsResponse
)
from backend.ingest import queries
from backend.ingest.tasks import (
    import_nse_date, import_nse_range, import_nse_latest
)
from backend.ingest.timescale import setup_all_timescale_policies as setup_timescale_policies

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health/db")
async def check_database_health():
    """
    Check if the database is accessible.
    """
    try:
        from backend.infrastructure.db import engine
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return {
                "status": "healthy",
                "database": "connected",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        # Return 503 Service Unavailable if DB is down, but with JSON body
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/ingest/import/status/{task_id}")
async def get_import_status(task_id: str):
    """
    Get real-time import progress for a specific task.
    """
    try:
        # Query Celery task status
        from celery.result import AsyncResult
        task = AsyncResult(task_id)

        response = {
            "task_id": task_id,
            "status": task.status,  # PENDING, STARTED, SUCCESS, FAILURE, PROGRESS
            "progress": 0,
            "current_file": "",
            "files_completed": [],
            "files_failed": [],
            "error": None
        }

        if task.state == 'PROGRESS':
            # Store task info inside meta to match frontend expectations
            response["meta"] = task.info

            # Optional: maintain top-level values for backwards compatibility
            response.update({
                "progress": task.info.get("progress", task.info.get("percent", 0)),
                "current_file": task.info.get("current_file", ""),
                "files_completed": task.info.get("files_completed", []),
                "files_failed": task.info.get("files_failed", [])
            })
        elif task.state == 'SUCCESS':
            # task.result is the return value of the function
            result = task.result
            files_completed = []
            files_failed = []

            # Handle both single date (dict) and range import (list of dicts) results
            if isinstance(result, dict) and 'details' in result:
                files_completed = [k for k, v in result.get('details', {}).items() if v.get('status') == 'SUCCESS']
                files_failed = [k for k, v in result.get('details', {}).items() if v.get('status') != 'SUCCESS']
            elif isinstance(result, list):
                # Range import result is a list of results
                for day_res in result:
                    if isinstance(day_res, dict) and 'details' in day_res:
                        files_completed.extend([k for k, v in day_res.get('details', {}).items() if v.get('status') == 'SUCCESS'])
                        files_failed.extend([k for k, v in day_res.get('details', {}).items() if v.get('status') != 'SUCCESS'])

            response.update({
                "progress": 100,
                "status": "SUCCESS",
                "current_file": "Done",
                # The result structure matches NSEImportResponse mostly
                "files_completed": list(set(files_completed)),
                "files_failed": list(set(files_failed))
            })
        elif task.state == 'FAILURE':
            response.update({
                "status": "FAILURE",
                "error": str(task.result)
            })

        return response
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(status_code=500, detail={"message": "Failed to get status", "error": str(e)})

@router.post("/ingest/import", response_model=dict[str, Any])
async def trigger_import(
    request: NSEImportRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger an async import for a specific date.
    """
    try:
        task = import_nse_date.delay(request.date, request.patterns, request.force)
        return {"success": True, "task_id": str(task.id), "message": "Import started in background"}
    except Exception as e:
        logger.error(f"Failed to trigger import task: {e}")
        raise HTTPException(status_code=503, detail={"message": "Failed to queue import task", "error": str(e)})

@router.post("/ingest/import/range")
async def trigger_import_range(
    start_date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    patterns: list[str] | None = Query(None),
    force: bool = Query(False)
):
    """
    Trigger an async import for a date range.
    """
    try:
        task = import_nse_range.delay(start_date, end_date, patterns, force=force)
        return {"success": True, "task_id": str(task.id), "message": "Range import started in background"}
    except Exception as e:
        logger.error(f"Failed to trigger range import task: {e}")
        raise HTTPException(status_code=503, detail={"message": "Failed to queue import task", "error": str(e)})

@router.post("/ingest/import/latest")
async def trigger_import_latest(
    patterns: list[str] | None = Query(None),
    force: bool = Query(False)
):
    """
    Trigger an async import for the latest trading day.
    """
    try:
        task = import_nse_latest.delay(patterns, force=force)
        return {"success": True, "task_id": str(task.id), "message": "Latest import started in background"}
    except Exception as e:
        logger.error(f"Failed to trigger latest import task: {e}")
        raise HTTPException(status_code=503, detail={"message": "Failed to queue import task", "error": str(e)})

@router.post("/ingest/timescale/setup")
async def setup_timescale(db: Session = Depends(get_db)):
    """
    Initialize TimescaleDB policies (One-time setup).
    """
    from fastapi.concurrency import run_in_threadpool
    try:
        await run_in_threadpool(setup_timescale_policies, db)
        return {"success": True, "message": "TimescaleDB setup completed"}
    except Exception as e:
        logger.error(f"Failed to trigger timescale setup: {e}")
        raise HTTPException(status_code=503, detail={"message": "Failed to queue setup task", "error": str(e)})

@router.get("/ingest/stats", response_model=ImportStatsResponse)
async def get_stats(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db)
):
    """
    Get statistics about import jobs.
    """
    try:
        from fastapi.concurrency import run_in_threadpool
        return await run_in_threadpool(queries.get_import_stats, db, start_date, end_date)
    except Exception as e:
        logger.error(f"Failed to fetch stats: {e}")
        raise HTTPException(status_code=500, detail={"message": "Database query failed", "error": str(e)})

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
    try:
        from fastapi.concurrency import run_in_threadpool
        data = await run_in_threadpool(queries.get_bhavcopy_eq_timeseries, db, symbol, start_date, end_date, resample)
        if not data:
            raise HTTPException(status_code=404, detail="No data found for criteria")
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"Timeseries query failed: {e}")
        raise HTTPException(status_code=500, detail={"message": "Query failed", "error": str(e)})

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
    try:
        from fastapi.concurrency import run_in_threadpool
        result = await run_in_threadpool(queries.get_fno_oi_trend, db, symbol, expiry, lookback_days)
        if not result:
            raise HTTPException(status_code=404, detail="No data found")

        return OITrendResponse(
            symbol=symbol,
            expiry=result.get('expiry'),
            source=result.get('source', 'unknown'),
            data=result.get('data', []),
            meta={}
        )
    except Exception as e:
        logger.error(f"OI Trend query failed: {e}")
        raise HTTPException(status_code=500, detail={"message": "Query failed", "error": str(e)})

@router.get("/market/fno/volatility/compare")
async def compare_volatility(
    symbols: str = Query(..., description="Comma-separated list of symbols"),
    days: int = 90,
    db: Session = Depends(get_db)
):
    """
    Compare volatility across multiple symbols.
    """
    try:
        symbol_list = [s.strip() for s in symbols.split(',')]
        if len(symbol_list) > 10:
            raise HTTPException(status_code=400, detail="Max 10 symbols allowed")

        from fastapi.concurrency import run_in_threadpool
        df = await run_in_threadpool(queries.get_volatility_comparison, db, symbol_list, days)
        return {"success": True, "data": df.to_dict(orient="records")}
    except Exception as e:
        logger.error(f"Volatility comparison failed: {e}")
        raise HTTPException(status_code=500, detail={"message": "Query failed", "error": str(e)})

@router.get("/market/fno/oi/participant/heatmap")
async def get_participant_heatmap(
    date: date | None = None,
    db: Session = Depends(get_db)
):
    """
    Get Participant-wise Open Interest Heatmap.
    """
    try:
        from fastapi.concurrency import run_in_threadpool
        result = await run_in_threadpool(queries.get_participant_oi_heatmap, db, date)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Heatmap query failed: {e}")
        raise HTTPException(status_code=500, detail={"message": "Query failed", "error": str(e)})

@router.post("/api/v1/symbol-master/upload")
async def upload_symbol_master(request: Request, db: Session = Depends(get_db)):
    """Uploads and merges Symbol Master data from CSV or manual entry."""
    from backend.ingest.nse_models import SymbolMaster
    from fastapi.concurrency import run_in_threadpool

    try:
        payload = await request.json()
        data = payload.get("data", [])

        if not data:
            return {"success": False, "message": "No data provided."}

        def process_upload():
            for row in data:
                symbol = row.get("symbol")
                if not symbol:
                    continue
                symbol = str(symbol).strip().upper()

                # Upsert logic
                existing = db.query(SymbolMaster).filter(SymbolMaster.symbol == symbol).first()
                if not existing:
                    existing = SymbolMaster(symbol=symbol)
                    db.add(existing)

                existing.company_name = row.get("company_name", existing.company_name)
                existing.broad_index = row.get("broad_index", existing.broad_index)
                existing.sector_index = row.get("sector_index", existing.sector_index)
                existing.derivative_liquidity_tier = row.get("derivative_liquidity_tier", existing.derivative_liquidity_tier)
                existing.typical_hedge_index = row.get("typical_hedge_index", existing.typical_hedge_index)

            db.commit()

        await run_in_threadpool(process_upload)
        return {"success": True, "message": f"Successfully processed {len(data)} symbol records."}

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to process Symbol Master upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/symbol-master")
async def get_symbol_master(db: Session = Depends(get_db)):
    """Fetches all Symbol Master data."""
    from backend.ingest.nse_models import SymbolMaster
    from fastapi.concurrency import run_in_threadpool

    def fetch_data():
        records = db.query(SymbolMaster).order_by(SymbolMaster.symbol).all()
        return [
            {
                "symbol": r.symbol,
                "company_name": r.company_name,
                "broad_index": r.broad_index,
                "sector_index": r.sector_index,
                "derivative_liquidity_tier": r.derivative_liquidity_tier,
                "typical_hedge_index": r.typical_hedge_index
            } for r in records
        ]

    data = await run_in_threadpool(fetch_data)
    return {"success": True, "data": data}
