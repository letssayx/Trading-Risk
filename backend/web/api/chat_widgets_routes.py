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
                # To perfectly match the main app, if it's awaited or not yet declared, use the original expected_date text (which includes 'Forecasted:') if available, else 'Record date not yet declared'
                final_date_str = expected_date if expected_date and expected_date != "-" else (d_str if d_str != "-" else "Record date not yet declared")

                # Check history to see if this exact pending amount already exists there as "Record date not yet declared"
                is_duplicate_of_history = False
                for h in history:
                    if h.get("ex_date") == "Record date not yet declared" and str(h.get("amount", "")) == str(expected_amount):
                        is_duplicate_of_history = True
                        break

                if not is_duplicate_of_history:
                    events.append({
                        "Symbol": sym,
                        "Event Type": "Upcoming/Expected",
                        "Date / Ex-Date": final_date_str,
                        "Amount": expected_amount if expected_amount is not None else "Pending",
                        "Type": item.get("expected_type", "-"),
                        "Status": "Awaited" if is_awaited else ("Board Meeting" if board_meeting_date and board_meeting_date != "-" else "Forecast/Announced"),
                        "Details": item.get("expected_less_likely", "-")
                    })

        # Add Historical data
        # Track added historical combos to prevent duplication (like Bharti Airtel showing up multiple times)
        seen_hist = set()
        for h in history:
            ex_date_str = h.get("ex_date")
            amt = h.get("amount", "N/A")
            div_type = h.get("dividend_type", "-")

            # De-duplication key
            hist_key = f"{ex_date_str}_{amt}_{div_type}"
            if hist_key in seen_hist:
                continue
            seen_hist.add(hist_key)

            is_awaited_hist = False

            if ex_date_str == "Record date not yet declared":
                is_awaited_hist = True
                ex_date_str = "Record date not yet declared"

            # Removed strict filters on historical events. Historical events should always be fully included
            # for any queried symbol to match the main app UI.

            events.append({
                "Symbol": sym,
                "Event Type": "Historical Dividend",
                "Date / Ex-Date": ex_date_str,
                "Amount": amt,
                "Type": div_type,
                "Status": "Confirmed",
                "Details": h.get("purpose", "")
            })

    # De-duplicate the entire events list based on Symbol, Date, Amount to catch any cross-over between Upcoming and Historical
    final_events = []
    # Key strategy: group by Amount and Symbol to find duplicates between Upcoming and Historical if one is "Record date not yet declared" and the other is a forecast.
    # Actually, let's keep it simple: if two rows have the same Amount, and one is 'Record date not yet declared' and the other is 'Forecasted...', keep the 'Forecasted...' one.

    amount_map = {}
    for e in events:
        sym_amt_key = f"{e['Symbol']}_{e['Amount']}"
        if sym_amt_key not in amount_map:
            amount_map[sym_amt_key] = []
        amount_map[sym_amt_key].append(e)

    for key, evs in amount_map.items():
        if len(evs) > 1:
            # Check if we have a "Record date not yet declared" and a "Forecasted:"
            has_forecast = any("Forecasted:" in e['Date / Ex-Date'] for e in evs)
            has_not_declared = any("Record date not yet declared" in e['Date / Ex-Date'] for e in evs)

            if has_forecast and has_not_declared:
                # Filter out the 'Record date not yet declared' one
                evs = [e for e in evs if "Record date not yet declared" not in e['Date / Ex-Date']]

            # Generic deduplication if they are exactly the same
            unique_evs = []
            seen = set()
            for e in evs:
                k = f"{e['Date / Ex-Date']}_{e['Type']}"
                if k not in seen:
                    unique_evs.append(e)
                    seen.add(k)
            final_events.extend(unique_evs)
        else:
            final_events.extend(evs)

    events = final_events

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
