import re

def update_route():
    with open('backend/web/api/data/board_meeting_routes.py', 'r') as f:
        content = f.read()

    # Search pattern for the function signature
    old_sig = """def override_board_meeting_xml(
    symbol: str = Form(...),
    meeting_date: str = Form(...),
    xml_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):"""

    new_sig = """def override_board_meeting_xml(
    xml_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):"""

    content = content.replace(old_sig, new_sig)

    # Next, we need to extract xml_text BEFORE querying the DB
    # Find where the try block for meeting_date is, and replace it
    old_body_start = """    try:
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
        raise HTTPException(status_code=400, detail="Either xml_url or an uploaded file must be provided.")"""

    new_body_start = """    # Fetch XML content
    xml_text = ""
    if file:
        xml_text = file.file.read().decode("utf-8")
    elif xml_url:
        if not xml_url.startswith("http"):
            raise HTTPException(status_code=400, detail="Only HTTP/HTTPS URLs are supported for security reasons.")
        try:
            import requests
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

    # Extract symbol and date from XML
    symbol_match = re.search(r'<[^>]*:NSESymbol[^>]*>\s*([^<]+)\s*</[^>]*>', xml_text, re.IGNORECASE)
    date_match = re.search(r'<[^>]*:DateOfBoardMeeting[^>]*>\s*([^<]+)\s*</[^>]*>', xml_text, re.IGNORECASE)
    if not date_match:
        date_match = re.search(r'<[^>]*:DateOfReport[^>]*>\s*([^<]+)\s*</[^>]*>', xml_text, re.IGNORECASE)

    if not symbol_match or not date_match:
        raise HTTPException(status_code=400, detail="Could not extract NSESymbol or Meeting Date from the XML.")

    symbol = symbol_match.group(1).strip().upper()
    meeting_date_str = date_match.group(1).strip()

    try:
        import pandas as pd
        meeting_date_obj = pd.to_datetime(meeting_date_str).date()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format in XML: {meeting_date_str}")

    bm = db.query(BoardMeeting).filter(
        BoardMeeting.symbol == symbol,
        BoardMeeting.meeting_date == meeting_date_obj
    ).first()

    if not bm:
        raise HTTPException(status_code=404, detail=f"Board meeting not found in database for symbol {symbol} and date {meeting_date_obj}.")"""

    content = content.replace(old_body_start, new_body_start)

    with open('backend/web/api/data/board_meeting_routes.py', 'w') as f:
        f.write(content)

update_route()
