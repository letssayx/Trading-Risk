from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.infrastructure.db import get_db

router = APIRouter()

@router.get("/api/data/derivatives/pcr_history")
async def get_pcr_history(symbol: str, days: int = 500, db: Session = Depends(get_db)):
    try:
        symbol = symbol.upper()
        query = text("""
            WITH fut_price AS (
                SELECT
                    trade_date,
                    close_price as fut_close,
                    ROW_NUMBER() OVER (PARTITION BY trade_date ORDER BY expiry_date ASC) as rn
                FROM bhavcopy_fo
                WHERE ticker_symb = :symbol
                  AND instrument_type IN ('FUTIDX', 'FUTSTK', 'STF', 'IDF')
                  AND expiry_date >= trade_date
            ),
            fut_oi AS (
                SELECT
                    trade_date,
                    SUM(open_interest) as total_fut_oi
                FROM bhavcopy_fo
                WHERE ticker_symb = :symbol
                  AND instrument_type IN ('FUTIDX', 'FUTSTK', 'STF', 'IDF')
                GROUP BY trade_date
            ),
            opt_data AS (
                SELECT
                    b.trade_date,
                    SUM(CASE WHEN b.option_type = 'CE' THEN b.open_interest ELSE 0 END) as total_ce_oi,
                    SUM(CASE WHEN b.option_type = 'PE' THEN b.open_interest ELSE 0 END) as total_pe_oi,
                    -- Delta weighted OI: Option OI * Absolute Delta
                    -- We use absolute delta for puts as well to represent total exposure magnitude
                    -- STRICT MATH: No fallback COALESCE to 0.5. Missing delta = 0 delta-weighted OI.
                    SUM(b.open_interest * COALESCE(ABS(c.delta), 0)) as delta_weighted_opt_oi
                FROM bhavcopy_fo b
                LEFT JOIN contract_delta c ON b.ticker_symb = c.symbol
                    AND b.trade_date = c.date
                    AND b.expiry_date = c.expiry_date
                    AND b.strike_price = c.strike_price
                    AND b.option_type = c.option_type
                WHERE b.ticker_symb = :symbol
                  AND b.instrument_type IN ('OPTIDX', 'OPTSTK', 'STO', 'IDO')
                GROUP BY b.trade_date
            )
            SELECT
                o.trade_date,
                f.fut_close,
                o.total_ce_oi,
                o.total_pe_oi,
                (COALESCE(foi.total_fut_oi, 0) + COALESCE(o.delta_weighted_opt_oi, 0)) as total_oi,
                CASE WHEN o.total_ce_oi > 0 THEN CAST(o.total_pe_oi AS FLOAT) / o.total_ce_oi ELSE 0 END as pcr
            FROM opt_data o
            JOIN fut_price f ON o.trade_date = f.trade_date AND f.rn = 1
            LEFT JOIN fut_oi foi ON o.trade_date = foi.trade_date
            ORDER BY o.trade_date DESC
            LIMIT :days
        """)

        result = db.execute(query, {"symbol": symbol, "days": days}).fetchall()

        # Sort back to ascending for charting
        result = sorted(result, key=lambda x: x[0])

        return {
            "dates": [r[0].strftime('%Y-%m-%d') for r in result],
            "price": [float(r[1]) for r in result],
            "ce_oi": [int(r[2]) for r in result],
            "pe_oi": [int(r[3]) for r in result],
            "total_oi": [int(r[4]) for r in result],
            "pcr": [float(r[5]) for r in result]
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
