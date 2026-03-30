from fastapi import APIRouter
from backend.web.api.data.volatility_routes import router as volatility_router

router = APIRouter()
router.include_router(volatility_router)
