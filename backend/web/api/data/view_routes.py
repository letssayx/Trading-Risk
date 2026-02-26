from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
import pandas as pd
import io
from datetime import datetime
from typing import Optional

from backend.infrastructure.db import get_db
from backend.domain.market.models import Bhavcopy
from backend.ingest import nse_models as models
from typing import Dict, Any, List
from datetime import datetime
import pandas as pd
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

def get_model_for_type(data_type: str):
    mapping = {
        'bhavcopy': Bhavcopy,
        'bhavcopy_eq': models.BhavcopyEQ,
        'bhavcopy_fo': models.BhavcopyFO,
        'participant_oi': models.FAOParticipantOI,
        'fo_volatility': models.FOVolatility,
        'fii_stats': models.FIIDerivativesStat,
        'bulk_deals': models.BulkDeal,
        'block_deals': models.BlockDeal,
        'mto': models.MTODelivery,
        'mwpl': models.MWPLClientPosition,
        'pe_ratio': models.PERatio,
        'var_stats': models.VaRStat,
        'contract_delta': models.ContractDelta,
        'margin_trading': models.MarginTrading,
        'security_master': models.SecurityMaster,
        'auctions': models.Auction, # Added auctions just in case
    }
    return mapping.get(data_type)

@router.get("/api/data/view/list")
async def list_data(
    type: str = Query(..., description="Data type (bhavcopy, participant_oi, etc.)"),
    symbol: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List data for a specific type with filters.
    """
    logger.info(f"View Request: type={type}, symbol={symbol}, date={start_date} to {end_date}")

    model = get_model_for_type(type)
    if not model:
        logger.error(f"Invalid data type requested: {type}")
        raise HTTPException(status_code=400, detail=f"Invalid data type: {type}")

    query = db.query(model)

    # Apply Symbol/Search Filter (if applicable)
    if symbol:
        symbol = symbol.upper().strip()

        # Comprehensive Filtering Logic
        filters = []

        # 1. Standard Symbol (Equity, Deals, P/E, VaR, Delta, Margin)
        if hasattr(model, 'symbol'):
            filters.append(model.symbol == symbol)

        # 2. Ticker Symbol (Bhavcopy FO, Security Master)
        if hasattr(model, 'ticker_symb'):
            filters.append(model.ticker_symb == symbol)

        # 3. Underlying Stock (MWPL)
        if hasattr(model, 'underlying_stock'):
            filters.append(model.underlying_stock == symbol)

        # 4. Security Name (MTO, Bulk/Block Deals descriptive fallback)
        if hasattr(model, 'security_name'):
            filters.append(model.security_name.ilike(f"%{symbol}%"))

        # 5. Client Type (Participant OI) - Exact or Partial
        if hasattr(model, 'client_type'):
             filters.append(model.client_type.ilike(f"%{symbol}%"))

        # 6. Instrument Type (FII Stats)
        if hasattr(model, 'instrument_type'):
            filters.append(model.instrument_type.ilike(f"%{symbol}%"))

        # 7. ISIN (Security Master)
        if hasattr(model, 'isin'):
            filters.append(model.isin == symbol)

        # 8. FinInstrmId (Security Master)
        if hasattr(model, 'fin_instrm_id'):
            filters.append(model.fin_instrm_id == symbol)

        # Apply filters using OR if multiple columns exist (e.g., Security Master has ticker, ISIN, ID)
        if filters:
            if len(filters) > 1:
                query = query.filter(or_(*filters))
            else:
                query = query.filter(filters[0])

    # Apply Date Filter
    date_col = getattr(model, 'trade_date', getattr(model, 'date', None))
    # Security Master uses 'listed_date' or 'updated_at' but likely user wants to browse master list regardless of date
    # If no date col (e.g. Security Master main view), skip date filter unless explicitly requested?
    # Security Master HAS listed_date but maybe updated_at is better for sorting?
    # Let's stick to trade_date/date for time-series.

    if date_col:
        if start_date:
            query = query.filter(date_col >= start_date)
        if end_date:
            query = query.filter(date_col <= end_date)

        # Order by date desc
        query = query.order_by(desc(date_col))
    elif hasattr(model, 'updated_at'):
        # Fallback for non-timeseries (Security Master)
        query = query.order_by(desc(model.updated_at))

    results = query.limit(limit).all()
    logger.info(f"Query returned {len(results)} rows for {type}")

    # Serialize results using Pydantic 'from_attributes' logic or simple dict
    # Since we don't have Pydantic models for all yet, we'll use a generic serializer
    data = []
    for row in results:
        # Convert row to dict, handling dates and serialization
        row_dict = {}
        for col in row.__table__.columns:
            val = getattr(row, col.name)
            if isinstance(val, (datetime, pd.Timestamp)):
                val = val.isoformat()
            elif hasattr(val, 'isoformat'): # date
                val = val.isoformat()
            row_dict[col.name] = val

        # Normalization for frontend consistency
        if 'ticker_symb' in row_dict and 'symbol' not in row_dict:
            row_dict['symbol'] = row_dict['ticker_symb']

        # Ensure instrument_type is present if available (handled by column add, but ensure key exists)
        if 'instrument_type' in row_dict and row_dict['instrument_type'] is None:
             # If explicitly None (legacy data), maybe map from instrument_name if possible?
             # e.g. "BANKNIFTY 26FEB2026 PE 45000" -> OPTIDX? Hard to guess reliably.
             pass
        if 'underlying_stock' in row_dict and 'symbol' not in row_dict:
            row_dict['symbol'] = row_dict['underlying_stock']

        data.append(row_dict)

    return data

@router.get("/api/data/view/search")
async def search_data(
    symbol: str = Query(..., min_length=2),
    segment: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Search data by symbol (latest first) - Legacy wrapper using generic list_data logic
    """
    # Reuse list_data logic but specific to Bhavcopy for backward compatibility
    # Or keep original logic? Original logic formats specific fields.
    # Let's keep original logic but fix the model if needed.

    query = db.query(Bhavcopy).filter(Bhavcopy.symbol == symbol.upper())

    if segment:
        query = query.filter(Bhavcopy.segment == segment)

    results = query.order_by(Bhavcopy.trade_date.desc()).limit(limit).all()

    data = []
    for row in results:
        data.append({
            "date": row.trade_date.strftime("%Y-%m-%d"),
            "biz_date": row.biz_date.strftime("%Y-%m-%d") if row.biz_date else "",
            "symbol": row.symbol,
            "segment": row.segment,
            "instrument": row.instrument_type,
            "expiry": row.expiry_date.strftime("%Y-%m-%d") if row.expiry_date else "",
            "strike": row.strike_price,
            "option": row.option_type,
            "open": row.open,
            "high": row.high,
            "low": row.low,
            "close": row.close,
            "volume": row.total_traded_qty,
            "oi": row.open_interest,
            "inst_name": row.instrument_name,
            "lot_size": row.lot_size
        })

    return data

@router.get("/api/data/view/export")
async def export_data(
    symbol: str = Query(..., min_length=2),
    segment: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Export all data for a symbol to Excel.
    """
    query = db.query(Bhavcopy).filter(Bhavcopy.symbol == symbol.upper())

    if segment:
        query = query.filter(Bhavcopy.segment == segment)

    # Fetch data
    results = query.order_by(Bhavcopy.trade_date.desc()).limit(5000).all()

    if not results:
        raise HTTPException(status_code=404, detail="No data found")

    # Convert to DataFrame
    data = []
    for row in results:
        data.append({
            "Trade Date": row.trade_date,
            "Biz Date": row.biz_date,
            "Symbol": row.symbol,
            "Segment": row.segment,
            "Instrument Type": row.instrument_type,
            "Instrument Name": row.instrument_name,
            "Expiry": row.expiry_date,
            "Actual Expiry": row.actual_expiry_date,
            "Strike": row.strike_price,
            "Option Type": row.option_type,
            "Open": row.open,
            "High": row.high,
            "Low": row.low,
            "Close": row.close,
            "Last": row.last,
            "Volume": row.total_traded_qty,
            "OI": row.open_interest,
            "Change in OI": row.change_in_oi,
            "Lot Size": row.lot_size,
            "ISIN": row.isin,
            "Remarks": row.remarks
        })

    df = pd.DataFrame(data)

    # Create Excel in memory
    output = io.BytesIO()
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=symbol.upper()[:30])
    except Exception as e:
        print(f"Excel Export Error: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

    output.seek(0)

    filename = f"{symbol.upper()}_Data_{datetime.now().strftime('%Y%m%d')}.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
