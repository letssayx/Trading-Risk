from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from web.auth.routes import get_current_user
from domain.common.user import User

router = APIRouter(prefix="", tags=["UI"])
templates = Jinja2Templates(directory="web/ui/templates")

@router.get("/dashboard")
async def dashboard_ui(request: Request):
    """
    Serves the main Analysis Workbench UI.
    Authentication check mocked or handled by middleware/frontend token logic.
    """
    return templates.TemplateResponse("dashboard.html", {"request": request})

@router.get("/ingest")
async def ingest_ui(request: Request):
    """
    Serves the Data Ingestion Hub UI.
    """
    return templates.TemplateResponse("ingest_hub.html", {"request": request})
