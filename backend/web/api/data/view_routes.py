from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
import pandas as pd
import io
from datetime import datetime

from backend.infrastructure.db import get_db
from backend.domain.market.models import Bhavcopy

router = APIRouter()

@router.get("/api/data/view/search")
async def search_data(
    symbol: str = Query(..., min_length=2),
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Search data by symbol (latest first).
    """
    results = db.query(Bhavcopy).filter(
        Bhavcopy.symbol == symbol.upper()
    ).order_by(Bhavcopy.trade_date.desc()).limit(limit).all()

    data = []
    for row in results:
        data.append({
            "date": row.trade_date.strftime("%Y-%m-%d"),
            "symbol": row.symbol,
            "segment": row.segment,
            "instrument": row.instrument_type,
            "expiry": row.expiry_date.strftime("%Y-%m-%d") if row.expiry_date else "",
            "strike": row.strike_price,
            "option": row.option_type,
            "close": row.close,
            "oi": row.open_interest
        })

    return data

@router.get("/api/data/view/export")
async def export_data(
    symbol: str = Query(..., min_length=2),
    db: Session = Depends(get_db)
):
    """
    Export all data for a symbol to Excel.
    """
    # Fetch ALL data (maybe limit to reasonable amount like 5000)
    results = db.query(Bhavcopy).filter(
        Bhavcopy.symbol == symbol.upper()
    ).order_by(Bhavcopy.trade_date.desc()).limit(5000).all()

    if not results:
        raise HTTPException(status_code=404, detail="No data found")

    # Convert to DataFrame
    data = []
    for row in results:
        data.append({
            "Date": row.trade_date,
            "Symbol": row.symbol,
            "Segment": row.segment,
            "Instrument": row.instrument_type,
            "Expiry": row.expiry_date,
            "Strike": row.strike_price,
            "Option Type": row.option_type,
            "Open": row.open,
            "High": row.high,
            "Low": row.low,
            "Close": row.close,
            "Volume": row.total_traded_qty,
            "OI": row.open_interest,
            "Change in OI": row.change_in_oi
        })

    df = pd.DataFrame(data)

    # Create Excel in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=symbol.upper())

    output.seek(0)

    filename = f"{symbol.upper()}_Data_{datetime.now().strftime('%Y%m%d')}.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
