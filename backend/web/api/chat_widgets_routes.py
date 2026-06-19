from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import datetime

from backend.infrastructure.db import get_db
from backend.ingest.nse_models import CorporateAction, BoardMeeting
from backend.web.api.data.special_sit_routes import get_special_sit_dividends

router = APIRouter()

@router.get("/api/chat-widgets/dividend")
def get_chat_widget_dividends(
    symbol: List[str] = Query(None),
    month: List[str] = Query(None),
    upcoming: bool = False,
    db: Session = Depends(get_db)
):
    all_data = get_special_sit_dividends(db)
    events = []

    # get_special_sit_dividends returns a dict with "eq_date" and "data" keys
    if isinstance(all_data, dict) and "data" in all_data:
        items = all_data["data"]
    else:
        items = all_data

    for item in items:
        if not isinstance(item, dict):
            continue

        sym = item.get("symbol", "").upper()
        if symbol and sym not in [s.upper() for s in symbol]:
            continue

        history = item.get("history", [])
        expected_amount = item.get("expected_amount")
        expected_date = item.get("expected_highly_likely")
        board_meeting_date = item.get("board_meeting_date")

        # Check if item matches any criteria to process
        has_data = len(history) > 0 or expected_amount is not None or expected_date not in ["-", None] or board_meeting_date not in ["-", None]
        if not has_data:
            continue

        # Add Expected/Upcoming data
        if expected_amount is not None or (expected_date and expected_date != "-") or (board_meeting_date and board_meeting_date != "-"):
            # If upcoming filter is on, this usually qualifies as upcoming (unless it's already announced and past, but we'll include it)
            # Find the date string
            d_str = "-"
            is_awaited = False

            if "Announced: " in str(expected_date):
                d_str = expected_date.replace("Announced: ", "").strip()
            elif "Forecasted: " in str(expected_date):
                d_str = expected_date.replace("Forecasted: ", "").strip()

            if "Amount declared, date not yet announced" in str(item.get("expected_less_likely", "")):
                is_awaited = True

            if board_meeting_date and board_meeting_date != "-":
                d_str = board_meeting_date # Might override if there's a bm

            include_upcoming = True

            if month and d_str and d_str != "-":
                try:
                    # expected date might be DD-MM-YYYY or YYYY-MM-DD
                    if len(d_str.split("-")[0]) == 4:
                        ex_d = datetime.datetime.strptime(d_str, "%Y-%m-%d").date()
                    else:
                        ex_d = datetime.datetime.strptime(d_str, "%d-%m-%Y").date()

                    m_name = ex_d.strftime("%B").lower()
                    if not any(m.lower() == m_name for m in month):
                        include_upcoming = False
                except:
                    pass

            if upcoming and d_str and d_str != "-":
                 try:
                    # expected date might be DD-MM-YYYY or YYYY-MM-DD
                    if len(d_str.split("-")[0]) == 4:
                        ex_d = datetime.datetime.strptime(d_str, "%Y-%m-%d").date()
                    else:
                        ex_d = datetime.datetime.strptime(d_str, "%d-%m-%Y").date()

                    # only if ex date is in the future
                    if ex_d < datetime.date.today():
                        include_upcoming = False
                 except:
                    pass

            if include_upcoming:
                events.append({
                    "Symbol": sym,
                    "Event Type": "Upcoming/Expected",
                    "Date / Ex-Date": "Record date not yet declared" if is_awaited else d_str,
                    "Amount": expected_amount if expected_amount is not None else "Pending",
                    "Type": item.get("expected_type", "-"),
                    "Status": "Awaited" if is_awaited else ("Board Meeting" if board_meeting_date and board_meeting_date != "-" else "Forecast/Announced"),
                    "Details": item.get("expected_less_likely", "-")
                })

        # Add Historical data
        for h in history:
            ex_date_str = h.get("ex_date")
            is_awaited_hist = False

            if ex_date_str == "Record date not yet declared":
                is_awaited_hist = True
                ex_date_str = "Record date not yet declared"

            if upcoming and not is_awaited_hist:
                if ex_date_str and ex_date_str not in ["-", "Awaited", "Record date not yet declared"]:
                    try:
                        ex_d = datetime.datetime.strptime(ex_date_str, "%Y-%m-%d").date()
                        if ex_d < datetime.date.today():
                            continue
                    except:
                        pass

            if month and ex_date_str and ex_date_str not in ["-", "Awaited", "Record date not yet declared"]:
                try:
                    ex_d = datetime.datetime.strptime(ex_date_str, "%Y-%m-%d").date()
                    m_name = ex_d.strftime("%B").lower()
                    if not any(m.lower() == m_name for m in month):
                        continue
                except:
                    pass

            events.append({
                "Symbol": sym,
                "Event Type": "Historical Dividend",
                "Date / Ex-Date": ex_date_str,
                "Amount": h.get("amount", "N/A"),
                "Type": h.get("dividend_type", "-"),
                "Status": "Confirmed",
                "Details": h.get("purpose", "")
            })

    def get_sort_date(e):
        d_str = e.get("Date / Ex-Date", "")
        if d_str in ["Awaited", "-", "Record date not yet declared"] or "Usually" in d_str or "Board Meeting" in str(e.get("Status", "")):
            return datetime.date(2099, 12, 31)
        try:
            if len(d_str.split("-")[0]) == 4:
                return datetime.datetime.strptime(d_str, "%Y-%m-%d").date()
            else:
                return datetime.datetime.strptime(d_str, "%d-%m-%Y").date()
        except:
            # For "Awaited", put them at the top
            if "Awaited" in str(e.get("Status", "")) or d_str in ["Awaited", "Record date not yet declared"]:
                return datetime.date(2099, 12, 31)
            else:
                return datetime.date(1900, 1, 1)

    events.sort(key=get_sort_date, reverse=True)
    return events
