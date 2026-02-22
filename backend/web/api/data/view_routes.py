from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
import pandas as pd
import io
from datetime import datetime
from typing import Optional

from backend.infrastructure.db import get_db
from backend.domain.market.models import Bhavcopy

router = APIRouter()

@router.get("/api/data/view/search")
async def search_data(
    symbol: str = Query(..., min_length=2),
    segment: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Search data by symbol (latest first).
    """
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
