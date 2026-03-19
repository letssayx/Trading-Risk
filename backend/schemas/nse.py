from typing import Literal, Any
from datetime import date, datetime
from pydantic import BaseModel, Field

class NSEImportRequest(BaseModel):
    """Request to trigger NSE data import for a specific date."""
    date: str = Field(..., description="Date in YYYY-MM-DD format", example="2026-02-18")
    patterns: list[str] | None = Field(None, description="List of specific file patterns to import (e.g., ['bhavcopy_fo'])")
    force: bool = Field(False, description="Force re-import even if data exists")
    include_non_fo: bool = Field(False, description="Allow importing Corporate Actions/Board Meetings for all non-F&O equities")

class NSEImportResponse(BaseModel):
    """Response from import operation."""
    status: str = Field(..., description="Status of the operation (COMPLETED, FAILED, SKIPPED)")
    date: str = Field(..., description="Date processed in YYYY-MM-DD format")
    files_processed: int = Field(..., description="Total number of file patterns attempted")
    successful: int = Field(..., description="Number of successfully imported files")
    details: dict[str, Any] = Field(..., description="Per-file status details")

class TimeseriesQuery(BaseModel):
    """Query parameters for timeseries data."""
    symbol: str = Field(..., description="Stock symbol (e.g., RELIANCE)")
    start_date: date = Field(..., description="Start date")
    end_date: date = Field(..., description="End date")
    resample: Literal['1h', '1d', '1w', '1m'] = Field('1d', description="Time bucket for resampling")

class OITrendResponse(BaseModel):
    """Open Interest Trend Data."""
    symbol: str
    expiry: str | None = None
    source: str = Field(..., description="Data source (continuous_aggregate or raw_table)")
    data: list[dict[str, Any]]
    meta: dict[str, Any] | None = None

class VolatilityCompareRequest(BaseModel):
    """Request to compare volatility across symbols."""
    symbols: list[str] = Field(..., min_items=1, max_items=10, description="List of symbols to compare")
    days: int = Field(90, ge=1, le=365, description="Number of days to look back")

class ImportStatsSummary(BaseModel):
    table_name: str
    status: str
    job_count: int
    total_rows: int | None = None
    last_import_date: date | None = None
    last_download_time: datetime | None = None

class ImportStatsResponse(BaseModel):
    """Statistics about import jobs."""
    summary: list[ImportStatsSummary]
    period: dict[str, str | None]
