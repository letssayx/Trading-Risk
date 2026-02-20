from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query, Form
# ... imports ...
from datetime import datetime, date
# ... rest of imports ...

def parse_udiff_date(date_str) -> Optional[date]:
    """Parse UDIFF date format (DD-MMM-YYYY)"""
    if pd.isna(date_str) or str(date_str).lower() == 'null' or str(date_str).strip() == '':
        return None
    if isinstance(date_str, datetime):
        return date_str.date()
    if isinstance(date_str, date):
        return date_str
    try:
        return datetime.strptime(str(date_str).strip(), "%d-%b-%Y").date()
    except:
        return None
# ... rest of file (import_bhavcopy logic etc) ...
