from fastapi import APIRouter
from backend.api.schemas import WidgetRequest
from backend.domain.workbench.service import WidgetService

router = APIRouter(prefix="/api/widgets", tags=["Widgets"])

@router.post("/data")
def get_widget_data(req: WidgetRequest):
    """
    Returns data formatted for the widget type (Chart, Metrics, Table).
    Delegates to WidgetService.
    """
    return WidgetService.get_widget_data(req.tool_name, req.params or {})
