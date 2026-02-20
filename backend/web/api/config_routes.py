from fastapi import APIRouter
from pydantic import BaseModel
import os

router = APIRouter()

class ConfigUpdate(BaseModel):
    google_api_key: str = None
    groq_api_key: str = None

@router.get("/api/config")
async def get_config():
    # Return masked keys or just status
    return {
        "google_configured": bool(os.getenv("GOOGLE_API_KEY")),
        "groq_configured": bool(os.getenv("GROQ_API_KEY"))
    }

@router.post("/api/config")
async def update_config(config: ConfigUpdate):
    # In a real app, we'd save this to .env or DB
    # For now, just set in current process (temporary)
    if config.google_api_key:
        os.environ["GOOGLE_API_KEY"] = config.google_api_key
    if config.groq_api_key:
        os.environ["GROQ_API_KEY"] = config.groq_api_key

    return {"status": "Config updated (Runtime only)"}
