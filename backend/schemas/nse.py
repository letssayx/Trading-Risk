from typing import List, Optional, Dict, Literal, Any
from datetime import date
from pydantic import BaseModel, Field

class NSEImportRequest(BaseModel):
    """Request to trigger NSE data import for a specific date."""
    date: str = Field(..., description="Date in YYYY-MM-DD format", example="2026-02-18")
    patterns: Optional[List[str]] = Field(None, description="List of specific file patterns to import (e.g., ['bhavcopy_fo'])")
    force: bool = Field(False, description="Force re-import even if data exists")

class NSEImportResponse(BaseModel):
    """Response from import operation."""
    status: str = Field(..., description="Status of the operation (COMPLETED, FAILED, SKIPPED)")
    date: str = Field(..., description="Date processed in YYYY-MM-DD format")
    files_processed: int = Field(..., description="Total number of file patterns attempted")
    successful: int = Field(..., description="Number of successfully imported files")
    details: Dict[str, Any] = Field(..., description="Per-file status details")

class TimeseriesQuery(BaseModel):
    """Query parameters for timeseries data."""
    symbol: str = Field(..., description="Stock symbol (e.g., RELIANCE)")
    start_date: date = Field(..., description="Start date")
    end_date: date = Field(..., description="End date")
    resample: Literal['1h', '1d', '1w', '1m'] = Field('1d', description="Time bucket for resampling")

class OITrendResponse(BaseModel):
    """Open Interest Trend Data."""
    symbol: str
    expiry: Optional[str] = None
    source: str = Field(..., description="Data source (continuous_aggregate or raw_table)")
    data: List[Dict[str, Any]]
    meta: Optional[Dict[str, Any]] = None

class VolatilityCompareRequest(BaseModel):
    """Request to compare volatility across symbols."""
    symbols: List[str] = Field(..., min_items=1, max_items=10, description="List of symbols to compare")
    days: int = Field(90, ge=1, le=365, description="Number of days to look back")

class ImportStatsResponse(BaseModel):
    """Statistics about import jobs."""
    summary: List[Dict[str, Any]]
    period: Dict[str, Optional[str]]
