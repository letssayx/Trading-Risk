from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from backend.infrastructure.db import get_db
from backend.domain.market.models import Bhavcopy

router = APIRouter()

@router.get("/api/data/view")
async def view_data(
    segment: str = Query(..., pattern="^(CM|FO)$"),
    date_str: str = Query(..., alias="date"),
    limit: int = 100,
    offset: int = 0,
    symbol: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get paginated data for viewing
    """
    try:
        target_date = date.fromisoformat(date_str)

        query = db.query(Bhavcopy).filter(
            Bhavcopy.segment == segment,
            Bhavcopy.trade_date == target_date
        )

        if symbol:
            query = query.filter(Bhavcopy.symbol.ilike(f"%{symbol}%"))

        total = query.count()
        data = query.offset(offset).limit(limit).all()

        return {
            "total": total,
            "data": data,
            "page": offset // limit + 1,
            "pages": (total + limit - 1) // limit
        }

    except ValueError:
        raise HTTPException(400, "Invalid date format")
