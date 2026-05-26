from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import re
import requests
from datetime import datetime, time
import pandas as pd
from backend.infrastructure.db import get_db
from backend.ingest.nse_models import BoardMeeting

router = APIRouter()

from fastapi import File, Form, UploadFile

class OverrideXMLRequest(BaseModel):
    symbol: str
    meeting_date: str
    xml_url: str

@router.post("/override-xml")
def override_board_meeting_xml(
    symbol: str = Form(...),
    meeting_date: str = Form(...),
    xml_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Allows a user to manually pass a URL to an XBRL XML file (like the one found
    on the NSE portal for specific outcomes) to override a specific Board Meeting's
    extracted amounts, record dates, and broadcast times.
    """
    try:
        meeting_date_obj = datetime.strptime(meeting_date, "%d-%b-%Y").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use DD-MMM-YYYY")

    bm = db.query(BoardMeeting).filter(
        BoardMeeting.symbol == symbol.upper(),
        BoardMeeting.meeting_date == meeting_date_obj
    ).first()

    if not bm:
        raise HTTPException(status_code=404, detail="Board meeting not found in database for the given symbol and date.")

    # Fetch XML content
    xml_text = ""
    if file:
        xml_text = file.file.read().decode("utf-8")
    elif xml_url:
        if not xml_url.startswith("http"):
            raise HTTPException(status_code=400, detail="Only HTTP/HTTPS URLs are supported for security reasons.")
        try:
            headers = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'accept-language': 'en-US,en;q=0.9',
            }
            resp = requests.get(xml_url, headers=headers, timeout=10)
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Failed to fetch XML URL. HTTP Status: {resp.status_code}")
            xml_text = resp.text
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error fetching remote XML: {e}")
    else:
        raise HTTPException(status_code=400, detail="Either xml_url or an uploaded file must be provided.")

    # Parse the XML exactly like nse_lib.py does
    found_amount = None
    found_record_date = None
    found_start_time = None

    # Amount extraction
    xbrl_patterns = [
        r'<[^>]*:rateoffinaldividend[^>]*>.*?Rs\.?\s*(\d+(?:\.\d+)?).*?</[^>]*>',
        r'<[^>]*:RateOfFinalDividendRecommendedPerEquityShare[^>]*>\s*(\d+(?:\.\d+)?)\s*</[^>]*>',
        r'<[^>]*:rateofinterimdividend[^>]*>.*?Rs\.?\s*(\d+(?:\.\d+)?).*?</[^>]*>',
        r'<[^>]*:RateOfInterimDividendDeclaredPerEquityShare[^>]*>\s*(\d+(?:\.\d+)?)\s*</[^>]*>',
        r'<[^>]*:rateofspecialdividend[^>]*>.*?Rs\.?\s*(\d+(?:\.\d+)?).*?</[^>]*>',
        r'<[^>]*:RateOfSpecialDividendDeclaredPerEquityShare[^>]*>\s*(\d+(?:\.\d+)?)\s*</[^>]*>'
    ]
    for pat in xbrl_patterns:
        matches = re.findall(pat, xml_text, re.IGNORECASE)
        if matches:
            found_amount = sum(float(m) for m in matches)
            break

    # Record date extraction
    xbrl_rd_patterns = [
        r'<[^>]*:recorddateoffinaldividend[^>]*>\s*([^<]+)\s*</[^>]*>',
        r'<[^>]*:RecordDateOfFinalDividendRecommended[^>]*>\s*([^<]+)\s*</[^>]*>',
        r'<[^>]*:recorddateofinterimdividend[^>]*>\s*([^<]+)\s*</[^>]*>',
        r'<[^>]*:RecordDateOfInterimDividendDeclared[^>]*>\s*([^<]+)\s*</[^>]*>',
        r'<[^>]*:recorddateofspecialdividend[^>]*>\s*([^<]+)\s*</[^>]*>',
        r'<[^>]*:RecordDateOfSpecialDividendDeclared[^>]*>\s*([^<]+)\s*</[^>]*>'
    ]
    for pat in xbrl_rd_patterns:
        rd_match = re.search(pat, xml_text, re.IGNORECASE)
        if rd_match:
            found_record_date = rd_match.group(1).strip()
            break

    # Time extraction - start time or end time
    time_match = re.search(r'<[^>]*:StartTimeOfBoardMeetingForAnnouncementOfDividend[^>]*>\s*([^<]+)\s*</[^>]*>', xml_text, re.IGNORECASE)
    if time_match:
        found_start_time = time_match.group(1).strip()
    else:
        time_match2 = re.search(r'<[^>]*:EndTimeOfBoardMeetingForAnnouncementOfDividend[^>]*>\s*([^<]+)\s*</[^>]*>', xml_text, re.IGNORECASE)
        if time_match2:
            found_start_time = time_match2.group(1).strip()

    # Apply updates
    updates_made = []

    if found_amount is not None:
        bm.extracted_dividend_amount = float(found_amount)
        updates_made.append(f"Amount: {found_amount}")

    if found_record_date:
        try:
            rd_obj = pd.to_datetime(found_record_date).date()
            bm.record_date = rd_obj
            updates_made.append(f"Record Date: {found_record_date}")
        except:
            updates_made.append(f"Failed to parse Record Date format: {found_record_date}")

    if found_start_time:
        # Re-attach exact time to broadcast_date so the front-end timeline can respect market hours correctly
        try:
            # Assumes formats like '19:00:00'
            time_parts = found_start_time.split(":")
            if len(time_parts) >= 2:
                hr = int(time_parts[0])
                mn = int(time_parts[1])
                sc = int(time_parts[2]) if len(time_parts) == 3 else 0
                time_obj = time(hr, mn, sc)
                combined_dt = datetime.combine(bm.meeting_date, time_obj)
                bm.broadcast_date = combined_dt
                updates_made.append(f"Time updated to: {combined_dt}")
        except Exception as e:
            updates_made.append(f"Failed to parse Time format {found_start_time}: {e}")

    db.commit()

    return {
        "status": "success",
        "message": f"Successfully processed manual override.",
        "updates": updates_made,
        "meeting_date": str(bm.meeting_date),
        "amount": bm.extracted_dividend_amount,
        "record_date": str(bm.record_date),
        "broadcast_date": str(bm.broadcast_date)
    }
