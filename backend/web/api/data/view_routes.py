from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, defer
from sqlalchemy import desc, asc, or_, func
from sqlalchemy.exc import ProgrammingError, OperationalError
import pandas as pd
import requests
import io
from datetime import datetime
from typing import Optional

from backend.infrastructure.db import get_db
from backend.domain.market.models import Bhavcopy
from backend.ingest import nse_models as models
import logging
import traceback

from backend.nselib.lib import NseSession

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/api/data/fundamentals")
def get_fundamentals(symbol: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    """Fetch fundamental placeholder data merged with latest actual price data."""
    try:
        from backend.ingest.nse_models import BhavcopyEQ
        from sqlalchemy import desc

        # Fetch latest price
        latest_eq = db.query(BhavcopyEQ).filter(BhavcopyEQ.symbol == symbol.upper()).order_by(desc(BhavcopyEQ.trade_date)).first()

        # We don't have a database table for fundamentals yet. The user wants to avoid fake data
        # so we will use Yahoo Finance as a temporary real data source until NSE is reliable.
        import yfinance as yf

        ticker = yf.Ticker(f"{symbol.upper()}.NS")
        info = ticker.info

        if not info or 'regularMarketPrice' not in info and 'currentPrice' not in info:
             # Fallback if no YF data found
             cmp = float(latest_eq.close_price) if latest_eq and latest_eq.close_price else 0.0
             prev_close = float(latest_eq.prev_close) if latest_eq and latest_eq.prev_close else cmp
             open_price = float(latest_eq.open_price) if latest_eq and latest_eq.open_price else cmp
             high_price = float(latest_eq.high_price) if latest_eq and latest_eq.high_price else cmp
             low_price = float(latest_eq.low_price) if latest_eq and latest_eq.low_price else cmp
             volume = float(latest_eq.total_traded_volume) if latest_eq and latest_eq.total_traded_volume else 0
             change = cmp - prev_close
             pct_change = (change / prev_close * 100) if prev_close else 0.0

             return {
                "symbol": symbol.upper(),
                "company_name": f"{symbol.upper()} LTD",
                "sector": "N/A",
                "cmp": cmp,
                "change": change,
                "pct_change": pct_change,
                "prev_close": prev_close,
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "volume": volume,
                "52w_high": 0,
                "52w_low": 0,
                "mcap_cr": 0,

                "pe_ratio": 0,
                "sector_pe": 0,
                "pb_ratio": 0,
                "div_yield": 0,
                "eps": 0,
                "roe": 0,
                "roce": 0,
                "debt_to_equity": 0,
                "book_value": 0,
                "face_value": 0,

                "promoter_holding": 0,
                "fii_holding": 0,
                "dii_holding": 0,
                "public_holding": 0,

                "date": latest_eq.trade_date.isoformat() if latest_eq else datetime.now().strftime("%Y-%m-%d")
             }

        cmp = info.get('currentPrice', info.get('regularMarketPrice', 0))
        prev_close = info.get('previousClose', 0)
        change = cmp - prev_close
        pct_change = (change / prev_close * 100) if prev_close else 0.0

        return {
            "symbol": symbol.upper(),
            "company_name": info.get('longName', f"{symbol.upper()} LTD"),
            "sector": info.get('sector', "General"),
            "cmp": cmp,
            "change": change,
            "pct_change": pct_change,
            "prev_close": prev_close,
            "open": info.get('open', 0),
            "high": info.get('dayHigh', 0),
            "low": info.get('dayLow', 0),
            "volume": info.get('volume', 0),
            "52w_high": info.get('fiftyTwoWeekHigh', 0),
            "52w_low": info.get('fiftyTwoWeekLow', 0),
            "mcap_cr": info.get('marketCap', 0) / 10000000 if info.get('marketCap') else 0, # Convert to Crores

            "pe_ratio": info.get('trailingPE', 0),
            "sector_pe": 0, # YF doesn't readily provide sector PE
            "pb_ratio": info.get('priceToBook', 0),
            "div_yield": info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
            "eps": info.get('trailingEps', 0),
            "roe": info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0,
            "roce": 0, # YF doesn't provide ROCE easily
            "debt_to_equity": info.get('debtToEquity', 0) / 100 if info.get('debtToEquity') else 0,
            "book_value": info.get('bookValue', 0),
            "face_value": 0, # YF doesn't provide face value

            "promoter_holding": info.get('heldPercentInsiders', 0) * 100 if info.get('heldPercentInsiders') else 0,
            "fii_holding": info.get('heldPercentInstitutions', 0) * 100 if info.get('heldPercentInstitutions') else 0,
            "dii_holding": 0, # Cannot reliably distinguish FII vs DII in YF
            "public_holding": 100 - (info.get('heldPercentInsiders', 0) * 100) - (info.get('heldPercentInstitutions', 0) * 100) if info.get('heldPercentInsiders') else 0,

            "date": datetime.now().strftime("%Y-%m-%d")
        }
    except Exception as e:
        logger.error(f"Error fetching fundamentals for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/data/live_price")
def get_live_price(symbol: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    """Fetch CMP and Futures price from the backend database."""
    try:
        from backend.ingest.nse_models import BhavcopyEQ, BhavcopyFO, HistoricalIndexData

        # 1. Fetch CMP from BhavcopyEQ
        latest_eq = db.query(BhavcopyEQ).filter(
            BhavcopyEQ.symbol == symbol.upper(),
            BhavcopyEQ.series == 'EQ'
        ).order_by(BhavcopyEQ.trade_date.desc()).first()

        db_cmp = latest_eq.close_price if latest_eq else 0.0

        # If CMP is 0, try fetching from HistoricalIndexData
        if db_cmp == 0.0:
            latest_idx = db.query(HistoricalIndexData).filter(
                HistoricalIndexData.index_name == symbol.upper()
            ).order_by(HistoricalIndexData.trade_date.desc()).first()
            if latest_idx:
                db_cmp = latest_idx.close_price

        # 2. Fetch Futures from BhavcopyFO
        near_fut = 0.0
        next_fut = 0.0
        far_fut = 0.0

        # We need the latest trade date in BhavcopyFO for this symbol to get active futures
        latest_fo_date_record = db.query(BhavcopyFO).filter(
            BhavcopyFO.ticker_symb == symbol.upper(),
            BhavcopyFO.instrument_type.in_(['FUTSTK', 'FUTIDX'])
        ).order_by(BhavcopyFO.trade_date.desc()).first()

        if latest_fo_date_record:
            latest_fo_date = latest_fo_date_record.trade_date
            futures = db.query(BhavcopyFO).filter(
                BhavcopyFO.ticker_symb == symbol.upper(),
                BhavcopyFO.trade_date == latest_fo_date,
                BhavcopyFO.instrument_type.in_(['FUTSTK', 'FUTIDX'])
            ).order_by(BhavcopyFO.expiry_date.asc()).limit(3).all()

            if len(futures) > 0: near_fut = futures[0].close_price
            if len(futures) > 1: next_fut = futures[1].close_price
            if len(futures) > 2: far_fut = futures[2].close_price

        return {
            "symbol": symbol.upper(),
            "price": db_cmp,
            "near_fut_price": near_fut,
            "next_fut_price": next_fut,
            "far_fut_price": far_fut
        }
    except Exception as e:
        logger.error(f"Error fetching price for {symbol}: {e}")
        return {
            "symbol": symbol.upper(),
            "price": 0,
            "near_fut_price": 0,
            "next_fut_price": 0,
            "far_fut_price": 0
        }


@router.get("/api/data/shareholding")
def get_shareholding(symbol: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    """Fetch live shareholding pattern data."""
    try:
        import requests
        import xml.etree.ElementTree as ET

        # Try fetching from NSE API first for absolute exact share counts
        url = f"https://www.nseindia.com/api/corporate-share-holdings-master?index=equities&symbol={symbol.upper()}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        session = requests.Session()
        session.get('https://www.nseindia.com', headers=headers, timeout=5)
        response = session.get(url, headers=headers, timeout=5)

        if response.status_code == 200:
            data = response.json()
            if data and isinstance(data, list):
                report_date = data[0].get('date', '')
                xbrl_url = data[0].get('xbrl')
                if xbrl_url:
                    res_xml = session.get(xbrl_url, headers=headers, timeout=5)
                    if res_xml.status_code == 200:
                        root = ET.fromstring(res_xml.text)
                        def get_shares(context_id):
                            # Try Demat form first
                            for elem in root:
                                tag_name = elem.tag.split('}')[-1]
                                if tag_name == 'NumberOfEquitySharesHeldInDematerializedForm' and elem.attrib.get('contextRef') == context_id:
                                    return float(elem.text)
                            # Fallback to fully paid up
                            for elem in root:
                                tag_name = elem.tag.split('}')[-1]
                                if tag_name == 'NumberOfFullyPaidUpEquityShares' and elem.attrib.get('contextRef') == context_id:
                                    return float(elem.text)
                            # Fallback to shares
                            for elem in root:
                                tag_name = elem.tag.split('}')[-1]
                                if tag_name == 'NumberOfShares' and elem.attrib.get('contextRef') == context_id:
                                    return float(elem.text)
                            return 0

                        promoter = get_shares('ShareholdingOfPromoterAndPromoterGroup_ContextI')
                        fii = get_shares('InstitutionsForeignPortfolioInvestorCategoryOne_ContextI') + get_shares('InstitutionsForeignPortfolioInvestorCategoryTwo_ContextI')
                        dii = get_shares('InstitutionsDomestic_ContextI') + get_shares('Governments_ContextI')
                        retail_less_200k = get_shares('ResidentIndividualShareholdersHoldingNominalShareCapitalUpToRsTwoLakh_ContextI')
                        public_gt_200k = get_shares('ResidentIndividualShareholdersHoldingNominalShareCapitalInExcessOfRsTwoLakh_ContextI')
                        if public_gt_200k == 0:
                            non_inst = get_shares('NonInstitutions_ContextI')
                            public_gt_200k = non_inst - retail_less_200k

                        adrs = get_shares('OverseasDepositories_ContextI')
                        others_trusts = get_shares('EmployeeBenefitsTrusts_ContextI')
                        total_out = get_shares('ShareholdingPattern_ContextI')

                        if total_out > 0:
                            promoter_holding = round((promoter/total_out)*100, 2)
                            fii_holding = round((fii/total_out)*100, 2)
                            dii_holding = round((dii/total_out)*100, 2)
                            retail_holding = round((retail_less_200k/total_out)*100, 2)
                            public_holding = round((public_gt_200k/total_out)*100, 2)
                            adr_holding = round((adrs/total_out)*100, 2)
                            others_holding = round((others_trusts/total_out)*100, 2)

                            return {
                                "symbol": symbol.upper(),
                                "report_date": report_date,
                                "promoter_holding": promoter_holding,
                                "fii_holding": fii_holding,
                                "dii_holding": dii_holding,
                                "retail_holding": retail_holding,
                                "public_holding": public_holding,
                                "adr_holding": adr_holding,
                                "others_holding": others_holding,
                                "total_outstanding": int(total_out),
                                "promoter_shares": int(promoter),
                                "fii_shares": int(fii),
                                "dii_shares": int(dii),
                                "retail_shares": int(retail_less_200k),
                                "public_shares": int(public_gt_200k),
                                "adr_shares": int(adrs),
                                "others_shares": int(others_trusts)
                            }
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="NSE shareholding fetch failed or no data returned. Fallbacks are disabled.")
    except Exception as e:
        from fastapi import HTTPException
        logger.error(f"Error fetching shareholding for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"NSE shareholding fetch error: {str(e)}")


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
    if data_type == 'dividend' and hasattr(models, 'DividendDatabank'):
        return getattr(models, 'DividendDatabank')
    if data_type == 'corporate_actions' and hasattr(models, 'CorporateAction'):
        return getattr(models, 'CorporateAction')
    if data_type in ['board_meetings', 'board_meeting'] and hasattr(models, 'BoardMeeting'):
        return getattr(models, 'BoardMeeting')

    return mapping.get(data_type)


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
            except Exception:
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
        date_col = None
        if hasattr(model, 'date'): date_col = model.date
        elif hasattr(model, 'trade_date'): date_col = model.trade_date
        elif hasattr(model, 'meeting_date'): date_col = model.meeting_date
        elif hasattr(model, 'ex_date'): date_col = model.ex_date

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


from backend.ingest.field_mapper import FieldMapper
from backend.ingest.nse_models import CorporateAction

@router.post("/api/data/dividends/patch")
def patch_historical_dividends(db: Session = Depends(get_db)):
    try:
        from sqlalchemy import or_
        # Fetch all corporate actions that likely contain dividends but haven't been parsed
        actions = db.query(CorporateAction).filter(
            CorporateAction.purpose != None,
            or_(CorporateAction.parsed_dividend_amount == None, CorporateAction.dividend_type.ilike('%special%'), CorporateAction.purpose.ilike('%special%')),
            or_(
                CorporateAction.purpose.ilike('%dividend%'),
                CorporateAction.purpose.ilike('%intdiv%'),
                CorporateAction.purpose.ilike('%int div%'),
                CorporateAction.purpose.ilike('%findiv%'),
                CorporateAction.purpose.ilike('%fin div%'),
                CorporateAction.purpose.ilike('%div-%'),
                CorporateAction.purpose.ilike('%div -%'),
                CorporateAction.purpose.ilike('% div %')
            )
        ).all()

        updated_count = 0
        for action in actions:
            if not action.purpose:
                continue

            # Attempt to parse
            amount, div_type = FieldMapper._parse_dividend(action.purpose, action.face_value)

            # Check if an update is needed
            needs_update = False
            if amount != action.parsed_dividend_amount:
                action.parsed_dividend_amount = amount
                needs_update = True

            if div_type and div_type != action.dividend_type:
                action.dividend_type = div_type
                needs_update = True

            if needs_update:
                updated_count += 1

        if updated_count > 0:
            db.commit()

            # Fire the background databank rebuild so these newly parsed amounts are actually visible in the UI
            from backend.ingest.tasks import build_dividend_databank_task
            build_dividend_databank_task.delay(force=False)

        return {"status": "success", "updated_count": updated_count}

    except Exception as e:
        db.rollback()
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
    latest: bool = Query(False),
    fo_only: Optional[bool] = False,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List data for a specific type with filters and optional sorting.
    """
    logger.info(f"View Request: type={type}, symbol={symbol}, instrument={instrument}, date={start_date} to {end_date}, sort={sort_by} {sort_order}, fo_only={fo_only}")

    model = get_model_for_type(type)
    if not model:
        logger.error(f"Invalid data type requested: {type}")
        raise HTTPException(status_code=400, detail=f"Invalid data type: {type}")

    query = db.query(model)

    if fo_only:
        from backend.ingest.nse_models import BhavcopyFO
        # Subquery to get distinct symbols from FO table
        fo_subquery = db.query(BhavcopyFO.ticker_symb).distinct().subquery()

        if hasattr(model, 'symbol'):
            query = query.filter(model.symbol.in_(db.query(fo_subquery)))
        elif hasattr(model, 'ticker_symb'):
            query = query.filter(model.ticker_symb.in_(db.query(fo_subquery)))
        elif hasattr(model, 'underlying_stock'):
            query = query.filter(model.underlying_stock.in_(db.query(fo_subquery)))


    # Handle Latest Data flag
    if latest:
        # Find the max date for this model
        if hasattr(model, 'date'):
            date_col = model.date
        elif hasattr(model, 'trade_date'):
            date_col = model.trade_date
        elif hasattr(model, 'board_meeting_date'):
             date_col = model.board_meeting_date
        elif hasattr(model, 'meeting_date'):
             date_col = model.meeting_date
        elif hasattr(model, 'ex_date'):
             date_col = model.ex_date
        else:
            date_col = None

        if date_col:
            max_date = db.query(func.max(date_col)).scalar()
            if max_date:
                # Override start and end dates
                start_date = max_date.strftime('%Y-%m-%d')
                end_date = max_date.strftime('%Y-%m-%d')

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
            if type == 'mto':
                # MTO often stores symbol as security_name or symbol format is mixed
                filters.append(model.security_name == symbol)

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
    # Add support for other date columns that were checked for max_date
    if date_col is None:
        if hasattr(model, 'board_meeting_date'):
            date_col = model.board_meeting_date
        elif hasattr(model, 'meeting_date'):
            date_col = model.meeting_date
        elif hasattr(model, 'ex_date'):
            date_col = model.ex_date

    if date_col is not None:
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
        if date_col is not None:
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
            if limit > 0:
                results = query.limit(limit).all()
            else:
                results = query.all()

            if not results and (start_date or end_date):
                 # Debugging: If no results with date filter, check total count for diagnostics
                 total_count = db.query(model).count()
                 logger.warning(f"Query returned 0 rows for {type} with date filter. Total rows in table: {total_count}")
            else:
                 logger.info(f"Query returned {len(results)} rows for {type}")

            if type == 'mwpl':
                from collections import defaultdict
                grouped = defaultdict(dict)
                max_clients = 0

                for row in results:
                    # Row is a SQLAlchemy model instance here
                    date_val = row.date.isoformat() if hasattr(row.date, 'isoformat') else str(row.date)
                    key = (date_val, row.underlying_stock)
                    client_num = row.client_position_num

                    grouped[key][f"Client {client_num}"] = row.position_pct
                    max_clients = max(max_clients, client_num)

                pivoted = []
                for (date, stock), positions in grouped.items():
                    row_dict = {
                        "Date": date,
                        "Underlying Stock": stock,
                    }
                    total = 0
                    for i in range(1, max_clients + 1):
                        client_key = f"Client {i}"
                        val = positions.get(client_key, None)
                        row_dict[client_key] = val
                        if val is not None:
                            total += val

                    row_dict["Total"] = round(total, 2)
                    pivoted.append(row_dict)

                # Sort by Date descending, then Total descending
                pivoted.sort(key=lambda x: (x["Date"], x["Total"]), reverse=True)

                # Add Sr No. after sort
                for idx, r in enumerate(pivoted, start=1):
                    r["Sr No."] = idx

                return pivoted

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
                    if limit > 0:
                        results = retry_query.limit(limit).all()
                    else:
                        results = retry_query.all()
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


import math

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
            if hasattr(val, 'strftime'):
                import datetime
                if isinstance(val, datetime.datetime):
                    val = val.strftime('%Y-%m-%dT%H:%M:%S')
                else:
                    val = val.strftime('%Y-%m-%d')
            elif isinstance(val, float):
                if math.isnan(val) or math.isinf(val):
                    val = None
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
    Returns all distinct symbols with company names from SymbolMaster, SecurityMaster, and bhavcopy_eq for client-side autocomplete.
    """
    from backend.ingest.nse_models import BhavcopyEQ, SymbolMaster, SecurityMaster
    from sqlalchemy import select

    symbols_list = []
    seen = set()

    def add_symbol_obj(sym, name):
        if sym and str(sym).strip() and sym not in seen:
            seen.add(sym)
            symbols_list.append({"symbol": sym, "name": name or ""})

    # Primary Source: User's Symbol Master
    try:
        sm_results = db.execute(select(SymbolMaster.symbol, SymbolMaster.company_name)).all()
        for row in sm_results:
            add_symbol_obj(row.symbol, row.company_name)
    except Exception as e:
        logger.warning(f"Could not load symbols from SymbolMaster: {e}")

    # Fallback Source: NSE Security Master
    try:
        sec_results = db.execute(select(SecurityMaster.ticker_symb, SecurityMaster.instrument_name)).all()
        for row in sec_results:
            add_symbol_obj(row.ticker_symb, row.instrument_name)
    except Exception as e:
        logger.warning(f"Could not load symbols from SecurityMaster: {e}")

    # Fallback Source: Bhavcopy EQ Distinct Symbols
    try:
        eq_results = db.execute(select(BhavcopyEQ.symbol).distinct()).scalars().all()
        for sym in eq_results:
            add_symbol_obj(sym, "")
    except Exception as e:
        logger.warning(f"Could not load symbols from BhavcopyEQ: {e}")

    return {"symbols": symbols_list}


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
    latest: bool = Query(False),
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

    # Handle Latest Data flag
    if latest:
        # Find the max date for this model
        if hasattr(model, 'date'):
            date_col = model.date
        elif hasattr(model, 'trade_date'):
            date_col = model.trade_date
        elif hasattr(model, 'board_meeting_date'):
             date_col = model.board_meeting_date
        elif hasattr(model, 'meeting_date'):
             date_col = model.meeting_date
        elif hasattr(model, 'ex_date'):
             date_col = model.ex_date
        else:
            date_col = None

        if date_col:
            max_date = db.query(func.max(date_col)).scalar()
            if max_date:
                # Override start and end dates
                start_date = max_date.strftime('%Y-%m-%d')
                end_date = max_date.strftime('%Y-%m-%d')

    # Re-use filtering logic (copied from list_data for now to keep independent)
    filters = []
    if symbol:
        symbol = symbol.upper().strip()

        if hasattr(model, 'symbol'): filters.append(model.symbol == symbol)
        if hasattr(model, 'ticker_symb'): filters.append(model.ticker_symb == symbol)
        if hasattr(model, 'underlying_stock'): filters.append(model.underlying_stock == symbol)
        if hasattr(model, 'security_name'):
            filters.append(model.security_name.ilike(f"%{symbol}%"))
            if type == 'mto':
                filters.append(model.security_name == symbol)
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
    if date_col is None:
        if hasattr(model, 'board_meeting_date'):
            date_col = model.board_meeting_date
        elif hasattr(model, 'meeting_date'):
            date_col = model.meeting_date
        elif hasattr(model, 'ex_date'):
            date_col = model.ex_date

    if date_col is not None:
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
                results = query.limit(100000).all() # Increase fallback export limit
            # Process results with potential instrument_type fix
            if type == 'mwpl':
                from collections import defaultdict
                grouped = defaultdict(dict)
                max_clients = 0

                for row in results:
                    # Row is a SQLAlchemy model instance here
                    date_val = row.date.isoformat() if hasattr(row.date, 'isoformat') else str(row.date)
                    key = (date_val, row.underlying_stock)
                    client_num = row.client_position_num

                    grouped[key][f"Client {client_num}"] = row.position_pct
                    max_clients = max(max_clients, client_num)

                pivoted = []
                for (date, stock), positions in grouped.items():
                    row_dict = {
                        "Date": date,
                        "Underlying Stock": stock,
                    }
                    total = 0
                    for i in range(1, max_clients + 1):
                        client_key = f"Client {i}"
                        val = positions.get(client_key, None)
                        row_dict[client_key] = val
                        if val is not None:
                            total += val

                    row_dict["Total"] = round(total, 2)
                    pivoted.append(row_dict)

                # Sort by Date descending, then Total descending
                pivoted.sort(key=lambda x: (x["Date"], x["Total"]), reverse=True)

                # Add Sr No. after sort
                for idx, r in enumerate(pivoted, start=1):
                    r["Sr No."] = idx

                return pivoted

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
    except Exception:
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
    except Exception:
        return []
