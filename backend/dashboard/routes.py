from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from backend.auth.routes import get_current_user
from backend.domain.common.user import User

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

# Mock Template Store
DASHBOARD_TEMPLATES = []

class DashboardTemplate(BaseModel):
    name: str
    config: Dict[str, Any]
    is_favorite: bool = False

class DashboardTemplateResponse(DashboardTemplate):
    template_id: int

@router.get("/templates", response_model=List[DashboardTemplateResponse])
async def get_templates(current_user: User = Depends(get_current_user)):
    """
    Retrieves all dashboard templates for the user.
    """
    # Filter by user in real DB
    return DASHBOARD_TEMPLATES

@router.post("/templates", response_model=DashboardTemplateResponse)
async def create_template(template: DashboardTemplate, current_user: User = Depends(get_current_user)):
    """
    Saves a new dashboard configuration.
    """
    new_id = len(DASHBOARD_TEMPLATES) + 1
    new_template = {
        "template_id": new_id,
        "name": template.name,
        "config": template.config,
        "is_favorite": template.is_favorite,
        "user_id": current_user.id
    }
    DASHBOARD_TEMPLATES.append(new_template)
    return new_template
