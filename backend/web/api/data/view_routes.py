from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlalchemy.orm import Session
import pandas as pd
import io
import datetime
import os
import logging
import traceback

from backend.infrastructure.db import get_db
from backend.domain.market.service import MarketDataService

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/data-viewer", response_class=HTMLResponse)
async def data_viewer_page():
    # Try multiple paths to find the template
    possible_paths = [
        "backend/ui/templates/data_viewer.html",  # From repo root
        "ui/templates/data_viewer.html",          # If in backend directory
        os.path.join(os.path.dirname(__file__), "../../../ui/templates/data_viewer.html"), # Relative from this file
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../ui/templates/data_viewer.html")) # Absolute
    ]

    template_path = None
    tried_paths = []
    for p in possible_paths:
        tried_paths.append(os.path.abspath(p))
        if os.path.exists(p):
            template_path = p
            break

    if not template_path:
        error_msg = f"<h1>Template not found</h1><p>Checked paths:</p><ul>" + "".join([f"<li>{p}</li>" for p in tried_paths]) + "</ul>"
        logger.error(f"Template not found. Checked: {tried_paths}")
        return HTMLResponse(content=error_msg, status_code=500)

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading template: {e}")
        return HTMLResponse(content=f"<h1>Error reading template: {str(e)}</h1>", status_code=500)

@router.get("/api/data/view/history/{symbol}")
async def get_history_view(
    symbol: str,
    db: Session = Depends(get_db)
):
    """
    Get all historical data for a symbol (Date-wise)
    """
    try:
        data = MarketDataService.get_daily_ohlc(db, symbol, days=3650) # 10 years
        if not data:
            return []
        return data
    except Exception as e:
        logger.error(f"Error fetching history for {symbol}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.get("/api/data/view/export/{symbol}")
async def export_history_view(
    symbol: str,
    db: Session = Depends(get_db)
):
    """
    Export historical data to Excel
    """
    try:
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting history for {symbol}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Export Failed: {str(e)}")
