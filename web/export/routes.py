from fastapi import APIRouter, Response, Depends
from web.auth.routes import get_current_user
from domain.common.user import User

router = APIRouter(prefix="/api/export", tags=["Export"])

@router.get("/pdf/{idea_id}")
async def export_pdf(idea_id: str, current_user: User = Depends(get_current_user)):
    """
    Exports the Trade Idea as a PDF report (Mock).
    """
    # Mock PDF generation
    report_content = f"Trade Report for {idea_id}\nUser: {current_user.username}\nRisk: HIGH"
    return Response(content=report_content, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=report_{idea_id}.pdf"})

@router.get("/csv/{idea_id}")
async def export_csv(idea_id: str, current_user: User = Depends(get_current_user)):
    """
    Exports the raw data for the Trade Idea as CSV.
    """
    csv_content = "Indicator,Value,Timestamp\nRSI,70,2023-10-01\nOI_Change,5%,2023-10-01"
    return Response(content=csv_content, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=data_{idea_id}.csv"})
