from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlalchemy.orm import Session
import pandas as pd
import io
import datetime
import os

from backend.infrastructure.db import get_db
from backend.domain.market.service import MarketDataService

router = APIRouter()

@router.get("/data-viewer", response_class=HTMLResponse)
async def data_viewer_page():
    # Try multiple paths to find the template
    possible_paths = [
        "backend/ui/templates/data_viewer.html",  # From root
        "ui/templates/data_viewer.html",          # If in backend
        os.path.join(os.path.dirname(__file__), "../../../ui/templates/data_viewer.html") # Relative
    ]

    template_path = None
    for p in possible_paths:
        if os.path.exists(p):
            template_path = p
            break

    if not template_path:
        return "<h1>Template not found (Checked multiple paths)</h1>"

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"<h1>Error reading template: {str(e)}</h1>"

@router.get("/api/data/view/history/{symbol}")
async def get_history_view(
    symbol: str,
    db: Session = Depends(get_db)
):
    """
    Get all historical data for a symbol (Date-wise)
    """
    data = MarketDataService.get_daily_ohlc(db, symbol, days=3650) # 10 years
    if not data:
        return []
    return data

@router.get("/api/data/view/export/{symbol}")
async def export_history_view(
    symbol: str,
    db: Session = Depends(get_db)
):
    """
    Export historical data to Excel
    """
    data = MarketDataService.get_daily_ohlc(db, symbol, days=3650)
    if not data:
        raise HTTPException(status_code=404, detail="No data found")

    df = pd.DataFrame(data)

    # Filter columns if they exist
    cols = ['time', 'open', 'high', 'low', 'close', 'volume', 'oi', 'expiry']
    valid_cols = [c for c in cols if c in df.columns]
    if valid_cols:
        df = df[valid_cols]

    output = io.BytesIO()
    # Use xlsxwriter for Excel export
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name=symbol[:30])

    output.seek(0)

    filename = f"{symbol}_History_{datetime.date.today()}.xlsx"
    headers = {
        'Content-Disposition': f'attachment; filename="{filename}"'
    }
    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers=headers
    )
