from fastapi import APIRouter, Response, Depends
from web.auth.routes import get_current_user
from domain.common.user import User

router = APIRouter(prefix="/api/export", tags=["Export"])

from fastapi.templating import Jinja2Templates
from fastapi import Request

templates = Jinja2Templates(directory="web/ui/templates")

@router.get("/pdf/{idea_id}")
async def export_pdf(request: Request, idea_id: str, current_user: User = Depends(get_current_user)):
    """
    Exports the Trade Idea as a rich HTML report (simulating PDF generation).
    In a real app, this HTML would be converted to PDF using WeasyPrint or wkhtmltopdf.
    """
    # Mock Data Aggregation (Simulating the SQL Join)
    # In prod: fetch from DB using idea_id

    context = {
        "request": request,
        "trade_id": idea_id,
        "timestamp": "2023-10-05 14:30:00",
        "user_name": current_user.full_name,
        "strategy": "Bull Call Spread",
        "instrument": "NIFTY 19500 CE / 19700 CE",
        "direction": "LONG",
        "rationale_text": "High conviction breakout supported by FII Long Buildup. Volatility is relatively low, making debit spreads attractive.",
        "evidence_items": ["Price crossing 20DMA", "FII Net Longs +15k contracts", "PCR > 1.2"],
        "market_state": "Institutional Accumulation",
        "flow_state": "Long Buildup",
        "worst_case_scenario": "Gap Down 5% (PnL: -25,000)",
        "scenario_results": [
            {"name": "Gap Down 5%", "pnl": -25000, "description": "Overnight crash"},
            {"name": "Vol Spike +10%", "pnl": 5000, "description": "Fear index rise"}
        ],
        "greeks": {"delta": 0.45, "gamma": 0.0012, "vega": 8.5},
        "snapshot_id": "SNAP-999",
        "logic_version": "v1.2.0",
        "license_client": "Acme Hedge Fund"
    }

    # Return HTML for verification (Browsers can "Print to PDF")
    return templates.TemplateResponse("report_template.html", context)

@router.get("/csv/{idea_id}")
async def export_csv(idea_id: str, current_user: User = Depends(get_current_user)):
    """
    Exports the raw data for the Trade Idea as CSV.
    """
    csv_content = "Indicator,Value,Timestamp\nRSI,70,2023-10-01\nOI_Change,5%,2023-10-01"
    return Response(content=csv_content, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=data_{idea_id}.csv"})
