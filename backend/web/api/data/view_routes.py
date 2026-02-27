from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, defer
from sqlalchemy import desc, asc, or_
from sqlalchemy.exc import ProgrammingError, OperationalError
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
        'fao_participant_oi': models.FAOParticipantOI,
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
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = Query('asc', pattern='^(asc|desc)$'),
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List data for a specific type with filters and optional sorting.
    """
    logger.info(f"View Request: type={type}, symbol={symbol}, date={start_date} to {end_date}, sort={sort_by} {sort_order}")

    model = get_model_for_type(type)
    if not model:
        logger.error(f"Invalid data type requested: {type}")
        raise HTTPException(status_code=400, detail=f"Invalid data type: {type}")

    query = db.query(model)

    # Apply Symbol/Search Filter (if applicable)
    filters = []
    if symbol:
        symbol = symbol.upper().strip()

        # Comprehensive Filtering Logic
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

    # Sorting Logic
    order_clauses = []

    if sort_by:
        # Custom sort requested
        if hasattr(model, sort_by):
            col = getattr(model, sort_by)
            order_clauses.append(desc(col) if sort_order == 'desc' else asc(col))
    else:
        # Default Sorting: Date DESC, then Symbol ASC
        if date_col:
            order_clauses.append(desc(date_col))

        # Determine symbol column for secondary sort
        sym_col = None
        if hasattr(model, 'symbol'): sym_col = model.symbol
        elif hasattr(model, 'ticker_symb'): sym_col = model.ticker_symb
        elif hasattr(model, 'underlying_stock'): sym_col = model.underlying_stock
        elif hasattr(model, 'security_name'): sym_col = model.security_name

        if sym_col:
            order_clauses.append(asc(sym_col))

        if not date_col and hasattr(model, 'updated_at'):
             order_clauses.append(desc(model.updated_at))

    if order_clauses:
        query = query.order_by(*order_clauses)

    try:
        results = query.limit(limit).all()
        logger.info(f"Query returned {len(results)} rows for {type}")
        return process_results(results, model)

    except (ProgrammingError, OperationalError) as e:
        # Catch missing column errors (e.g. instrument_type in bhavcopy_fo)
        err_msg = str(e)
        logger.error(f"Database Error for {type}: {err_msg}")

        # Explicit rollback required for Postgres transaction errors
        db.rollback()

        # Robust Fallback for known missing column issues
        if "instrument_type" in err_msg and hasattr(model, 'instrument_type'):
            logger.warning(f"Retrying query for {type} without 'instrument_type' column")
            try:
                # Retry query deferring the missing column
                # Re-build query since the previous transaction is dead
                query = db.query(model)
                if filters:
                    if len(filters) > 1: query = query.filter(or_(*filters))
                    else: query = query.filter(filters[0])

                if date_col:
                    if start_date: query = query.filter(date_col >= start_date)
                    if end_date: query = query.filter(date_col <= end_date)

                if order_clauses:
                    query = query.order_by(*order_clauses)

                query = query.options(defer(model.instrument_type))
                results = query.limit(limit).all()
                return process_results(results, model, skip_instrument_type=True)
            except Exception as retry_exc:
                logger.error(f"Retry failed: {retry_exc}")
                raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def process_results(results, model, skip_instrument_type=False):
    """Serialize and normalize results."""
    data = []
    for row in results:
        # Convert row to dict, handling dates and serialization
        row_dict = {}
        for col in row.__table__.columns:
            # Skip deferred columns if they are not loaded (though accessing them usually triggers load,
            # here we want to avoid accessing them if we know they are missing in DB)
            if skip_instrument_type and col.name == 'instrument_type':
                continue

            val = getattr(row, col.name)
            if isinstance(val, (datetime, pd.Timestamp)):
                val = val.isoformat()
            elif hasattr(val, 'isoformat'): # date
                val = val.isoformat()
            row_dict[col.name] = val

        # Normalization for frontend consistency
        if 'ticker_symb' in row_dict and 'symbol' not in row_dict:
            row_dict['symbol'] = row_dict['ticker_symb']

        # Ensure instrument_type is present and valid
        # If we skipped it (because DB lacks it) or it's None, fill it
        if skip_instrument_type or ('instrument_type' in row_dict and not row_dict['instrument_type']):
             # Heuristic: Infer instrument_type if missing (e.g. legacy data or import issue)
             # This ensures frontend grid (which filters by Type) shows the data
             symbol = row_dict.get('ticker_symb', row_dict.get('symbol', ''))
             option_type = row_dict.get('option_type', '')

             is_index = symbol in ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY']
             is_opt = option_type in ['CE', 'PE']

             if is_index:
                 row_dict['instrument_type'] = 'OPTIDX' if is_opt else 'FUTIDX'
             else:
                 # Default to Stock if not index.
                 # Note: This is a fallback. Actual data usually has explicit type.
                 row_dict['instrument_type'] = 'OPTSTK' if is_opt else 'FUTSTK'

        elif 'instrument_type' not in row_dict:
             # If model doesn't have it at all (unlikely for FO), do nothing or add default?
             pass

        if 'underlying_stock' in row_dict and 'symbol' not in row_dict:
            row_dict['symbol'] = row_dict['underlying_stock']

        # Alias instrument_type to FinInstrmTp for Bhavcopy FO if requested by user convention
        if model.__tablename__ == 'bhavcopy_fo' and 'instrument_type' in row_dict:
            row_dict['FinInstrmTp'] = row_dict['instrument_type']

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
    type: str = Query(..., description="Data type (bhavcopy_eq, bhavcopy_fo, etc.)"),
    symbol: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Export filtered data to CSV (Server-side streaming).
    """
    logger.info(f"Export Request: type={type}, symbol={symbol}, date={start_date} to {end_date}")

    model = get_model_for_type(type)
    if not model:
        raise HTTPException(status_code=400, detail=f"Invalid data type: {type}")

    query = db.query(model)

    # Re-use filtering logic (copied from list_data for now to keep independent)
    filters = []
    if symbol:
        symbol = symbol.upper().strip()

        if hasattr(model, 'symbol'): filters.append(model.symbol == symbol)
        if hasattr(model, 'ticker_symb'): filters.append(model.ticker_symb == symbol)
        if hasattr(model, 'underlying_stock'): filters.append(model.underlying_stock == symbol)
        if hasattr(model, 'security_name'): filters.append(model.security_name.ilike(f"%{symbol}%"))
        if hasattr(model, 'client_type'): filters.append(model.client_type.ilike(f"%{symbol}%"))
        if hasattr(model, 'instrument_type'): filters.append(model.instrument_type.ilike(f"%{symbol}%"))
        if hasattr(model, 'isin'): filters.append(model.isin == symbol)
        if hasattr(model, 'fin_instrm_id'): filters.append(model.fin_instrm_id == symbol)

        if filters:
            if len(filters) > 1: query = query.filter(or_(*filters))
            else: query = query.filter(filters[0])

    date_col = getattr(model, 'trade_date', getattr(model, 'date', None))
    if date_col:
        if start_date: query = query.filter(date_col >= start_date)
        if end_date: query = query.filter(date_col <= end_date)

        # Order by date desc, then symbol asc (if available)
        order_clauses = [desc(date_col)]
        if hasattr(model, 'symbol'):
            order_clauses.append(model.symbol.asc())
        elif hasattr(model, 'ticker_symb'):
            order_clauses.append(model.ticker_symb.asc())
        elif hasattr(model, 'underlying_stock'):
            order_clauses.append(model.underlying_stock.asc())
        elif hasattr(model, 'security_name'):
            order_clauses.append(model.security_name.asc())

        query = query.order_by(*order_clauses)
    elif hasattr(model, 'updated_at'):
        query = query.order_by(desc(model.updated_at))

    # Fetch all matching records (or limit to reasonable export size e.g. 50k)
    try:
        results = query.limit(50000).all()
        # Process results with potential instrument_type fix
        data = process_results(results, model)

    except (ProgrammingError, OperationalError) as e:
        # Catch missing column errors (e.g. instrument_type in bhavcopy_fo)
        err_msg = str(e)
        logger.error(f"Export Database Error for {type}: {err_msg}")

        # Explicit rollback
        db.rollback()

        # Robust Fallback for known missing column issues
        if "instrument_type" in err_msg and hasattr(model, 'instrument_type'):
            logger.warning(f"Retrying export for {type} without 'instrument_type' column")
            try:
                # Re-build query since the previous transaction is dead
                query = db.query(model)
                if filters:
                    if len(filters) > 1: query = query.filter(or_(*filters))
                    else: query = query.filter(filters[0])

                if date_col:
                    if start_date: query = query.filter(date_col >= start_date)
                    if end_date: query = query.filter(date_col <= end_date)

                if hasattr(model, 'updated_at') and not date_col:
                    query = query.order_by(desc(model.updated_at))
                elif date_col:
                    query = query.order_by(*order_clauses)

                query = query.options(defer(model.instrument_type))
                results = query.limit(50000).all()
                data = process_results(results, model, skip_instrument_type=True)
            except Exception as retry_exc:
                logger.error(f"Export retry failed: {retry_exc}")
                raise HTTPException(status_code=500, detail=f"Database error during export: {str(e)}")
        else:
             raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    if not data:
        raise HTTPException(status_code=404, detail="No data found for export")

    df = pd.DataFrame(data)

    # CSV Export
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)

    filename = f"{type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
