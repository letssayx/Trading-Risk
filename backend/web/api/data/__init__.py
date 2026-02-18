from fastapi import APIRouter
from backend.web.api.data import view_routes

router = APIRouter()
router.include_router(view_routes.router)
