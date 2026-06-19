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

        ca_list = item.get("corporate_actions", [])
        bm_list = item.get("board_meetings", [])

        if not ca_list and not bm_list and not item.get("historical_avg_yield"):
            continue

        for ca in ca_list:
            ex_date_str = ca.get("ex_date")
            is_awaited = ca.get("is_awaited", False)

            if upcoming and not is_awaited:
                if ex_date_str and ex_date_str != "-":
                    try:
                        ex_d = datetime.datetime.strptime(ex_date_str, "%Y-%m-%d").date()
                        if ex_d < datetime.date.today():
                            continue
                    except:
                        pass

            if month and ex_date_str and ex_date_str != "-":
                try:
                    ex_d = datetime.datetime.strptime(ex_date_str, "%Y-%m-%d").date()
                    m_name = ex_d.strftime("%B").lower()
                    if not any(m.lower() == m_name for m in month):
                        continue
                except:
                    pass

            events.append({
                "Symbol": sym,
                "Event Type": "Declared Dividend",
                "Date / Ex-Date": "Awaited" if is_awaited else ex_date_str,
                "Amount": ca.get("amount", "N/A"),
                "Yield": f"{ca.get('yield', 0)}%" if ca.get('yield') else "-",
                "Status": "Awaited" if is_awaited else "Confirmed",
                "Details": ca.get("purpose", "")
            })

        for bm in bm_list:
            meeting_date_str = bm.get("meeting_date")
            if upcoming:
                if meeting_date_str and meeting_date_str != "-":
                    try:
                        m_d = datetime.datetime.strptime(meeting_date_str, "%Y-%m-%d").date()
                        if m_d < datetime.date.today():
                            continue
                    except:
                        pass

            if month and meeting_date_str and meeting_date_str != "-":
                try:
                    m_d = datetime.datetime.strptime(meeting_date_str, "%Y-%m-%d").date()
                    m_name = m_d.strftime("%B").lower()
                    if not any(m.lower() == m_name for m in month):
                        continue
                except:
                    pass

            events.append({
                "Symbol": sym,
                "Event Type": "Board Meeting",
                "Date / Ex-Date": meeting_date_str,
                "Amount": bm.get("expected_dividend", "Pending"),
                "Yield": "-",
                "Status": "Pending",
                "Details": bm.get("purpose", "")
            })

        if not upcoming and month and not ca_list and not bm_list:
            hist_months = item.get("historical_months", [])
            for hist_m in hist_months:
                if any(m.lower() == hist_m.lower() for m in month):
                    events.append({
                        "Symbol": sym,
                        "Event Type": "Historical Pattern",
                        "Date / Ex-Date": f"Usually {hist_m}",
                        "Amount": f"Avg ~{item.get('historical_avg_amount', 'N/A')}",
                        "Yield": f"~{item.get('historical_avg_yield', 'N/A')}%",
                        "Status": "Pattern",
                        "Details": "Based on historical average"
                    })
                    break

    def get_sort_date(e):
        d_str = e.get("Date / Ex-Date", "")
        if d_str in ["Awaited", "-"] or "Usually" in d_str:
            return datetime.date(2099, 12, 31)
        try:
            return datetime.datetime.strptime(d_str, "%Y-%m-%d").date()
        except:
            return datetime.date(1900, 1, 1)

    events.sort(key=get_sort_date, reverse=True)
    return events
