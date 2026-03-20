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
import traceback
import json

from backend.nselib.lib import NseSession

logger = logging.getLogger(__name__)

router = APIRouter()

# Share a single NseSession instance for proxying
_nse_session = None
def get_nse_session():
    global _nse_session
    if _nse_session is None:
        _nse_session = NseSession()
    return _nse_session

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
        'pe_ratio_idx': models.IndexPERatio,
        'india_vix': models.IndiaVIX,
        'var_stats': models.VaRStat,
        'contract_delta': models.ContractDelta,
        'margin_trading': models.MarginTrading,
        'fii_dii_cash': models.FIIDIICash,
        'security_master': models.SecurityMaster,
        'historical_index_data': models.HistoricalIndexData,
        'auctions': models.Auction, # Added auctions just in case
        'historical_index_data': models.HistoricalIndexData
    }
    # Safely get CorporateAction if it exists in models (may be unmerged)
    if data_type in ['corporate_actions', 'dividend'] and hasattr(models, 'CorporateAction'):
        return getattr(models, 'CorporateAction')
    if data_type in ['board_meetings', 'board_meeting'] and hasattr(models, 'BoardMeeting'):
        return getattr(models, 'BoardMeeting')

    return mapping.get(data_type)

import requests

@router.get("/api/proxy/rights")
def proxy_rights():
    """Fetches Rights Issues directly from NSE API endpoint."""
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    all_data = []
    seen_ids = set()

    try:
        session.get("https://www.nseindia.com", headers=headers, timeout=10) # Prime

        url_listing = "https://www.nseindia.com/api/corporate-further-issues-ri"
        res_listing = session.get(url_listing, headers=headers, timeout=10)
        if res_listing.ok:
            data = res_listing.json().get('data', [])
            for item in data:
                if item.get('appId') not in seen_ids:
                    all_data.append(item)
                    seen_ids.add(item.get('appId'))

        url_in_principle = "https://www.nseindia.com/api/corporate-further-issues-ri?index=FIRIIP"
        res_in_principle = session.get(url_in_principle, headers=headers, timeout=10)
        if res_in_principle.ok:
            data = res_in_principle.json().get('data', [])
            for item in data:
                if item.get('appId') not in seen_ids:
                    all_data.append(item)
                    seen_ids.add(item.get('appId'))
    except Exception as e:
        logger.error(f"Failed to fetch Rights. Error: {e}")

    return {"data": all_data}


@router.get("/api/proxy/public-issues")
def proxy_public_issues():
    """Fetches Rights, OFS, and Tender Issues from NSE API endpoints."""
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    all_data = []
    seen_ids = set()

    try:
        session.get("https://www.nseindia.com", headers=headers, timeout=10)

        # The user requested no fallbacks. They just want the explicit pages.
        # Since OFS/Tender might be empty, we just query them. If they 404, we return empty.
        endpoints = {
            'rights': "https://www.nseindia.com/api/corporate-further-issues-rits?index=equities",
            'ofs': "https://www.nseindia.com/api/corporate-further-issues-ofs?index=equities",
            'tender': "https://www.nseindia.com/api/corporate-further-issues-tender?index=equities"
        }

        for issue_type, url in endpoints.items():
            try:
                res = session.get(url, headers=headers, timeout=10)
                if res.ok:
                    data = res.json()
                    items = data if isinstance(data, list) else data.get('data', [])
                    for item in items:
                        uid = item.get('appId') or f"{item.get('symbol', '')}_{item.get('date', '')}"
                        if uid not in seen_ids:
                            item['issue_type'] = issue_type
                            all_data.append(item)
                            if uid:
                                seen_ids.add(uid)
            except Exception as e:
                logger.warning(f"Failed to fetch exact {issue_type}: {e}.")

    except Exception as e:
        logger.error(f"Failed to prime session for Public Issues. Error: {e}")

    return {"data": all_data}

@router.get("/api/proxy/announcements")
def proxy_announcements():
    """Fetches Corporate Announcements."""
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    try:
        session.get("https://www.nseindia.com", headers=headers, timeout=10)
        url = "https://www.nseindia.com/api/corporate-announcements?index=equities"
        res = session.get(url, headers=headers, timeout=10)
        if res.ok:
            return res.json()
    except Exception as e:
        logger.error(f"Failed to fetch Announcements: {e}")
    return {"data": []}

@router.get("/api/proxy/event-calendar")
def proxy_event_calendar():
    """Fetches Corporate Event Calendar."""
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    try:
        session.get("https://www.nseindia.com", headers=headers, timeout=10)
        url = "https://www.nseindia.com/api/event-calendar"
        res = session.get(url, headers=headers, timeout=10)
        if res.ok:
            # Event calendar might return raw list
            data = res.json()
            if isinstance(data, list):
                return {"data": data}
            return data
    except Exception as e:
        logger.error(f"Failed to fetch Event Calendar: {e}")
    return {"data": []}

@router.get("/api/proxy/circulars")
def proxy_circulars(db: Session = Depends(get_db)):
    """Fetches Exchange Circulars from local DB first, then scrapes if missing and saves."""
    from backend.ingest.nse_models import ExchangeCircular
    from datetime import date

    # 1. Fetch from DB
    db_records = db.query(ExchangeCircular).order_by(ExchangeCircular.trade_date.desc()).limit(100).all()
    if db_records:
        data = []
        for r in db_records:
            data.append({
                "circDate": r.trade_date.strftime("%d-%b-%Y"),
                "circNo": r.circular_no,
                "sub": r.subject,
                "circDepartment": r.department,
                "circFile": r.link
            })
        return {"data": data}

    # 2. If DB is empty, proxy and save (Seed Data)
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    response = None
    try:
        session.get("https://www.nseindia.com", headers=headers, timeout=10) # Prime
        url = "https://www.nseindia.com/api/circulars"
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        json_data = response.json()

        # Save to DB
        items = json_data.get('data', [])
        for item in items:
            try:
                dt_str = item.get('cirDate') or item.get('circDate')
                from datetime import datetime
                parsed_date = datetime.strptime(dt_str, "%d-%b-%Y").date() if dt_str else date.today()

                circ = ExchangeCircular(
                    trade_date=parsed_date,
                    circular_no=item.get('circNumber') or item.get('circNo') or 'UNKNOWN',
                    subject=item.get('sub') or item.get('subject'),
                    department=item.get('circDepartment') or item.get('department'),
                    link=item.get('circFilelink') or item.get('circFile')
                )
                db.add(circ)
            except Exception as e:
                db.rollback() # reset failed transaction if duplicate
                pass # skip duplicates or parsing errors
        db.commit()
        return json_data
    except Exception as e:
        status = getattr(response, 'status_code', 'N/A') if response else 'N/A'
        body = getattr(response, 'text', 'N/A') if response else 'N/A'
        logger.error(f"Failed to fetch Circulars. Status: {status}, Body: {body}, Error: {e}")
        return {"data": []}

@router.get("/api/proxy/board-meetings")
def proxy_board_meetings():
    """Fetches Board Meetings directly from NSE API endpoint."""
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    response = None
    try:
        session.get("https://www.nseindia.com", headers=headers, timeout=10) # Prime
        url = "https://www.nseindia.com/api/corporate-board-meetings?index=equities"
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        status = getattr(response, 'status_code', 'N/A') if response else 'N/A'
        body = getattr(response, 'text', 'N/A') if response else 'N/A'
        logger.error(f"Failed to fetch Board Meetings. Status: {status}, Body: {body}, Error: {e}")
        return {"data": []}

@router.get("/api/proxy/corporate-actions")
def proxy_corporate_actions():
    """Fetches Corporate Actions directly from NSE API endpoint."""
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    response = None
    try:
        session.get("https://www.nseindia.com", headers=headers, timeout=10) # Prime
        url = "https://www.nseindia.com/api/corporates-corporateActions?index=equities"
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        status = getattr(response, 'status_code', 'N/A') if response else 'N/A'
        body = getattr(response, 'text', 'N/A') if response else 'N/A'
        logger.error(f"Failed to fetch Corporate Actions. Status: {status}, Body: {body}, Error: {e}")
        return {"data": []}


@router.delete("/api/data/view/range")
async def delete_data_range(
    type: str = Query(..., description="Data type"),
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Delete data and import logs for a given data type and date range."""
    model = get_model_for_type(type)
    if not model:
        raise HTTPException(status_code=400, detail=f"Invalid data type: {type}")

    try:
        s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        e_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Dates must be in YYYY-MM-DD format")

    try:
        # 1. Determine the date column name in the model
        date_col = getattr(model, 'date', getattr(model, 'trade_date', None))
        table_name = model.__tablename__

        def execute_delete():
            if not date_col:
                if type == 'security_master':
                    # Security master doesn't have date filtering. Delete all.
                    deleted_count = db.query(model).delete(synchronize_session=False)
                    logs_deleted = db.query(models.ImportLog).filter(
                        models.ImportLog.table_name == 'nse_security'
                    ).delete(synchronize_session=False)
                else:
                    raise HTTPException(status_code=400, detail=f"Model {type} does not have a recognizable date column")
            else:
                # 2. Delete data by date range
                deleted_count = db.query(model).filter(
                    date_col >= s_date,
                    date_col <= e_date
                ).delete(synchronize_session=False)

                # 3. Delete from import_logs
                logs_deleted = db.query(models.ImportLog).filter(
                    models.ImportLog.table_name == table_name,
                    models.ImportLog.import_date >= s_date,
                    models.ImportLog.import_date <= e_date
                ).delete(synchronize_session=False)

            db.commit()
            return deleted_count, logs_deleted

        from fastapi.concurrency import run_in_threadpool
        deleted_count, logs_deleted = await run_in_threadpool(execute_delete)

        logger.info(f"Deleted {deleted_count} rows from {table_name} and {logs_deleted} logs between {s_date} and {e_date}")
        return {
            "status": "success",
            "message": f"Deleted {deleted_count} records and {logs_deleted} logs for {type}",
            "records_deleted": deleted_count,
            "logs_deleted": logs_deleted
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting data range: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/data/view/list")
async def list_data(
    type: str = Query(..., description="Data type (bhavcopy, participant_oi, etc.)"),
    symbol: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    instrument: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = Query('asc', pattern='^(asc|desc)$'),
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List data for a specific type with filters and optional sorting.
    """
    logger.info(f"View Request: type={type}, symbol={symbol}, instrument={instrument}, date={start_date} to {end_date}, sort={sort_by} {sort_order}")

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
        if hasattr(model, 'instrument_type') and type != 'bhavcopy_fo':
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

    if type == 'dividend':
        query = query.filter(or_(
            model.parsed_dividend_amount != None,
            model.dividend_type.in_(['Bonus', 'Split'])
        ))

    # Handle FO Instrument filter
    if type == 'bhavcopy_fo' and instrument and instrument.upper() != 'ALL':
        inst_upper = instrument.upper()
        if 'FUT' in inst_upper:
            # Match old (FUTIDX, FUTSTK) and new (STF, IDF, FUTIVX) formats
            query = query.filter(model.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK', 'FUTIVX', 'FUTIRC']))
        elif 'OPT' in inst_upper:
            # Match old (OPTIDX, OPTSTK) and new (STO, IDO, OPTIRC) formats
            query = query.filter(model.instrument_type.in_(['STO', 'IDO', 'OPTIDX', 'OPTSTK', 'OPTIRC']))
        else:
            query = query.filter(model.instrument_type.like(f"%{inst_upper}%"))

    # Apply Date Filter
    date_col = getattr(model, 'trade_date', getattr(model, 'date', None))

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

    def execute_query():
        try:
            results = query.limit(limit).all()

            if not results and (start_date or end_date):
                 # Debugging: If no results with date filter, check total count for diagnostics
                 total_count = db.query(model).count()
                 logger.warning(f"Query returned 0 rows for {type} with date filter. Total rows in table: {total_count}")
            else:
                 logger.info(f"Query returned {len(results)} rows for {type}")

            return process_results(results, model)

        except (ProgrammingError, OperationalError) as e:
            # Catch missing column errors (e.g. instrument_type in bhavcopy_fo)
            err_msg = str(e)
            logger.error(f"Database Error for {type}: {err_msg}\n{traceback.format_exc()}")
            db.rollback()

            # Robust Fallback for known missing column issues
            if "instrument_type" in err_msg and hasattr(model, 'instrument_type'):
                logger.warning(f"Retrying query for {type} without 'instrument_type' column")
                try:
                    # Retry logic similar to above...
                    retry_query = db.query(model)
                    if filters:
                        if len(filters) > 1: retry_query = retry_query.filter(or_(*filters))
                        else: retry_query = retry_query.filter(filters[0])
                    if date_col:
                        if start_date: retry_query = retry_query.filter(date_col >= start_date)
                        if end_date: retry_query = retry_query.filter(date_col <= end_date)
                    if order_clauses:
                        retry_query = retry_query.order_by(*order_clauses)

                    retry_query = retry_query.options(defer(model.instrument_type))
                    results = retry_query.limit(limit).all()
                    return process_results(results, model, skip_instrument_type=True)
                except Exception as retry_exc:
                    logger.error(f"Retry failed: {retry_exc}")
                    raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

        except Exception as e:
            # Catch unexpected errors
            logger.error(f"Unexpected error listing data for {type}: {e}\n{traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

    from fastapi.concurrency import run_in_threadpool
    return await run_in_threadpool(execute_query)


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

@router.get("/api/data/view/symbols/all")
async def all_symbols(db: Session = Depends(get_db)):
    """
    Returns all distinct symbols from bhavcopy_eq for client-side autocomplete.
    """
    from backend.ingest.nse_models import BhavcopyEQ
    from sqlalchemy import select

    query = select(BhavcopyEQ.symbol).distinct()
    results = db.execute(query).scalars().all()

    return {"symbols": results}


@router.get("/api/data/view/symbols/autocomplete")
async def autocomplete_symbols(
    q: str = Query(..., min_length=2),
    db: Session = Depends(get_db)
):
    """
    Fast autocomplete endpoint for the AI-Analyze command bar.
    Searches SecurityMaster for matching symbols or company names.
    """
    from backend.ingest.nse_models import SecurityMaster
    from sqlalchemy import func, or_, select

    q_upper = q.upper().strip()

    # Prioritize exact symbol matches first, then partial symbol, then name
    query = select(SecurityMaster.ticker_symb, SecurityMaster.instrument_name).filter(
        or_(
            func.upper(SecurityMaster.ticker_symb).like(f"{q_upper}%"),
            func.upper(SecurityMaster.instrument_name).like(f"%{q_upper}%")
        )
    ).limit(10)

    results = db.execute(query).all()

    data = []
    seen = set()
    for row in results:
        if row.ticker_symb not in seen:
            data.append({
                "symbol": row.ticker_symb,
                "name": row.instrument_name or ""
            })
            seen.add(row.ticker_symb)

    # If no results found in SecurityMaster, try distinct from BhavcopyEQ as fallback
    if not data:
        from backend.ingest.nse_models import BhavcopyEQ
        bc_query = select(BhavcopyEQ.symbol).filter(
            func.upper(BhavcopyEQ.symbol).like(f"{q_upper}%")
        ).distinct().limit(5)

        bc_results = db.execute(bc_query).scalars().all()
        for sym in bc_results:
            if sym not in seen:
                data.append({
                    "symbol": sym,
                    "name": "Historical Symbol"
                })
                seen.add(sym)

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
    instrument: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Export filtered data to CSV (Server-side streaming).
    """
    logger.info(f"Export Request: type={type}, symbol={symbol}, date={start_date} to {end_date}, instrument={instrument}")

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
        if hasattr(model, 'instrument_type') and type != 'bhavcopy_fo': filters.append(model.instrument_type.ilike(f"%{symbol}%"))
        if hasattr(model, 'isin'): filters.append(model.isin == symbol)
        if hasattr(model, 'fin_instrm_id'): filters.append(model.fin_instrm_id == symbol)

        if filters:
            if len(filters) > 1: query = query.filter(or_(*filters))
            else: query = query.filter(filters[0])

    if type == 'bhavcopy_fo' and instrument and instrument.upper() != 'ALL':
        inst_upper = instrument.upper()
        if 'FUT' in inst_upper:
            query = query.filter(model.instrument_type.in_(['STF', 'IDF', 'FUTIDX', 'FUTSTK', 'FUTIVX', 'FUTIRC']))
        elif 'OPT' in inst_upper:
            query = query.filter(model.instrument_type.in_(['STO', 'IDO', 'OPTIDX', 'OPTSTK', 'OPTIRC']))
        else:
            query = query.filter(model.instrument_type.like(f"%{inst_upper}%"))

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
    # If no date constraints are provided, fall back to limit to prevent OOM
    has_date_constraint = start_date is not None or end_date is not None

    def execute_export_query():
        try:
            if has_date_constraint:
                results = query.all()
            else:
                results = query.limit(50000).all()
            # Process results with potential instrument_type fix
            return process_results(results, model)

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
                    retry_query = db.query(model)
                    if filters:
                        if len(filters) > 1: retry_query = retry_query.filter(or_(*filters))
                        else: retry_query = retry_query.filter(filters[0])

                    if date_col:
                        if start_date: retry_query = retry_query.filter(date_col >= start_date)
                        if end_date: retry_query = retry_query.filter(date_col <= end_date)

                    if hasattr(model, 'updated_at') and not date_col:
                        retry_query = retry_query.order_by(desc(model.updated_at))
                    elif date_col:
                        retry_query = retry_query.order_by(*order_clauses)

                    retry_query = retry_query.options(defer(model.instrument_type))
                    if has_date_constraint:
                        results = retry_query.all()
                    else:
                        results = retry_query.limit(50000).all()
                    return process_results(results, model, skip_instrument_type=True)
                except Exception as retry_exc:
                    logger.error(f"Export retry failed: {retry_exc}")
                    raise HTTPException(status_code=500, detail=f"Database error during export: {str(e)}")
            else:
                 raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    from fastapi.concurrency import run_in_threadpool
    data = await run_in_threadpool(execute_export_query)

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


@router.get("/api/proxy/ofs")
def get_ofs():
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    try:
        session.get("https://www.nseindia.com", headers=headers, timeout=10)
        res = session.get("https://www.nseindia.com/api/corporate-further-issues-ofs?index=equities", headers=headers, timeout=10)
        data = res.json()
        return data if isinstance(data, list) else data.get("data", [])
    except Exception as e:
        return []

@router.get("/api/proxy/tender")
def get_tender():
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    try:
        session.get("https://www.nseindia.com", headers=headers, timeout=10)
        res = session.get("https://www.nseindia.com/api/corporate-further-issues-tender?index=equities", headers=headers, timeout=10)
        data = res.json()
        return data if isinstance(data, list) else data.get("data", [])
    except Exception as e:
        return []
